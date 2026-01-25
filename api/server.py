import os
import sqlite3
from typing import List, Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import cloudscraper
from urllib.parse import urljoin
from scraper_utils import scrape_author, format_author_name

headers = {'Accept-Encoding': 'identity', 'User-Agent': 'Defined'}
scraper = cloudscraper.create_scraper()

# uvicorn server:app --host 0.0.0.0 --port 8000


FRONTEND_ORIGIN = "http://localhost:5173"
DB_PATH =  "../database/links.db"

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS links (
            url TEXT UNIQUE,
            author TEXT,
            article TEXT,
            downloaded INTEGER,
            title TEXT,
            book_author TEXT,
            date TEXT,
            language TEXT,
            genre TEXT,
            image_url TEXT,
            book_url TEXT,
            description TEXT,
            has_epub INTEGER,
            has_pdf INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()


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

def get_filename(url):
    return url.split("/")[-1].split("?")[0]


@app.post("/download")
async def downloadFile(body: dict):
    from os.path import join, expanduser
    from os import makedirs
    from bs4 import BeautifulSoup

    book_url = body.get("bookUrl")
    book_title = body.get("bookTitle", "Unknown Book") 
    custom_destination = body.get("destination")
    
    if not book_url:
        return {"error": "bookUrl is required", "bookUrl": book_url, "bookTitle": book_title}, 400
    
    try:
        if custom_destination:
            destination = custom_destination
        else:
            destination = join(expanduser("~"), "Downloads")
        
        makedirs(destination, exist_ok=True)
        print(f"Fetching book page: {book_url}")
        
        max_retries = 3
        retry_delay = 2
        response = None
        
        for attempt in range(max_retries):
            try:
                response = scraper.get(book_url, headers=headers)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    print(f"Connection error fetching book page (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"Retrying in {wait_time} seconds...")
                    import time
                    time.sleep(wait_time)
                else:
                    print(f"Failed to fetch book page after {max_retries} attempts")
                    raise
        
        html = BeautifulSoup(response.text, "html.parser")
        
        forms = html.find_all('form', {'action': lambda x: x and 'Fetching_Resource.php' in x})
        
        if not forms:
            print("No download forms found")
            return {"error": "Could not find download form on page", "bookUrl": book_url, "bookTitle": book_title}, 404
        
        # Prefer epub over pdf
        selected_form = None
        for form in forms:
            filename_input = form.find('input', {'name': 'filename'})
            if filename_input:
                filename_value = filename_input.get('value', '')
                if filename_value.endswith('.epub'):
                    selected_form = form
                    print(f"Found EPUB form: {filename_value}")
                    break
        
        # If no epub, use pdf
        if not selected_form:
            for form in forms:
                filename_input = form.find('input', {'name': 'filename'})
                if filename_input:
                    filename_value = filename_input.get('value', '')
                    if filename_value.endswith('.pdf'):
                        selected_form = form
                        print(f"Found PDF form (no EPUB available): {filename_value}")
                        break
        
        if not selected_form:
            print("No valid download form found")
            return {"error": "Could not find epub or pdf download form", "bookUrl": book_url, "bookTitle": book_title}, 404
        
        form_action = selected_form.get('action')
        form_id = selected_form.find('input', {'name': 'id'})
        form_filename = selected_form.find('input', {'name': 'filename'})
        
        if not form_action or not form_id or not form_filename:
            print("Form missing required fields")
            return {"error": "Download form is incomplete", "bookUrl": book_url, "bookTitle": book_title}, 404
        
        server_id = form_id.get('value')
        filename = form_filename.get('value')
        
        print(f"Form action: {form_action}")
        print(f"Server ID: {server_id}")
        print(f"Filename: {filename}")
        
        form_data = {
            'id': server_id,
            'filename': filename
        }
        
        print(f"Submitting form to download file...")
        
        # Retry form submission
        download_response = None
        for attempt in range(max_retries):
            try:
                download_response = scraper.post(form_action, data=form_data, headers=headers, allow_redirects=True)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    print(f"Connection error submitting form (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"Retrying in {wait_time} seconds...")
                    import time
                    time.sleep(wait_time)
                else:
                    print(f"Failed to submit form after {max_retries} attempts")
                    raise
        
        redirect_html = BeautifulSoup(download_response.text, "html.parser")
        meta_refresh = redirect_html.find('meta', attrs={'http-equiv': 'Refresh'})
        
        if not meta_refresh:
            print("Could not find redirect URL")
            return {"error": "Could not find download redirect", "bookUrl": book_url, "bookTitle": book_title}, 404
        
        content_attr = meta_refresh.get('content', '')
        if 'url=' in content_attr:
            actual_download_url = content_attr.split('url=')[1]
            print(f"Found actual download URL: {actual_download_url}")
        else:
            print("Could not parse redirect URL")
            return {"error": "Could not parse download URL", "bookUrl": book_url, "bookTitle": book_title}, 404
        
        print(f"Downloading file from: {actual_download_url}")
        
        # Retry file download
        file_response = None
        for attempt in range(max_retries):
            try:
                file_response = scraper.get(actual_download_url, headers=headers, allow_redirects=True)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    print(f"Connection error downloading file (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"Retrying in {wait_time} seconds...")
                    import time
                    time.sleep(wait_time)
                else:
                    print(f"Failed to download file after {max_retries} attempts")
                    raise
        
        filepath = join(destination, filename)
        with open(filepath, 'wb') as file:
            file.write(file_response.content)
        
        print(f"Successfully downloaded to: {filepath}")
        
        with get_connection() as conn:
            conn.execute(
                "UPDATE links SET downloaded = 1 WHERE book_url = ?",
                (book_url,)
            )
            conn.commit()
        print(f"Marked {book_url} as downloaded in database")
        
        return {"success": True, "filename": filename, "destination": destination}
        
    except Exception as e:
        print(f"Error downloading: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "bookUrl": book_url, "bookTitle": book_title}, 500

@app.get("/authors")
async def get_all_authors():
    with get_connection() as conn:
        cur = conn.execute("""
            SELECT DISTINCT author, book_author 
            FROM links 
            WHERE author IS NOT NULL AND author != ''
            GROUP BY author
            ORDER BY book_author
        """)
        rows = cur.fetchall()
    return {row["author"]: row["book_author"] or row["author"] for row in rows}


@app.get("/links")
async def get_links(author: Optional[str] = Query(default=None)):
    sql = """SELECT url, author, article, downloaded, 
             title, book_author, date, language, genre, 
             image_url, book_url, description, has_epub, has_pdf 
             FROM links"""
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
            "title": row["title"] or "",
            "bookAuthor": row["book_author"] or "",
            "date": row["date"] or "",
            "language": row["language"] or "",
            "genre": row["genre"] or "",
            "imageUrl": row["image_url"] or "",
            "bookUrl": row["book_url"] or "",
            "description": row["description"] or "",
            "hasEpub": bool(row["has_epub"]),
            "hasPdf": bool(row["has_pdf"]),
        }
        for row in rows
    ]


@app.delete("/authors/cleanup")
async def cleanup_downloaded_authors():
    try:
        with get_connection() as conn:
            cur = conn.execute("""
                SELECT author, book_author, COUNT(*) as total_books, 
                       SUM(CASE WHEN downloaded = 1 THEN 1 ELSE 0 END) as downloaded_books
                FROM links
                WHERE author IS NOT NULL AND author != ''
                GROUP BY author
                HAVING total_books = downloaded_books
            """)
            authors_to_delete = cur.fetchall()
            
            deleted_authors = []
            total_books_deleted = 0
            
            for row in authors_to_delete:
                author_slug = row["author"]
                author_name = row["book_author"] or author_slug
                result = conn.execute(
                    "DELETE FROM links WHERE author = ?",
                    (author_slug,)
                )
                books_deleted = result.rowcount
                total_books_deleted += books_deleted
                deleted_authors.append(author_name)
            
            conn.commit()
        
        print(f"Cleanup: Deleted {len(deleted_authors)} author(s) with {total_books_deleted} book(s)")
        return {
            "success": True,
            "authors_deleted": len(deleted_authors),
            "books_deleted": total_books_deleted,
            "deleted_author_names": deleted_authors
        }
    except Exception as e:
        print(f"Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}, 500


@app.delete("/authors/all")
async def delete_all_authors():
    """Delete all authors and books from the database."""
    try:
        with get_connection() as conn:
            cur = conn.execute("""
                SELECT COUNT(DISTINCT author) as author_count, COUNT(*) as book_count
                FROM links
                WHERE author IS NOT NULL AND author != ''
            """)
            stats = cur.fetchone()
            author_count = stats["author_count"]
            book_count = stats["book_count"]
            
            # Delete all records
            conn.execute("DELETE FROM links")
            conn.commit()
        
        print(f"Deleted all {author_count} author(s) and {book_count} book(s)")
        return {
            "success": True,
            "authors_deleted": author_count,
            "books_deleted": book_count
        }
    except Exception as e:
        print(f"Error deleting all: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}, 500


@app.delete("/authors/{author_slug}")
async def delete_author(author_slug: str):
    try:
        with get_connection() as conn:
            result = conn.execute(
                "DELETE FROM links WHERE author = ?",
                (author_slug,)
            )
            deleted_count = result.rowcount
            conn.commit()
        
        print(f"Deleted author '{author_slug}' and {deleted_count} book(s)")
        return {"success": True, "deleted_count": deleted_count}
    except Exception as e:
        print(f"Error deleting author: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}, 500


@app.post("/scrape-author")
async def scrape_author_endpoint(body: dict):
    author_input = body.get("author")
    if not author_input:
        return {"error": "author is required"}, 400
    
    author = format_author_name(author_input)
    
    try:
        with get_connection() as conn:
            result = scrape_author(author, conn)
        
        if result['success']:
            return {
                "success": True,
                "books_added": result['books_added'],
                "author": result['author']
            }
        else:
            return {"error": result.get('error', 'Unknown error')}, 500
            
    except Exception as e:
        print(f"Error scraping author: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}, 500


@app.post("/scrape-authors")
async def scrape_authors_endpoint(body: dict):
    authors_input = body.get("authors")
    if not authors_input:
        return {"error": "authors is required"}, 400
    
    author_names = [name.strip() for name in authors_input.split(",") if name.strip()]
    
    if not author_names:
        return {"error": "No valid author names provided"}, 400
    
    results = []
    total_books = 0
    errors = []
    
    try:
        with get_connection() as conn:
            for author_input in author_names:
                author = format_author_name(author_input)
                print(f"Scraping author: {author}")
                
                try:
                    result = scrape_author(author, conn)
                    
                    if result['success']:
                        total_books += result['books_added']
                        results.append({
                            "author": result['author'],
                            "books_added": result['books_added'],
                            "success": True
                        })
                    else:
                        errors.append({
                            "author": author,
                            "error": result.get('error', 'Unknown error')
                        })
                        results.append({
                            "author": author,
                            "books_added": 0,
                            "success": False,
                            "error": result.get('error', 'Unknown error')
                        })
                except Exception as e:
                    error_msg = str(e)
                    print(f"Error scraping {author}: {error_msg}")
                    errors.append({"author": author, "error": error_msg})
                    results.append({
                        "author": author,
                        "books_added": 0,
                        "success": False,
                        "error": error_msg
                    })
        
        return {
            "success": True,
            "total_books_added": total_books,
            "authors_processed": len(author_names),
            "results": results,
            "errors": errors if errors else None
        }
            
    except Exception as e:
        print(f"Error scraping authors: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}, 500
    
