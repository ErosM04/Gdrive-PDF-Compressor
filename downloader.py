import os
import io
import re
import sys

from googleapiclient.http import MediaIoBaseDownload
from compressor import print_lock
from utils import format_duration


def sanitize_name(name):
    r"""
    Replaces illegal Windows file/folder characters with an underscore.
    Illegal characters: < > : " / \ | ? *
    """ # r at the start to flag docstring as "raw string" to ignore backslash
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def process_folder(service, executor, compress_func, folder_id, current_download_dir, current_compressed_dir, recursive=False, recursive_depth=sys.maxsize):
    """Recursively processes folders to find and download PDF, then compress them with background threads."""
    # Ensure the local directories exist to mirror the Google Drive structure
    os.makedirs(current_download_dir, exist_ok=True)
    os.makedirs(current_compressed_dir, exist_ok=True)

    query = f"'{folder_id}' in parents and trashed=false"
    page_token = None

    # Cycles through the pages (Google sends batch of files in pages)
    while True:
        results = service.files().list(
            q=query, 
            spaces='drive',
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=page_token
        ).execute()
        
        items = results.get('files', [])

        for item in items:
            file_id = item['id']
            file_name = sanitize_name(item['name'])
            mime_type = item['mimeType']

            # Folder handling
            if mime_type == 'application/vnd.google-apps.folder':
                if recursive or (not recursive and recursive_depth > 0): # We can dive until bottom, or we still didn't reach the secified depth
                    print(f"\n📂 Opening Subfolder: {file_name}/")
                    new_download_dir = os.path.join(current_download_dir, file_name)
                    new_compressed_dir = os.path.join(current_compressed_dir, file_name)
                    process_folder(service=service, 
                                   executor=executor,
                                   compress_func=compress_func,
                                   folder_id=file_id, 
                                   current_download_dir=new_download_dir,
                                   current_compressed_dir=new_compressed_dir,
                                   recursive=recursive,
                                   recursive_depth=recursive_depth-1 # Decrease available 'dive'
                                   )
                elif (not recursive and recursive_depth == 0): # We reached the specified depth
                    print(f"   ➡️ Skipped Subfolder (run with higher --rd to include): {file_name}/")
                else: # We can't dive at all
                    print(f"   ➡️ Skipped Subfolder (run with -r to include): {file_name}/")
                continue
                
            # Skip native Google Workspace files (Docs/Sheets/Slides)
            elif "application/vnd.google-apps" in mime_type:
                continue

            # PDF files handling
            if file_name.lower().endswith('.pdf') or mime_type == 'application/pdf':
                print(f"\n⬇️ Downloading: {file_name}")
                request = service.files().get_media(fileId=file_id)
                file_path = os.path.join(current_download_dir, file_name)
                
                with io.FileIO(file_path, mode='wb') as fh:
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                        print(f"   ➡️ Download {int(status.progress() * 100)}%.", end='\r', flush=True) # Gradually updates only for >100MB files
                print()
                
                output_path = os.path.join(current_compressed_dir, file_name)
                print(f"   ➡️ 🔄 Pushing '{file_name}' to background compression queue...")

                # Submits the function and arguments to the background thread pool
                future = executor.submit(compress_func, file_path, output_path)
                future.add_done_callback(print_compression_result)
            else:
                print(f"Skipped compression (not a PDF): {file_name}")
                pass

        # Handles pagination if the folder has a massive amount of files (Google sends batch of files in pages)
        page_token = results.get('nextPageToken', None)
        if page_token is None:
            break


def print_compression_result(future):
    try:
        result_data = future.result()
        
        with print_lock:
            if result_data.success:
                print(f"\n   ✅ '{result_data.file_name}' took {format_duration(result_data.compression_duration)} to compress from {result_data.original_size}KB to {result_data.compressed_size}KB ({result_data.get_compression_percentage()}%)")
            else:
                print(f"\n   ⚠️ Background task failed for {result_data.file_name}: {result_data.error_message}")
            
    except Exception as e:
        with print_lock:
            print(f"\n   🔴 Background thread crashed: {e}")