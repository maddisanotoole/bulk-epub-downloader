# Bulk EPUB Downloader

Automation for downloading epubs. 

## Setup:

```bash
npm i
```

## Step 1:
Book links are stored in a sqlite3 db file. Before running the app, we fetch links by author.

```bash
npm run author
```
You will be prompted for an author name (e.g. "j k rowling")


Optional: 
If you need to query db from terminal

```bash
sqlite3 database/links.db 
// OR
npm run db

// THEN
"select author, url from links"
```


## Step 2:
Run backend and FE to see the list of available books. You can then multi-select and download.
It will prefer epubs, but will grab pdf if only that is available. 

```bash
npm run api
npm run start
```


# Notes

This is a WIP

Known issues / upcoming features:
* Folder selection not working, leave as is to default to download folder
* Allow user to pick between pdf & epub
* Move link fetching from script to FE
* Better filtering
* Allow searching
* Allow clearing of downloaded/unwanted links
