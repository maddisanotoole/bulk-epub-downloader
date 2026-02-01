from fastapi.testclient import TestClient
from sqlmodel import Session, select

from models import Link


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
    
    # Verify deletion
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
