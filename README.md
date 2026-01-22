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

## Get Book links:

Book links are stored in a sqlite3 db file.

They can be added by author, via the 'Add Author' button.

OR in the terminal

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
select author, url from links;
```

# Notes

This is a WIP

Known issues / upcoming features:

- Allow user to pick between pdf & epub
- Better filtering
- Allow searching
