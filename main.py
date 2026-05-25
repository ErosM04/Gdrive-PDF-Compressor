import os
import io
from random import random
import time
import json
import subprocess
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Scopes required for downloading from Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_IDS_LOCATION = "folder_ids.json"


def read_folders_ids(location):
    """Reads a JSON file containg all the folder IDs"""
    if not os.path.exists(location) and os.path.getsize(location) > 0:
        print(f"File '{location}' not found or empty.")
        return
    
    data = None
    with open(location, "r") as file:
        try:
            data = json.load(file)

        except json.JSONDecodeError:
            print(f"The '{location}' file exists but does not contain a valid JSON.")
            return

    if not data or not data["ids"]:
        print(f"No folder IDs listed in '{location}'")
        return
    
    ids = []
    for id in data["ids"]:
        ids.append(id)
            
    return ids


def authenticate_gdrive():
    """Handles Google Drive OAuth2 authentication."""

    creds = None
    # token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no valid credentials, prompt the user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return creds


def compress_pdf_ghostscript(input_path, output_path):
    """Compresses a PDF file using Ghostscript."""
    # Note: If you are on Windows, change "gs" to "gswin64c"
    ghostscript_cmd = "gswin64c" 
    
    # Ghostscript PDFSETTINGS levels:
    # /screen   (lowest resolution, smallest size)
    # /ebook    (medium resolution)
    # /printer  (high resolution)
    # /prepress (highest resolution, preserves colors)
    
    command = [
        ghostscript_cmd,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dPDFSETTINGS=/ebook", 
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        input_path
    ]
    
    total_time = 0;
    try:
        start = time.time()
        subprocess.run(command, check=True) # Compress the PDF using the Ghostscript command
        duration = time.time() - start;
        total_time += duration;
        print(f"   │     ├─ Successfully compressed: {os.path.basename(output_path)}")
        print(f"   │     ├─ Original size: {os.path.getsize(input_path) / 1024:.2f} KB")
        print(f"   │     ├─ Compressed size: {os.path.getsize(output_path) / 1024:.2f} KB")
        print(f"   │     ├─ Compressed to {(100 * (os.path.getsize(output_path) / 1024)) / (os.path.getsize(input_path) / 1024):.2f}% of original size")
        print(f"   │     └─ Compression time: {format_duration(duration)}")
    except subprocess.CalledProcessError as e:
        print(f"   │     └─ Error compressing {input_path}: {e}")
    except FileNotFoundError:
        print(f"   │     └─ Error: Ghostscript ('{ghostscript_cmd}') not found. Please ensure it is installed and added to your PATH.")
    return total_time;


def format_duration(duration):
    "Formats a number into ``xxh xxm xxs``"
    duration = int(duration)
    if duration < 60:
        return f"{duration}s"
    elif duration < 3600:
        minutes = int(duration // 60)
        seconds = duration % 60
        return f"{minutes}m {seconds}s"
    else:
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = duration % 60
        return f"{hours}h {minutes}m {seconds}s"


def main(folder_ids_list, download_dir="downloads"):
    total_compressed_files = 0;
    total_time = 0;
    creds = authenticate_gdrive()
    service = build('drive', 'v3', credentials=creds)

    # Set up directories
    compressed_dir = os.path.join(download_dir, "compressed")
    os.makedirs(compressed_dir, exist_ok=True) # Also creates all intermediate directories

    for folder_id in folder_ids_list:
        print(f"\nProcessing folder: {folder_id}")

        # Query to list all files in the specific folder (excluding trashed files)
        query = f"'{folder_id}' in parents and trashed=false"
        
        print("└─ Fetching file list from Google Drive...")
        results = service.files().list(q=query, fields="nextPageToken, files(id, name, mimeType)").execute()
        items = results.get('files', [])

        if not items:
            print('  └─ No PDF files found in the specified folder.')
            if(random.randint(1, 100) == 1):
                print("     └─ No PDFiles, Jeffry is sad :(")
            return

        for item in items:
            file_id = item['id']
            file_name = item['name']
            mime_type = item['mimeType']
            
            # Skip native Google Docs/Sheets/Slides (they require exporting, not standard downloading)
            if "application/vnd.google-apps" in mime_type:
                print(f"   ├─ Skipping Google Workspace file: {file_name}")
                continue

            print(f"   │\n   ├─ Downloading: {file_name}")
            request = service.files().get_media(fileId=file_id)
            
            file_path = os.path.join(download_dir, file_name)
            
            # Download the file in chunks
            with io.FileIO(file_path, mode='wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    print(f"   │  ├─ Download {int(status.progress() * 100)}%.", end='\r', flush=True)
            print() # Clear line break after progress percentage
            
            # Check if the file is a PDF before passing it to Ghostscript
            if file_name.lower().endswith('.pdf') or mime_type == 'application/pdf':
                output_path = os.path.join(compressed_dir, file_name)
                print(f"   │  └─ Compressing: {file_name}")
                total_time += compress_pdf_ghostscript(file_path, output_path)
                total_compressed_files += 1;
            else:
                print(f"   │  └─ Skipped compression (not a PDF): {file_name}")
    
    if total_compressed_files > 0:
        print(f"\nProcessing complete.\nTotal files: {total_compressed_files}\nTotal compression time: {format_duration(total_time)}")
        print(f"Average compression time: {format_duration(total_time / total_compressed_files)}")
    else:
        print("No PDF files were compressed.")


if __name__ == '__main__': # Avoids to run the script when file is imported as module
    main(read_folders_ids(FOLDER_IDS_LOCATION))