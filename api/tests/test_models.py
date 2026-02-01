import pytest
from sqlmodel import Session, select
from datetime import datetime

from models import Link, QueueItem
from constants import QueueStatus


def test_create_link(session: Session):
    """Test creating a link"""
    link = Link(
        url="https://example.com/book",
        author="test-author",
        title="Test Book",
        book_url="https://example.com/download"
    )
    session.add(link)
    session.commit()
    
    statement = select(Link).where(Link.url == "https://example.com/book")
    result = session.exec(statement).first()
    
    assert result is not None
    assert result.title == "Test Book"
    assert result.author == "test-author"
    assert result.downloaded == 0  # Default value


def test_link_defaults(session: Session):
    """Test link default values"""
    link = Link(url="https://example.com/test", book_url="test")
    session.add(link)
    session.commit()
    
    assert link.downloaded == 0
    assert link.has_epub == 0
    assert link.has_pdf == 0


def test_create_queue_item(session: Session):
    """Test creating a queue item"""
    queue_item = QueueItem(
        book_title="Test Book",
        book_url="https://example.com/book"
    )
    session.add(queue_item)
    session.commit()
    
    statement = select(QueueItem).where(QueueItem.book_title == "Test Book")
    result = session.exec(statement).first()
    
    assert result is not None
    assert result.book_url == "https://example.com/book"
    assert result.status == QueueStatus.PENDING.value
    assert result.retry_count == 0


def test_queue_item_defaults(session: Session):
    """Test queue item default values"""
    queue_item = QueueItem(
        book_title="Test",
        book_url="https://test.com"
    )
    session.add(queue_item)
    session.commit()
    
    assert queue_item.status == QueueStatus.PENDING.value
    assert queue_item.retry_count == 0
    assert queue_item.created_at is not None
    assert queue_item.started_at is None
    assert queue_item.completed_at is None


def test_update_queue_status(session: Session):
    """Test updating queue item status"""
    queue_item = QueueItem(
        book_title="Test",
        book_url="https://test.com"
    )
    session.add(queue_item)
    session.commit()
    
    queue_item.status = QueueStatus.IN_PROGRESS.value
    queue_item.started_at = datetime.now().isoformat()
    session.commit()
    
    result = session.get(QueueItem, queue_item.id)
    assert result.status == QueueStatus.IN_PROGRESS.value
    assert result.started_at is not None


def test_query_by_status(session: Session):
    """Test querying queue items by status"""
    item1 = QueueItem(book_title="Book 1", book_url="url1", status=QueueStatus.PENDING.value)
    item2 = QueueItem(book_title="Book 2", book_url="url2", status=QueueStatus.IN_PROGRESS.value)
    item3 = QueueItem(book_title="Book 3", book_url="url3", status=QueueStatus.PENDING.value)
    
    session.add(item1)
    session.add(item2)
    session.add(item3)
    session.commit()
    
    statement = select(QueueItem).where(QueueItem.status == QueueStatus.PENDING.value)
    pending = session.exec(statement).all()
    
    assert len(pending) == 2
    assert all(item.status == QueueStatus.PENDING.value for item in pending)


def test_increment_retry_count(session: Session):
    """Test incrementing retry count"""
    queue_item = QueueItem(book_title="Test", book_url="url")
    session.add(queue_item)
    session.commit()
    
    original_count = queue_item.retry_count
    queue_item.retry_count += 1
    session.commit()
    
    result = session.get(QueueItem, queue_item.id)
    assert result.retry_count == original_count + 1


def test_link_unique_constraint(session: Session):
    """Test that duplicate URLs are not allowed"""
    from sqlalchemy.exc import IntegrityError
    
    link1 = Link(url="https://example.com/same", book_url="test")
    session.add(link1)
    session.commit()
    
    link2 = Link(url="https://example.com/same", book_url="test2")
    session.add(link2)
    
    with pytest.raises(IntegrityError):
        session.commit()
