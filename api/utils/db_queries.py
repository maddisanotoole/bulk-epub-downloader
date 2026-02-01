
INIT_LINKS_TABLE = """CREATE TABLE IF NOT EXISTS links (
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
    )"""

INIT_QUEUE_TABLE ="""
    CREATE TABLE IF NOT EXISTS queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_title TEXT
    book_url TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    started_at TEXT,
    completed_at TEXT,
    retry_count INTEGER DEFAULT -3,
    status INTEGER,
    error_message TEXT
)"""