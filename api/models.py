from sqlmodel import SQLModel, Field, create_engine, Session
from datetime import datetime
from typing import Optional
from constants import QueueStatus
import os

class Link(SQLModel, table=True):
    __tablename__ = "links"
    
    url: str = Field(primary_key=True)
    author: Optional[str] = None
    article: Optional[str] = None
    downloaded: int = 0
    title: Optional[str] = None
    book_author: Optional[str] = None
    date: Optional[str] = None
    language: Optional[str] = None
    genre: Optional[str] = None
    image_url: Optional[str] = None
    book_url: Optional[str] = None
    description: Optional[str] = None
    has_epub: int = 0
    has_pdf: int = 0


class QueueItem(SQLModel, table=True):
    __tablename__ = "queue"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    book_title: str
    book_url: str
    book_author: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retry_count: int = 0
    status: str = Field(default=QueueStatus.PENDING.value)
    error_message: Optional[str] = None


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "database", "links.db")
DB_DIR = os.path.dirname(DB_PATH)

os.makedirs(DB_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables():
    """Initialize database and create all tables"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get a database session for queries"""
    with Session(engine) as session:
        yield session
