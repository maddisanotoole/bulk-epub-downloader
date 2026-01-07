import path from "path";
import sqlite3 from "sqlite3";
import { Link } from "./types";

const defaultDbPath = path.join(process.cwd(), "database", "links.db");

export class DatabaseHelper {
  private db: sqlite3.Database;

  constructor(dbPath = defaultDbPath) {
    this.db = new sqlite3.Database(dbPath, sqlite3.OPEN_READONLY, (err) => {
      if (err) console.error(err.message);
    });
  }

  getAllLinks(): Promise<Link[]> {
    return new Promise((resolve, reject) => {
      this.db.all<Link>(
        "SELECT url, author, article, downloaded FROM links",
        (err, rows) => {
          if (err) return reject(err);
          resolve(
            rows.map((row) => ({ ...row, downloaded: !!row.downloaded }))
          );
        }
      );
    });
  }

  getLinksByAuthor(author: string): Promise<Link[]> {
    return new Promise((resolve, reject) => {
      this.db.all<Link>(
        "SELECT url, author, article, downloaded FROM links WHERE author = ?",
        [author],
        (err, rows) => {
          if (err) return reject(err);
          resolve(
            rows.map((row) => ({ ...row, downloaded: !!row.downloaded }))
          );
        }
      );
    });
  }

  getAllAuthors(): Promise<string[]> {
    return new Promise((resolve, reject) => {
      this.db.all<{ author: string }>(
        "SELECT DISTINCT author FROM links WHERE author IS NOT NULL AND author != ''",
        (err, rows) => {
          if (err) return reject(err);
          resolve(rows.map((row) => row.author));
        }
      );
    });
  }

  close(): void {
    this.db.close();
  }
}
