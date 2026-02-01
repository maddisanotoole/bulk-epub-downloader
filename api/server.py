import os
from typing import List, Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cloudscraper
from urllib.parse import urljoin
from sqlmodel import Session, select
from scraper_utils import scrape_author, format_author_name
from models import create_db_and_tables, engine, Link
from constants import QueueStatus, MAX_RETRY_COUNT

headers = {'Accept-Encoding': 'identity', 'User-Agent': 'Defined'}
scraper = cloudscraper.create_scraper()

# uvicorn server:app --host 0.0.0.0 --port 8000

FRONTEND_ORIGIN = "http://localhost:5173"

create_db_and_tables()


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
    with Session(engine) as session:
        statement = select(Link.author, Link.book_author).where(
            Link.author.is_not(None),
            Link.author != ''
        ).distinct().order_by(Link.book_author)
        results = session.exec(statement).all()
    return {row[0]: row[1] or row[0] for row in results}


@app.get("/links")
async def get_links(author: Optional[str] = Query(default=None)):
    with Session(engine) as session:
        statement = select(Link)
        if author:
            statement = statement.where(Link.author == author)
        links = session.exec(statement).all()
    
    return [
        {
            "url": link.url,
            "author": link.author,
            "article": link.article,
            "downloaded": bool(link.downloaded),
            "title": link.title or "",
            "bookAuthor": link.book_author or "",
            "date": link.date or "",
            "language": link.language or "",
            "genre": link.genre or "",
            "imageUrl": link.image_url or "",
            "bookUrl": link.book_url or "",
            "description": link.description or "",
            "hasEpub": bool(link.has_epub),
            "hasPdf": bool(link.has_pdf),
        }
        for link in links
    ]


@app.delete("/authors/cleanup")
async def cleanup_downloaded_authors():
    try:
        with Session(engine) as session:
            all_links = session.exec(select(Link)).all()
            
            from collections import defaultdict
            author_books = defaultdict(list)
            for link in all_links:
                if link.author:
                    author_books[link.author].append(link)
            
            deleted_authors = []
            total_books_deleted = 0
            
            for author_slug, books in author_books.items():
                if all(book.downloaded == 1 for book in books):
                    author_name = books[0].book_author or author_slug
                    for book in books:
                        session.delete(book)
                        total_books_deleted += 1
                    deleted_authors.append(author_name)
            
            session.commit()
        
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
        with Session(engine) as session:
            all_links = session.exec(select(Link)).all()
            author_count = len(set(link.author for link in all_links if link.author))
            book_count = len(all_links)
            
            for link in all_links:
                session.delete(link)
            session.commit()
        
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
        with Session(engine) as session:
            statement = select(Link).where(Link.author == author_slug)
            links_to_delete = session.exec(statement).all()
            deleted_count = len(links_to_delete)
            
            for link in links_to_delete:
                session.delete(link)
            session.commit()
        
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
        raise HTTPException(status_code=400, detail="author is required")
    
    author = format_author_name(author_input)
    
    try:
        with Session(engine) as session:
            result = scrape_author(author, session)
        
        if result['success']:
            return {
                "success": True,
                "books_added": result['books_added'],
                "author": result['author']
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error scraping author: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape-authors")
async def scrape_authors_endpoint(body: dict):
    authors_input = body.get("authors")
    if not authors_input:
        raise HTTPException(status_code=400, detail="authors is required")
    
    author_names = [name.strip() for name in authors_input.split(",") if name.strip()]
    
    if not author_names:
        raise HTTPException(status_code=400, detail="No valid author names provided")
    
    results = []
    total_books = 0
    errors = []
    
    try:
        with Session(engine) as session:
            for author_input in author_names:
                author = format_author_name(author_input)
                print(f"Scraping author: {author}")
                
                try:
                    result = scrape_author(author, session)
                    
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
    
