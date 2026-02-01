import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from models import Link, QueueItem


test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(name="session", autouse=True)
def session_fixture():
    """Create a test database session"""
    SQLModel.metadata.create_all(test_engine)
    
    with Session(test_engine) as session:
        yield session
        
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a test client with test database"""
    # Temporarily replace the engine
    import models
    original_engine = models.engine
    models.engine = test_engine
    
    from server import app
    
    client = TestClient(app)
    yield client
    
    # Restore original engine
    models.engine = original_engine


@pytest.fixture
def sample_link():
    """Create a sample link for testing"""
    return Link(
        url="https://example.com/book-1",
        author="test-author",
        title="Test Book",
        book_author="Test Author",
        book_url="https://example.com/download-1",
        downloaded=0,
        has_epub=1,
        has_pdf=0
    )


@pytest.fixture
def sample_queue_item():
    """Create a sample queue item for testing"""
    return QueueItem(
        book_title="Test Book",
        book_url="https://example.com/download-1",
        book_author="Test Author",
        status="pending"
    )
