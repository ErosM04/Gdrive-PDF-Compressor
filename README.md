# Gdrive-PDF-Compressor
Python script to retrive PDF files from a Google Drive folder and then compress them with Ghostscript


## Steps
- Do ``python.exe -m pip install --upgrade pip`` then ``pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib``
- Install [GhostScript AGPL](https://ghostscript.com/releases/gsdnld.html)


## Important stuff
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

Add this:
``"Grab this from the URL of your Google Drive folder
Example: If URL is https://drive.google.com/drive/folders/1A2B3C4D5E6F, the ID is 1A2B3C4D5E6F"``