# mirror.py

This is a python script for mirroring a static website.

Currently, it could download all html documents and all the js, css, image files it needs.

## Requirements

Python3 is required. Use `pip install -r requirements.txt` to install packages it needs.

## Usage

```bash
python3 mirror.py <first_url> [root_directory]

first_url: often the root index of the site

root_directory: the root directory to save website files
```

It would firstly download the first_url. If the downloaded file is a html document, then all the links in it would be extracted and downloaded. Links of html document only get downloaded when they are in the same host and the same directory with the first_url, and same operations would be applied, which means the whole process is recursive. Links of js, css, images and fonts would be download directly. Downloaded files are stored as the following file structure.

```bash
site_downloaded/
├── css
├── font
├── html
├── img
└── js
```

