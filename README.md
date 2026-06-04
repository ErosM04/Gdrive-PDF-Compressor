# Gdrive-PDF-Compressor
Python script to retrive PDF files from Google Drive folders, compress them with Ghostscript and re-upload them back to Google Drive.

> [!NOTE]
This script and its guide were created and tested only on a Windows system, so they probably won't work on other systems. 


## Index
1. [Setup](#setup)
    - 1.1 [Download **GDrive-PDF-Compressor**](#download-gdrive-pdf-compressor)
    - 1.2 [Python](#python)
    - 1.3 [GhostScript](#ghostscript)
    - 1.4 [Google Cloud project](#google-cloud-project)
2. [How To Use](#how-to-use)
    - 2.1 [Provide the folder IDs](#provide-the-folder-ids)
    - 2.2 [Run the script](#run-the-script)
    - 2.3 [Examples](#examples)
3. [Common Errors](#common-errors)


## Setup


### Download GDrive-PDF-Compressor
Download this Python project either by clicking on ``Code > Download ZIP`` (then extract the content) or if you have **Git** installed on your terminal run:
```shell
git clone https://github.com/ErosM04/Gdrive-PDF-Compressor.git
```
You can move the **GDrive-PDF-Compressor** folder wherever you want.


### Python
Then installing Python from the [website](https://www.python.org/downloads/):snake: or by using your local package manager.
Then open the terminal and run the following command:
```shell
python --version
```

If you get prompted with an error, instead of the version, go to ``Modify System Environment Variables > Environment Variables > PATH`` then, one by one, add the following lines:
```shell
C:\Users\{username}\AppData\Local\Programs\Python\Python{version}\Scripts\
C:\Users\{username}\AppData\Local\Programs\Python\Python{version}\
C:\Users\{username}\AppData\Local\Programs\Python\Launcher\
```
Then save and reopen the terminal to verify the command works.


### GhostScript
Install the compression tool [GhostScript AGPL](https://ghostscript.com/releases/gsdnld.html) and again go to ``Modify System Environment Variables > Environment Variables > PATH`` and add the following line:
```shell
C:\Program Files\gs\gs10.07.1\bin
```
Note that this path may vary if you changed it during the GhostScript installation.

Then close and reopen the terminal and run the following command:
```shell
gswin64c --version
```
If you get prompted with the Ghostcript version it is installed and properly working for our use case. Eventually you can try with ``gs --version``.


### Google Cloud project
Open the terminal and update pip (Python package manager) by running:
```shell
python.exe -m pip install --upgrade pip
```
Then install the Google OAuth libraries by running:
```shell
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

> [!WARNING]
You need have a 18+ Google Account to perform the following step.

Go to the [Google Cloud Console](https://console.cloud.google.com/) and login with the same Google account linked with the Google Drive files you want to compress.

Then:
1. Create a new project.
2. From the right panel go to ``APIs & Services > Library``, search for **"Google Drive API"**, select it and click **Enable**.
3. Go to ``APIs & Services > Credentials`` and create **OAuth client ID** credentials (choose **"Desktop app"**).
4. Download the JSON file, rename it to ``credentials.json`` and place it in the **GDrive-PDF-Compressor** folder.


## How To Use


### Provide the folder IDs
To use the script you first need to get the Google Drive folder ID. To get it just open your Google Drive folder on your browser and copy the number contained at the end of the URL.

Example: If URL is https://drive.google.com/drive/folders/1A2Bv3C4dz5E6F, the ID is **``1A2Bv3C4dz5E6F``**.

To provide the folder ID to the script you have 2 ways:
1. Passing it as a parameter when you run the script, e.g.:
    ```shell
    py .\main.py 1A2Bv3C4dz5E6F
    ```
    Note: This won't just provide the ID to the scipt, it will also run it.

2. Passing more than one ID by creating a file in the **GFrive-PDF-Compressor** folder called ``folder_ids.json`` with the following structure:
    ```json
    {
        "ids": [
            "1A2Bv3C4dz5E6F",
            "1A5Pv6tDFqfSMP",
            "1A50XbuVv6tvwB"
        ]
    }
    ```
    Note: If you already specified the ID in the command, the IDs in the file won't be used.


### Run the script
To finally run the script open the terminal, move to the **GFrive-PDF-Compressor** folder and run (don't insert the ID if you want to use the ID file):
```shell
py .\main.py 1A2Bv3C4dz5E6F
```

You can also active various functions using the parameters. To list them just run:
```shell
py .\main.py --help
```

This are the parameters:
- ``-c``, ``--clean``: Delete the existing ``downloads`` and ``compressed`` folder before starting.
- ``-r``, ``--recursive``: Recursively search and download files from all subfolders.
- ``--rd``, ``--recursive-depth`` ``RD``: Recursively search and download files from all subfolders with given depth (``RD``).
- ``-u``, ``--upload``: Uploads the compressed file to its orginal position to Google Drive. The script overwrites the orginal file with its compressed version, thus preserving the orginal ID.
- ``--pf``, ``--pdfs-first``: Before diving into subfolders, process all the PDF files in the current folder.
- ``-n``, ``--number-of-files`` ``NUMBER_OF_FILES``: Set the amount of file that can be processed (``NUMBER_OF_FILES``) for each given folder ID. After the limit is reached the program stops processing the folder.
- ``-d``, ``--delete``: Deletes all downloaded and compressed files after successfully completing the upload. This will work only if the upload is enabled (with ``-u``). If any compression or upload fails no file will be eliminated.
- ``-dd``, ``--delete-downloads``: Deletes all downloaded files after successfully completing the compression or the upload. If any compression or upload fails no file will be eliminated.
- ``-dc``, ``--delete-compressed``: Deletes all compressed files after successfully completing the upload. This will work only if the upload is enabled (with ``-u``). If any compression or upload fails no file will be eliminated.
- ``-t``, ``--thread-count`` ``THREAD_COUNT``: Set the amount of cores (``THREAD_COUNT``) to use (each managing a different thread) for asynchronous compression and upload. The default value is 4 as it is safe for most CPUs (in order not to overload them).


### Examples
...


## Common Errors
- If you get prompted with **Request** problems just delete ``token.json``. This happens because the Google Cloud project has the OAuth consent screen set to **"Testing"** mode, meaning it automatically expires after 7 days. To fix this permanently go to the ``Google Cloud Console > Navigate to APIs & Services > OAuth consent`` screen and click ``Publish App`` under ``Publishing status`` to push it to production. (Since it's just a local desktop script, it won't actually be published to the public or require a Google review).
- If the scipt prompts an error while trying to fetch the files it's probably because you didn't enable the **Google Drive API** on your Google Cloud prject. Just click the link in the error and it will open a web page to enable the API, just click ``Enable``. Than (as the error says) wait a few minutes for the change to be propageted on all the Google's servers.
- In the ``compress_pdf_ghostscript`` the command ``gswin64c`` works on Windows, otherwise you may need to change the string to ``gs``.
- Clean ``downloads`` and ``compressed`` before running to avoid errors.
- If you use the recurse functionality don't avoid inserting in folder_ids a folder that is already a subfolder of another id you inserted.


## TODO
- [X] Clean download and compressed folders with ``-c``
- [X] Asynchronous download and compression
- [X] Recursive search: explore folders in current directory
    - [X] use ``-r`` to specify recurse until bottom of subfolders tree
    - [X] use ``--rd [n]`` where n is a prameter used to specify the max depth of the subfolders tree, e.g. n=3 opens up to 3 consecutive subfolders
- [X] Process files first, then folders with ``--pf``
- [X] Re-upload once the compression is completed with ``-u``
- [X] Delete downloaded and compressed files right after upload with ``-d``
    - [X] delete downloaded files right after compression with ``-dd``
    - [X] delete compressed files right after upload with ``-dc``
- [X] Set max amount of files, default is ♾️, otherwise ``-n [n]``
- [X] Option to read folder ID from terminal
- [X] Remove weighted avg compression time (pretty usless)
- [X] Change default core amount with ``-t``