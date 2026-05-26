import argparse
import os
# from random import random
import sys
import json
from concurrent.futures import ThreadPoolExecutor
from googleapiclient.discovery import build

from auth import authenticate_gdrive
from downloader import process_folder
from compressor import compress_pdf_ghostscript
from utils import clean_directory

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


def main(folder_ids_list, clean: bool, recursive: bool, recursive_depth=sys.maxsize, download_dir="downloads", compressed_dir="compressed"):
    """Setup the Google Drive service and cycles all the given folders."""
    # Clean the directories if the -c flag is used
    if clean:
        clean_directory(download_dir)
        clean_directory(compressed_dir)

    # Setup Google Drive service
    service = build('drive', 'v3', credentials=authenticate_gdrive())
    
    # Set up the Thread Pool
    # max_workers=4 allows up to 4 PDFs to be compressed simultaneously.
    # You can increase this if you have a powerful CPU, but 4 is generally safe.
    with ThreadPoolExecutor(max_workers=4) as executor:
        for folder_id in folder_ids_list:
            try:
                folder_metadata = service.files().get(fileId=folder_id, fields="name").execute()
                root_folder_name = folder_metadata.get('name', 'Unknown Folder')
                print(f"\n📁 Target Google Drive Folder: {root_folder_name}")
            except Exception as e:
                print(f"\n⚠️ Could not fetch folder name (Check if the ID is correct). Error: {e}")

            process_folder(
                service=service, 
                executor=executor,
                compress_func=compress_pdf_ghostscript,
                folder_id=folder_id,
                current_download_dir=download_dir,
                current_compressed_dir=compressed_dir,
                recursive=recursive,
                recursive_depth=recursive_depth,
                )
        
        # Once all files are downloaded, the 'with' block will automatically freeze the main thread 
        # and wait until the remaining background workers finish their active compressions.
        print("\n⏳ All files downloaded! Waiting for background compressions to finish...")
    
    print("\nAll operations complete!")


def setup_flags(parser: argparse.ArgumentParser):
    """Setup all the flags for the script arguments. Can be listed with '--help'."""
    
    # -c / --clean flag
    parser.add_argument('-c', '--clean', 
                        action='store_true', # treats the argument as a boolean itself, or the command to run the script would be: "py .\main.py -r True" 
                        help="Delete the existing 'downloads' and 'compressed' folder before starting.")
    
    # -r / --recursive flag
    parser.add_argument('-r', '--recursive', 
                        action='store_true',
                        help="Recursively search and download files from all subfolders.")
   
    # --rd / --recursive-depth flag
    parser.add_argument("--rd", "--recursive-depth",
                        type=int,
                        help="Recursively search and download files from all subfolders with given depth.")


if __name__ == '__main__': # Avoids to run the script when file is imported as module
    # Set up the command line argument parser
    parser = argparse.ArgumentParser(description="Download and compress PDFs from a Google Drive folder.")
    
    setup_flags(parser)

    # Parse the arguments provided by the user
    args = parser.parse_args()

    if args.rd is None:
        main(read_folders_ids(FOLDER_IDS_LOCATION), clean=args.clean, recursive=args.recursive)
    else:
        main(read_folders_ids(FOLDER_IDS_LOCATION), clean=args.clean, recursive=args.recursive, recursive_depth=args.rd)


#     if total_compressed_files > 0:
#         print(f"\nProcessing complete.\nTotal files: {total_compressed_files}\nTotal compression time: {format_duration(total_time)}")
#         print(f"Average compression time: {format_duration(total_time / total_compressed_files)}")
#     else:
#         print("No PDF files were compressed.")