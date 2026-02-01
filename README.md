# Bulk EPUB Downloader

Automation for downloading epubs.

## Setup:

```bash
npm i
```

## Start App:

Run backend and FE to see the list of available books. You can then multi-select and download.
It will prefer epubs, but will grab pdf if only that is available.

```bash
npm run dev
```

The app is made up of 3 components:

**FE**: React TS Frontend, for adding authors and selecting files to download.

**API server**: Python server, for scraping and communication with the FE. When a download is requested, it adds its to a DB queue.

**Worker**: Runs in the background, periodically checks the DB queue for uncompleted downloads and downloads them.

## Get Book links:

Book links are stored in a sqlite3 db file.

They can be added by author, via the 'Add Author' button.

OR in the terminal

```bash
npm run author
```

You will be prompted for an author name (e.g. "j k rowling")

Optional:
If you want to query db from terminal

```bash
sqlite3 database/links.db
// OR
npm run db

// THEN
select author, url from links;
```
