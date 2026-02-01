import os
from typing import List, Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cloudscraper
from urllib.parse import urljoin
from sqlmodel import Session, select
from utils.scraper_utils import scrape_author, format_author_name
from utils.download_utils import download_book
from models import create_db_and_tables, engine, Link, QueueItem
from constants import QueueStatus

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
    book_url = body.get("bookUrl")
    book_title = body.get("bookTitle", "Unknown Book") 
    book_author = body.get("bookAuthor")
    
    if not book_url:
        raise HTTPException(status_code=400, detail="bookUrl is required")
    
    try:
        with Session(engine) as session:
            # Check if already in queue
            existing = session.exec(
                select(QueueItem).where(
                    QueueItem.book_url == book_url,
                    QueueItem.status.in_([QueueStatus.PENDING.value, QueueStatus.IN_PROGRESS.value])
                )
            ).first()
            
            if existing:
                return {
                    "success": True,
                    "queued": True,
                    "queue_id": existing.id,
                    "message": "Book already in queue"
                }
            
            queue_item = QueueItem(
                book_title=book_title,
                book_url=book_url,
                book_author=book_author,
                status=QueueStatus.PENDING.value
            )
            session.add(queue_item)
            session.commit()
            session.refresh(queue_item)
            
            return {
                "success": True,
                "queued": True,
                "queue_id": queue_item.id,
                "message": "Book added to download queue"
            }
        
    except Exception as e:
        print(f"Error adding to queue: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

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


@app.get("/queue")
async def get_queue(status: Optional[str] = Query(default=None)):
    """Get all queue items, optionally filtered by status"""
    with Session(engine) as session:
        statement = select(QueueItem)
        if status:
            statement = statement.where(QueueItem.status == status)
        statement = statement.order_by(QueueItem.created_at)
        items = session.exec(statement).all()
    
    return [
        {
            "id": item.id,
            "bookTitle": item.book_title,
            "bookUrl": item.book_url,
            "bookAuthor": item.book_author,
            "status": item.status,
            "retryCount": item.retry_count,
            "errorMessage": item.error_message,
            "createdAt": item.created_at,
            "startedAt": item.started_at,
            "completedAt": item.completed_at,
        }
        for item in items
    ]


@app.get("/queue/{queue_id}")
async def get_queue_item(queue_id: int):
    """Get a specific queue item by ID"""
    with Session(engine) as session:
        item = session.get(QueueItem, queue_id)
        if not item:
            raise HTTPException(status_code=404, detail="Queue item not found")
        
        return {
            "id": item.id,
            "bookTitle": item.book_title,
            "bookUrl": item.book_url,
            "bookAuthor": item.book_author,
            "status": item.status,
            "retryCount": item.retry_count,
            "errorMessage": item.error_message,
            "createdAt": item.created_at,
            "startedAt": item.started_at,
            "completedAt": item.completed_at,
        }


@app.delete("/queue/{queue_id}")
async def cancel_queue_item(queue_id: int):
    """Cancel a queued download (only if still pending)"""
    with Session(engine) as session:
        item = session.get(QueueItem, queue_id)
        if not item:
            raise HTTPException(status_code=404, detail="Queue item not found")
        
        if item.status != QueueStatus.PENDING.value:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel item with status: {item.status}"
            )
        
        session.delete(item)
        session.commit()
        
        return {"success": True, "message": "Queue item cancelled"}
    
