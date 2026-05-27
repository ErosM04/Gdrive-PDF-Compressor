import argparse
import os
# from random import random
import json
from concurrent.futures import ThreadPoolExecutor
from googleapiclient.discovery import build

from auth import authenticate_gdrive
from downloader import process_folder
from compressor import compress_pdf_ghostscript
from utils import clean_directory, format_duration

FOLDER_IDS_LOCATION = "folder_ids.json"


def read_folders_ids(location):
    """Reads a JSON file containg all the folder IDs"""
    if not os.path.exists(location) and os.path.getsize(location) > 0:
        print(f"Folder IDs file '{location}' not found or empty.")
        return
    
    data = None
    with open(location, "r") as file:
        try:
            data = json.load(file)

        except json.JSONDecodeError:
            print(f"The folder IDs file '{location}' exists but does not contain a valid JSON.")
            return

    if not data or not data["ids"]:
        print(f"No folder IDs listed in '{location}'")
        return
    
    ids = []
    for id in data["ids"]:
        ids.append(id)
            
    return ids


def main(folder_ids_list, args, download_dir="downloads", compressed_dir="compressed"):
    """Setup the Google Drive service and cycles all the given folders."""
    # Clean the directories if the -c flag is used
    if args.clean is not None and args.clean is True:
        clean_directory(download_dir)
        clean_directory(compressed_dir)

    # Setup Google Drive service
    service = build('drive', 'v3', credentials=authenticate_gdrive())

    future_list = []
    
    # Set up the Thread Pool
    # max_workers is the number of background threads, 4 is generally safe for most CPUs.
    with ThreadPoolExecutor(max_workers=4) as executor:
        params = { # Creates parameters for process_folder()
                        "service": service, 
                        "executor": executor,
                        "compress_func": compress_pdf_ghostscript,
                        "current_download_dir": download_dir,
                        "current_compressed_dir": compressed_dir,
                        "recursive": args.recursive,
                        "pdfs_first": args.pf,
                        "recursive_depth": args.rd,
                        "file_limit": args.number_of_files
                    }
        
        for folder_id in folder_ids_list:
            try:
                folder_metadata = service.files().get(fileId=folder_id, fields="name").execute()
                root_folder_name = folder_metadata.get('name', 'Unknown Folder')
                print(f"\n\n📁 Target Google Drive Folder: '{root_folder_name}'")
            except Exception as e:
                print(f"\n\n⚠️ Could not fetch folder name (check if the ID is correct). Error: {e}")
            
            params["folder_id"] = folder_id # Adds folder_id to parameters
            kwargs = {k: v for k, v in params.items() if v is not None} # Dictionary comprehension to remove None parameters

            future_list += process_folder(**kwargs)
        
        # Once all files are downloaded, the 'with' block will automatically freeze the main thread 
        # and wait until the remaining background workers finish their active compressions.
        print("\n\n⏳ All files downloaded. Waiting for background compressions to finish...")

    print("\n\n🎉 All operations complete!")

    total_time = 0
    w_total_time = 0
    successful_count = 0
    failed_count = 0
    total_compression = 0
    w_total_compression = 0
    weights_sum = 0

    # Loop through every CompressionData object and get the total infos
    for future in future_list:
        result_data = future.result()
        if result_data.success:
            successful_count += 1
            total_time += result_data.compression_duration
            w_total_time += result_data.compression_duration * result_data.compressed_size # value * weighted
            total_compression += result_data.get_compression_percentage()
            w_total_compression += result_data.get_compression_percentage() * result_data.compressed_size # value * weighted
            weights_sum += result_data.compressed_size
            
        else:
            failed_count += 1

    print("\n\n📊 --- COMPRESSION STATISTICS ---")
    print(f"Total PDFs processed: {len(future_list)}")
    print(f"✅ Successful: {successful_count}")
    print(f"❌ Failed: {failed_count}")

    if successful_count > 0:
        print(f"🕑 Total time compressing: {format_duration(total_time)}")
        print(f"⏱️ Average time per PDF: {format_duration(total_time / successful_count)}")
        print(f"📉 Average compressed size: {(total_compression / successful_count):.2f}%")
        print(f"⚖️⏱️ Normalized weighted average time per PDF: {format_duration(w_total_time / weights_sum)}")
        print(f"⚖️📉 Normalized weighted average compressed size: {(w_total_compression / weights_sum):.2f}%")
    else:
        print("😢 No files were successfully compressed.")


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
    
    # -n / --number-of-files flag
    parser.add_argument("-n", "--number-of-files",
                        type=int,
                        help="Set the amount of file that can be processed for each given folder ID. After the limit is reached the program stops processing the folder.")

    # --pf / --pdfs-first flag
    parser.add_argument('--pf', '--pdfs-first', 
                        action='store_true',
                        help="Before diving into subfolders, process all the PDF files in the current folder.")


if __name__ == '__main__': # Avoids to run the script when file is imported as module
    # Set up the command line argument parser
    parser = argparse.ArgumentParser(description="Download and compress PDFs from a Google Drive folder.")
    
    setup_flags(parser)

    main(read_folders_ids(FOLDER_IDS_LOCATION), args=parser.parse_args())