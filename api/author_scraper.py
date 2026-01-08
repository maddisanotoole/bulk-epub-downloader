import time
import cloudscraper
from bs4 import BeautifulSoup
import sqlite3
import random

headers = {'Accept-Encoding': 'identity', 'User-Agent': 'Defined'}
scraper = cloudscraper.create_scraper()
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
    
    combined_text = title + ' ' + description
    has_epub = '[EPUB]' in combined_text
    has_pdf = '[PDF]' in combined_text
    
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

def scrape_author(author):
    page = 1
    while True:
        if page == 1:
            url = f"https://oceanofpdf.com/category/authors/{author}/"
        else:
            url = f"https://oceanofpdf.com/category/authors/{author}/page/{page}"
        print(f"Scraping {url}")
        try:
            response = scraper.get(url, headers=headers)
            html = BeautifulSoup(response.text, "html.parser")
           
            articles = html.find_all("article")
            if not articles:
                print("No more articles found.")
                break
            for article in articles:
                href = article.find("a")['href']
                article_html = str(article)

                try:
                    if author not in href:
                        return
                    print(f"Found link: {href}")
                    
                    parsed = parse_article_html(article_html)
                    print(parsed)
                    print('\n')
                    cursor.execute("""
                        INSERT INTO links(
                            url, author, article, downloaded,
                            title, book_author, date, language, genre,
                            image_url, book_url, description,
                            has_epub, has_pdf
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, (
                        href, author, article_html, 0,
                        parsed['title'], parsed['book_author'], parsed['date'],
                        parsed['language'], parsed['genre'], parsed['image_url'],
                        parsed['book_url'], parsed['description'],
                        1 if parsed['has_epub'] else 0,
                        1 if parsed['has_pdf'] else 0
                    ))
                    conn.commit()
                except sqlite3.IntegrityError:
                    pass
        except Exception as e:
            print(e)
            break
        
        # delay 
        sleep_s = 0.8 + random.random() * 0.7  # ~0.8–1.5s
        time.sleep(sleep_s)
        
        page += 1

def format_name(author_input):
    return author_input.strip().lower().replace(' ', '-')


if __name__ == "__main__":
    print ("Starting author scraper. Provide empty author name to exit")
    while True: 
        author = format_name(input("\nEnter author name (as in URL, e.g. 'j-k-rowling'): "))

        if author in ['exit', 'e', 'n', 'q', 'quit','' ]: 
            break
        print("Author: ", author)
        scrape_author(author)
    conn.close()

