from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from compressor import print_lock

def replace_file_on_drive(creds, file_id, file_path, file_name, start_spacing):
    """Uploads the compressed file to Drive, overwriting the original file's content, thus preserving the orginal ID."""
    
    # Create a fresh, thread-safe connection to Google Drive for this specific upload
    service = build('drive', 'v3', credentials=creds)
    
    try:
        # with print_lock:
        #     print(f"\n{start_spacing}☁️ Starting upload for replacement: {file_name}...")
            
        # Prepare the file for upload
        media = MediaFileUpload(file_path, mimetype='application/pdf', resumable=True)
        
        # The update() method forces the new bytes into the existing File ID
        service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
        
        with print_lock:
            print(f"{start_spacing}⬆️ ✅ Successfully replaced on Drive: {file_name}")
        return True
        
    except Exception as e:
        with print_lock:
            print(f"{start_spacing}⬆️ ❌ Error uploading {file_name}: {e}")
        return False