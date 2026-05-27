import os
import io
import re

from googleapiclient.http import MediaIoBaseDownload
from compressor import print_lock
from utils import format_duration

BASE_SPACING = "   " # Space increase between subfolders's prints


def process_folder(service, # Google Drive service to retrive data
                   executor, # Multithread manager
                   compress_func, # Compression function
                   folder_id, # Google Drive ID of the folder to process
                   current_download_dir, # Current downloads folder path
                   current_compressed_dir, # Current compressed (files) folder path
                   recursive=False, # Use recursion until subfolder tree bottom
                   recursive_depth=0, # Limit to subfolder tree depth that can be reached
                   pdfs_first=False, # If True process all PDF files before diving into subfolders
                   file_limit=None, # Limit of file that can be processed, None is no limit
                   starting_spacing=BASE_SPACING # Amount of spacing to insert before a print
                   ):
    """Recursively processes folders to find and download PDF, then compresses them with background threads."""
    # Ensure the local directories exist to mirror the Google Drive structure
    os.makedirs(current_download_dir, exist_ok=True)
    os.makedirs(current_compressed_dir, exist_ok=True)

    query = f"'{folder_id}' in parents and trashed=false" # Google Drive query
    page_token = None # Pagination token

    futures = [] # Tracks all futures in this folder

    # Cycles through the pages (Google sends batch of files in pages)
    while True:
        results = service.files().list(
            q=query, 
            spaces='drive',
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=page_token
        ).execute()
        
        items = results.get('files', [])

        if pdfs_first:
            items = push_folders_to_tail(items)

        for item in items:
            file_id = item['id']
            file_name = sanitize_name(item['name'])
            mime_type = item['mimeType']

            # Check on file limit
            if file_limit is not None and file_limit <= 0:
                print(f"\n{starting_spacing}⚠️ Processable file limit reached")
                break

            # Folder handling
            if mime_type == 'application/vnd.google-apps.folder':
                if recursive or (not recursive and recursive_depth > 0): # We can dive until bottom, or we still didn't reach the secified depth
                    print(f"\n{starting_spacing}📂 Opening Subfolder: {file_name}/")
                    new_download_dir = os.path.join(current_download_dir, file_name)
                    new_compressed_dir = os.path.join(current_compressed_dir, file_name)
                    subfolder_futures = process_folder(service=service, 
                                   executor=executor,
                                   compress_func=compress_func,
                                   folder_id=file_id, 
                                   current_download_dir=new_download_dir,
                                   current_compressed_dir=new_compressed_dir,
                                   recursive=recursive,
                                   recursive_depth=recursive_depth-1, # Decrease available 'dive'
                                   pdfs_first=pdfs_first,
                                   file_limit=file_limit,
                                   starting_spacing=starting_spacing+BASE_SPACING
                                   )
                    futures.extend(subfolder_futures)
                elif (not recursive and recursive_depth == 0): # We reached the specified depth
                    print(f"\n{starting_spacing}▶️ Skipped Subfolder (run with higher --rd to include): {file_name}/")
                else: # We can't dive at all
                    print(f"\n{starting_spacing}▶️ Skipped Subfolder (run with -r to include): {file_name}/")
                continue
                
            # Skip native Google Workspace files (Docs/Sheets/Slides)
            elif "application/vnd.google-apps" in mime_type:
                continue

            # PDF files handling
            if (file_name.lower().endswith('.pdf') or mime_type == 'application/pdf'):              
                file_limit -= 1
                print(f"\n{starting_spacing}📄 Downloading: {file_name}")
                
                request = service.files().get_media(fileId=file_id)
                file_path = os.path.join(current_download_dir, file_name)
                
                with io.FileIO(file_path, mode='wb') as fh:
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                        print(f"{starting_spacing}  ▶️ Download {int(status.progress() * 100)}%.", end='\r', flush=True) # Gradually updates only for >100MB files
                print()
                
                output_path = os.path.join(current_compressed_dir, file_name)
                print(f"{starting_spacing}  ▶️ 🔄 Pushing '{file_name}' to background compression queue...")

                # Submits the function and arguments to the background thread pool, append a callback and adds the future to the list
                future = executor.submit(compress_func, file_path, output_path, starting_spacing)
                future.add_done_callback(print_compression_result)
                futures.append(future)
            else:
                print(f"{starting_spacing}  ▶️ Skipped compression (not a PDF): {file_name}")
                pass

        # Handles pagination if the folder has a massive amount of files (Google sends batch of files in pages)
        page_token = results.get('nextPageToken', None)
        if page_token is None:
            break
    return futures


def sanitize_name(name):
    r"""
    Replaces illegal Windows file/folder characters with an underscore.
    Illegal characters: < > : " / \ | ? *
    """ # r at the start to flag docstring as "raw string" to ignore backslash
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def push_folders_to_tail(list):
    """Takes a List and push to the tail all the Google Drive folder elements."""
    index = 0
    virtual_len = len(list)

    while index < virtual_len:
        if list[index]['mimeType'] == 'application/vnd.google-apps.folder':
            list.append(list[index])
            list.pop(index)
            index -= 1
            virtual_len -= 1
        index += 1
    
    return list


def print_compression_result(future):
    """Prints informations regarding the results of a file compression."""
    try:
        result_data = future.result()
        
        with print_lock:
            if result_data.success:
                print(f"\n{result_data.start_spacing}▶️ ✅ '{result_data.file_name}' took {format_duration(result_data.compression_duration)} to compress from {result_data.original_size}KB to {result_data.compressed_size}KB ({result_data.get_compression_percentage()}%)")
            else:
                print(f"\n{result_data.start_spacing}▶️ ⚠️ Background task failed for {result_data.file_name}: {result_data.error_message}")
            
    except Exception as e:
        with print_lock:
            print(f"\n{result_data.start_spacing}▶️ 🔴 Background thread crashed: {e}")