import sqlite3
from scraper_utils import scrape_author, format_author_name

conn = sqlite3.connect("../database/links.db", check_same_thread = False)
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


if __name__ == "__main__":
    print ("Starting author scraper. Provide empty author name to exit")
    while True: 
        author = format_author_name(input("\nEnter author name (as in URL, e.g. 'j-k-rowling'): "))

        if author in ['exit', 'e', 'n', 'q', 'quit','' ]: 
            break
        print("Author: ", author)
        result = scrape_author(author, conn)
        if result['success']:
            print(f"Successfully added {result['books_added']} books!")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    conn.close()

