import time
import cloudscraper
from bs4 import BeautifulSoup
import sqlite3
import random
# inside scrape_author, right after processing a page
sleep_s = 0.8 + random.random() * 0.7  # ~0.8–1.5s
time.sleep(sleep_s)
headers = {'Accept-Encoding': 'identity', 'User-Agent': 'Defined'}
scraper = cloudscraper.create_scraper()
conn = sqlite3.connect("../database/links.db", check_same_thread = False)
cursor = conn.cursor()
cursor.execute("create table if not exists links (url text, author text, article text, downloaded integer)")

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
                    cursor.execute(
                        "INSERT INTO links(url, author, article, downloaded) VALUES (?, ?, ?, ?);",
                        (href, author, article_html, 0),
                    )
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

