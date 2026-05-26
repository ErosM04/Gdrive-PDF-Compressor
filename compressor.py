import os
import time
import subprocess
import threading

from compression_data import CompressionData


# A lock to prevent background threads from fucking up terminal text when printing
print_lock = threading.Lock()


def compress_pdf_ghostscript(input_path, output_path):
    """Compresses a PDF file using Ghostscript in a background thread.
    If the compression succeded returns the informations regarding the compression."""
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
    
    try:
        start = time.time()
        subprocess.run(command, check=True) # Compress the PDF using the Ghostscript command
        
        return CompressionData(file_name=os.path.basename(output_path),
                                   original_size= round((os.path.getsize(input_path) / 1024), 2),
                                   compressed_size=round((os.path.getsize(output_path) / 1024), 2),
                                   compression_duration= time.time() - start,
                                   success=True)
        
    except subprocess.CalledProcessError as e:
        return CompressionData(file_name=os.path.basename(output_path),
                                   original_size= round((os.path.getsize(input_path) / 1024), 2),
                                   compression_duration= time.time() - start,
                                   success=False,
                                   error_message=e)
    except FileNotFoundError:
        return CompressionData(file_name=os.path.basename(output_path),
                                   success=False,
                                   error_message=e)