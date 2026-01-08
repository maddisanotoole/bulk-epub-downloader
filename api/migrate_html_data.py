import sqlite3
from bs4 import BeautifulSoup

DB_PATH = "../database/links.db"

def parse_article_html(html_string):
    soup = BeautifulSoup(html_string, 'html.parser')
    
    title_elem = soup.select_one('.entry-title a')
    title = title_elem.text.strip() if title_elem else ''
    book_url = title_elem['href'] if title_elem else ''
    date_elem = soup.select_one('.entry-time')
    date = date_elem.text.strip() if date_elem else ''
    
    postmeta = soup.select_one('.postmetainfo')
    author = ''
    language = ''
    genre = ''
    
    if postmeta:
        strong_tags = postmeta.find_all('strong')
        for strong in strong_tags:
            label = strong.text.strip().rstrip(':')
            next_sibling = strong.next_sibling
            value = ''
            while next_sibling and next_sibling.name != 'br' and next_sibling.name != 'strong':
                if isinstance(next_sibling, str):
                    value += next_sibling
                next_sibling = next_sibling.next_sibling if next_sibling else None
            
            value = value.strip()
            if label == 'Author':
                author = value
            elif label == 'Language':
                language = value
            elif label == 'Genre':
                genre = value
    
    img_elem = soup.select_one('.entry-image-link img')
    image_url = ''
    if img_elem:
        image_url = img_elem.get('data-src', img_elem.get('src', ''))
    desc_elem = soup.select_one('.entry-content p')
    description = desc_elem.text.strip() if desc_elem else ''
    has_epub = '[EPUB]' in description
    has_pdf = '[PDF]' in description
    
    return {
        'title': title,
        'book_author': author,
        'date': date,
        'language': language,
        'genre': genre,
        'image_url': image_url,
        'book_url': book_url,
        'description': description,
        'has_epub': has_epub,
        'has_pdf': has_pdf
    }


def migrate_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Adding new columns to the database...")
    columns_to_add = [
        ("title", "TEXT"),
        ("book_author", "TEXT"),
        ("date", "TEXT"),
        ("language", "TEXT"),
        ("genre", "TEXT"),
        ("image_url", "TEXT"),
        ("book_url", "TEXT"),
        ("description", "TEXT"),
        ("has_epub", "INTEGER"),
        ("has_pdf", "INTEGER"),
    ]
    
    for column_name, column_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE links ADD COLUMN {column_name} {column_type}")
            print(f"  Added column: {column_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"  Column {column_name} already exists, skipping...")
            else:
                raise
    
    conn.commit()
    
    print("\nFetching all records...")
    cursor.execute("SELECT rowid, article FROM links WHERE article IS NOT NULL AND article != ''")
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} records to process")
    
    success_count = 0
    error_count = 0
    
    for rowid, article_html in rows:
        try:
            parsed_data = parse_article_html(article_html)
            print(parsed_data)
            cursor.execute("""
                UPDATE links 
                SET title = ?,
                    book_author = ?,
                    date = ?,
                    language = ?,
                    genre = ?,
                    image_url = ?,
                    book_url = ?,
                    description = ?,
                    has_epub = ?,
                    has_pdf = ?
                WHERE rowid = ?
            """, (
                parsed_data['title'],
                parsed_data['book_author'],
                parsed_data['date'],
                parsed_data['language'],
                parsed_data['genre'],
                parsed_data['image_url'],
                parsed_data['book_url'],
                parsed_data['description'],
                1 if parsed_data['has_epub'] else 0,
                1 if parsed_data['has_pdf'] else 0,
                rowid
            ))
            
            success_count += 1
            if success_count % 10 == 0:
                print(f"  Processed {success_count}/{len(rows)} records...")
                conn.commit()
                
        except Exception as e:
            error_count += 1
            print(f"  Error processing rowid {rowid}: {e}")
    
    conn.commit()
    print(f"\nMigration complete!")
    print(f"  Successfully processed: {success_count}")
    print(f"  Errors: {error_count}")
    
    conn.close()


if __name__ == "__main__":
    migrate_database()
