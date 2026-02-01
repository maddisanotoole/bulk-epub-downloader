import time
import random
from sqlalchemy.exc import IntegrityError
import cloudscraper
from bs4 import BeautifulSoup
from models import Link

from constants import QueueStatus, MAX_RETRY_COUNT
headers = {'Accept-Encoding': 'identity', 'User-Agent': 'Defined'}
scraper = cloudscraper.create_scraper()


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


def format_author_name(author_input):
    return author_input.strip().lower().replace(' ', '-').replace('.','').replace(',','')


def scrape_author(author, session):
    books_added = 0
    page = 1
    
    try:
        while True:
            if page == 1:
                url = f"https://oceanofpdf.com/category/authors/{author}/"
            else:
                url = f"https://oceanofpdf.com/category/authors/{author}/page/{page}"
            
            print(f"Scraping {url}")
            
            retry_delay = 2
            response = None
            
            for attempt in range(MAX_RETRY_COUNT):
                try:
                    response = scraper.get(url, headers=headers)
                    break 
                except Exception as e:
                    if attempt < MAX_RETRY_COUNT - 1:
                        wait_time = retry_delay * (attempt + 1)
                        print(f"Connection error (attempt {attempt + 1}/{MAX_RETRY_COUNT}): {e}")
                        print(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        print(f"Failed after {MAX_RETRY_COUNT} attempts: {e}")
                        raise
            
            try:
                html = BeautifulSoup(response.text, "html.parser")
                
                articles = html.find_all("article")
                if not articles:
                    print("No more articles found.")
                    break
                
                for article in articles:
                    href = article.find("a")['href']
                    article_html = str(article)
                    
                    if author not in href:
                        print(f"Author not in href, stopping: {href}")
                        return {
                            'success': True,
                            'books_added': books_added,
                            'author': author
                        }
                    
                    try:
                        parsed = parse_article_html(article_html)
                        print(f"Found link: {href}")
                        print(parsed)
                        print('\n')
                        
                        link = Link(
                            url=href,
                            author=author,
                            article=article_html,
                            downloaded=0,
                            title=parsed['title'],
                            book_author=parsed['book_author'],
                            date=parsed['date'],
                            language=parsed['language'],
                            genre=parsed['genre'],
                            image_url=parsed['image_url'],
                            book_url=parsed['book_url'],
                            description=parsed['description'],
                            has_epub=1 if parsed['has_epub'] else 0,
                            has_pdf=1 if parsed['has_pdf'] else 0
                        )
                        session.add(link)
                        session.commit()
                        
                        books_added += 1
                        print(f"Added book: {parsed['title']}")
                        
                    except IntegrityError:
                        session.rollback()
                        print(f"Book already exists: {href}")
                        pass
                
            except Exception as e:
                print(f"Error on page {page}: {e}")
                break
            
            # Random delay to lower hit on site
            sleep_s = 0.8 + random.random() * 0.7  # ~0.8–1.5s
            time.sleep(sleep_s)
            
            page += 1
        
        print(f"Scraping complete. Added {books_added} books for author '{author}'")
        return {
            'success': True,
            'books_added': books_added,
            'author': author
        }
        
    except Exception as e:
        print(f"Error scraping author: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'books_added': books_added,
            'author': author
        }
