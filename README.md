# Gdrive-PDF-Compressor
Python script to retrive PDF files from a Google Drive folder and then compress them with Ghostscript


## Important stuff
- If you get prompted with **Request** problems just delete ``token.json``. This happens because the Google Cloud project has the OAuth consent screen set to **"Testing"** mode, meaning it automatically expires after 7 days. To fix this permanently go to the ``Google Cloud Console > Navigate to APIs & Services > OAuth consent`` screen and click ``Publish App`` under ``Publishing status`` to push it to production. (Since it's just a local desktop script, it won't actually be published to the public or require a Google review).
- If the scipt prompts an error while trying to fetch the files it's probably because you didn't enable the **Google Drive API** on your Google Cloud prject. Just click the link in the error and it will open a web page to enable the API, just click ``Enable``. Than (as the error says) wait a few minutes for the change to be propageted on all the Google's servers.
- In the ``compress_pdf_ghostscript`` the command ``gswin64c`` works on Windows, otherwise you may need to change the string to ``gs``.
- Clean ``downloads`` and ``compressed`` before running to avoid errors


## TODO
- Print list of all files before download with ``-p``
    - Integrate behavior with ``-n [n]``
- Asyncronous download and compression
    - is default, or use ``-s`` for sync
- Recursive search: explore folders in current directory
    - use ``-r`` to specify recurse use, default is until bottom
    - use ``-r [n]`` where n is a prameter used to specify the max depth of the subfolders tree, e.g. n=3 opens up to 3 consecutive folders  
- Re-upload once the compression is completed
- Delete downloaded and compressed files right after upload with ``-d``
    - delete downloaded files right after compression with ``-dd``
    - delete compressed files right after upload with ``-dc``
- Set max amount of files, default is ♾️, otherwise ``-n [n]``

Add this:
``"Grab this from the URL of your Google Drive folder
Example: If URL is https://drive.google.com/drive/folders/1A2B3C4D5E6F, the ID is 1A2B3C4D5E6F"``