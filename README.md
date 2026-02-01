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

<p align="center">
<img width="808" height="397" alt="image" src="https://github.com/user-attachments/assets/8f1b6103-2a4e-46df-a0ae-da82a793de93" />
<img width="1278" height="635" alt="image" src="https://github.com/user-attachments/assets/22d49f72-fe26-4354-b825-da9d665e4634" />
<img width="1284" height="500" alt="image" src="https://github.com/user-attachments/assets/5561f207-5467-4106-a5c8-c25adf2f1bdd" />
</p>

**API server**: Python server, for scraping and communication with the FE. When a download is requested, it adds its to a DB queue.

**Worker**: Runs in the background, periodically checks the DB queue for uncompleted downloads and downloads them to your Downloads folder.

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

## Upcoming Features:
 * Download folder selection
 * Add Docker support for containerised deployment
 * Bulk import authors from CSV/text file
 * Include book description
 * Schedule downloads for specific times
 * Dark mode toggle
