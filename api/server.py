import os
import sqlite3
from typing import List, Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# uvicorn server:app --host 0.0.0.0 --port 8000


FRONTEND_ORIGIN = "http://localhost:5173"
DB_PATH =  "../database/links.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/authors", response_model=List[str])
async def get_all_authors():
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT DISTINCT author FROM links WHERE author IS NOT NULL AND author != ''"
        )
        rows = cur.fetchall()
    return [row["author"] for row in rows]


@app.get("/links")
async def get_links(author: Optional[str] = Query(default=None)):
    sql = "SELECT url, author, article, downloaded FROM links"
    params = []
    if author:
        sql += " WHERE author = ?"
        params.append(author)
    with get_connection() as conn:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
    return [
        {
            "url": row["url"],
            "author": row["author"],
            "article": row["article"],
            "downloaded": bool(row["downloaded"]),
        }
        for row in rows
    ]
    
