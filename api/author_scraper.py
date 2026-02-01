from sqlmodel import Session
from scraper_utils import scrape_author, format_author_name
from models import create_db_and_tables, engine

create_db_and_tables()

if __name__ == "__main__":
    print ("Starting author scraper. Provide empty author name to exit")
    while True: 
        author = format_author_name(input("\nEnter author name (as in URL, e.g. 'j-k-rowling'): "))

        if author in ['exit', 'e', 'n', 'q', 'quit','' ]: 
            break
        print("Author: ", author)
        with Session(engine) as session:
            result = scrape_author(author, session)
        if result['success']:
            print(f"Successfully added {result['books_added']} books!")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")

