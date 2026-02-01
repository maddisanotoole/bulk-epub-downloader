from fastapi.testclient import TestClient
from sqlmodel import Session, select

from models import Link, QueueItem
from constants import QueueStatus


def test_get_authors_empty(client: TestClient):
    """Test getting authors when database is empty"""
    response = client.get("/authors")
    assert response.status_code == 200
    assert response.json() == {}


def test_get_authors_with_data(client: TestClient, session: Session, sample_link: Link):
    """Test getting authors with data"""
    session.add(sample_link)
    session.commit()
    
    response = client.get("/authors")
    assert response.status_code == 200
    data = response.json()
    assert "test-author" in data
    assert data["test-author"] == "Test Author"


def test_get_links_empty(client: TestClient):
    """Test getting links when database is empty"""
    response = client.get("/links")
    assert response.status_code == 200
    assert response.json() == []


def test_get_links_with_data(client: TestClient, session: Session, sample_link: Link):
    """Test getting links with data"""
    session.add(sample_link)
    session.commit()
    
    response = client.get("/links")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Book"
    assert data[0]["bookAuthor"] == "Test Author"
    assert data[0]["hasEpub"] is True
    assert data[0]["hasPdf"] is False


def test_get_links_filter_by_author(client: TestClient, session: Session):
    """Test filtering links by author"""
    link1 = Link(
        url="https://example.com/book-1",
        author="author-1",
        title="Book 1",
        book_author="Author One",
        book_url="https://example.com/download-1"
    )
    link2 = Link(
        url="https://example.com/book-2",
        author="author-2",
        title="Book 2",
        book_author="Author Two",
        book_url="https://example.com/download-2"
    )
    session.add(link1)
    session.add(link2)
    session.commit()
    
    response = client.get("/links?author=author-1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Book 1"


def test_delete_author(client: TestClient, session: Session, sample_link: Link):
    """Test deleting an author"""
    session.add(sample_link)
    session.commit()
    
    response = client.delete("/authors/test-author")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["deleted_count"] == 1
    
    links = session.exec(select(Link)).all()
    assert len(links) == 0


def test_delete_all_authors(client: TestClient, session: Session):
    """Test deleting all authors"""
    link1 = Link(url="https://example.com/1", author="author-1", book_url="url1")
    link2 = Link(url="https://example.com/2", author="author-2", book_url="url2")
    session.add(link1)
    session.add(link2)
    session.commit()
    
    response = client.delete("/authors/all")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["books_deleted"] == 2
    
    links = session.exec(select(Link)).all()
    assert len(links) == 0


def test_cleanup_downloaded_authors(client: TestClient, session: Session):
    """Test cleanup of fully downloaded authors"""
    # Author with all books downloaded
    link1 = Link(
        url="https://example.com/1",
        author="author-1",
        book_author="Author One",
        book_url="url1",
        downloaded=1
    )
    link2 = Link(
        url="https://example.com/2",
        author="author-1",
        book_author="Author One",
        book_url="url2",
        downloaded=1
    )
    # Author with some books not downloaded
    link3 = Link(
        url="https://example.com/3",
        author="author-2",
        book_author="Author Two",
        book_url="url3",
        downloaded=0
    )
    
    session.add(link1)
    session.add(link2)
    session.add(link3)
    session.commit()
    
    response = client.delete("/authors/cleanup")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["authors_deleted"] == 1
    assert data["books_deleted"] == 2
    
    # Verify only author-2 remains
    links = session.exec(select(Link)).all()
    assert len(links) == 1
    assert links[0].author == "author-2"


def test_scrape_author_missing_param(client: TestClient):
    """Test scraping author without required parameter"""
    response = client.post("/scrape-author", json={})
    assert response.status_code == 400


def test_scrape_authors_missing_param(client: TestClient):
    """Test scraping authors without required parameter"""
    response = client.post("/scrape-authors", json={})
    assert response.status_code == 400


def test_download_adds_to_queue(client: TestClient, session: Session, sample_link: Link):
    """Test that download endpoint adds books to queue"""
    session.add(sample_link)
    session.commit()
    
    response = client.post("/download", json={
        "bookUrl": sample_link.book_url,
        "bookTitle": sample_link.title,
        "bookAuthor": sample_link.book_author
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["queued"] is True
    assert "queue_id" in data
    
    # Verify queue item was created
    queue_items = session.exec(select(QueueItem)).all()
    assert len(queue_items) == 1
    assert queue_items[0].book_url == sample_link.book_url
    assert queue_items[0].status == QueueStatus.PENDING.value


def test_download_duplicate_in_queue(client: TestClient, session: Session, sample_queue_item: QueueItem):
    """Test that downloading same book twice doesn't create duplicate queue entries"""
    session.add(sample_queue_item)
    session.commit()
    
    response = client.post("/download", json={
        "bookUrl": sample_queue_item.book_url,
        "bookTitle": sample_queue_item.book_title,
        "bookAuthor": sample_queue_item.book_author
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["queued"] is True
    assert data["message"] == "Book already in queue"
    
    # Verify only one queue item exists
    queue_items = session.exec(select(QueueItem)).all()
    assert len(queue_items) == 1


def test_download_missing_book_url(client: TestClient):
    """Test download endpoint without bookUrl"""
    response = client.post("/download", json={
        "bookTitle": "Test Book"
    })
    assert response.status_code == 400


def test_get_queue_empty(client: TestClient):
    """Test getting queue when empty"""
    response = client.get("/queue")
    assert response.status_code == 200
    assert response.json() == []


def test_get_queue_with_items(client: TestClient, session: Session, sample_queue_item: QueueItem):
    """Test getting all queue items"""
    session.add(sample_queue_item)
    session.commit()
    
    response = client.get("/queue")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["bookTitle"] == "Test Book"
    assert data[0]["status"] == "pending"


def test_get_queue_filter_by_status(client: TestClient, session: Session):
    """Test filtering queue by status"""
    item1 = QueueItem(
        book_title="Book 1",
        book_url="url1",
        status=QueueStatus.PENDING.value
    )
    item2 = QueueItem(
        book_title="Book 2",
        book_url="url2",
        status=QueueStatus.COMPLETED.value
    )
    session.add(item1)
    session.add(item2)
    session.commit()
    
    response = client.get("/queue?status=pending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["bookTitle"] == "Book 1"


def test_get_queue_item(client: TestClient, session: Session, sample_queue_item: QueueItem):
    """Test getting a specific queue item"""
    session.add(sample_queue_item)
    session.commit()
    session.refresh(sample_queue_item)
    
    response = client.get(f"/queue/{sample_queue_item.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_queue_item.id
    assert data["bookTitle"] == "Test Book"
    assert data["status"] == "pending"


def test_get_queue_item_not_found(client: TestClient):
    """Test getting non-existent queue item"""
    response = client.get("/queue/999")
    assert response.status_code == 404


def test_cancel_queue_item(client: TestClient, session: Session, sample_queue_item: QueueItem):
    """Test cancelling a pending queue item"""
    session.add(sample_queue_item)
    session.commit()
    session.refresh(sample_queue_item)
    
    response = client.delete(f"/queue/{sample_queue_item.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Verify item was deleted
    queue_items = session.exec(select(QueueItem)).all()
    assert len(queue_items) == 0


def test_cancel_queue_item_not_found(client: TestClient):
    """Test cancelling non-existent queue item"""
    response = client.delete("/queue/999")
    assert response.status_code == 404


def test_cancel_in_progress_item(client: TestClient, session: Session):
    """Test that you cannot cancel an in-progress item"""
    item = QueueItem(
        book_title="Test Book",
        book_url="url1",
        status=QueueStatus.IN_PROGRESS.value
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    
    response = client.delete(f"/queue/{item.id}")
    assert response.status_code == 400
    assert "Cannot cancel" in response.json()["detail"]
