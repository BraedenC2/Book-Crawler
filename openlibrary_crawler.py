import requests
import json
import csv
import time

def get_openlibrary_books(output_file, limit=10000):
    print("Starting Open Library crawler...")
    
    queries = [
        # Slightly different than the google scraper. I don't want to get the same exact books
        "bestseller+fiction",
        "new+york+times+bestseller",
        "author:stephen+king",
        "author:dan+brown",
        "author:james+patterson",
        "author:john+grisham",
        "subject:romance+bestseller",
        "subject:mystery+bestseller",
        "subject:thriller+bestseller",
        "harry+potter",
        "game+of+thrones",
        "hunger+games"
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ID', 'Title', 'Author', 'Year', 'Publisher', 'ISBN', 'Format', 'Language', 'URL'])
        
        count = 0
        
        for query in queries:
            if count >= limit:
                break
                
            page = 1
            while count < limit:
                try:
                    url = (f"https://openlibrary.org/search.json?"
                          f"q={query}"
                          f"&sort=editions"
                          f"&fields=key,title,author_name,first_publish_year,"
                          f"publisher,isbn,format,language,edition_key"
                          f"&limit=100&page={page}")
                    
                    print(f"Fetching page {page}...")
                    
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    docs = data.get('docs', [])
                    if not docs:
                        print("No more books found")
                        break
                    
                    print(f"Found {len(docs)} books on this page")
                    
                    for book in docs:
                        try:
                            book_id = f"ol_{book.get('key', '').split('/')[-1]}"
                            title = book.get('title', '')
                            
                            authors = book.get('author_name', [])
                            author = authors[0] if authors else ''
                            
                            year = str(book.get('first_publish_year', ''))
                            
                            publishers = book.get('publisher', [])
                            publisher = publishers[0] if publishers else ''
                            
                            isbns = book.get('isbn', [])
                            isbn = isbns[0] if isbns else ''
                            
                            format = 'Paperback'
                            languages = book.get('language', [])
                            language = languages[0] if languages else 'eng'
                            
                            edition_keys = book.get('edition_key', [])
                            if edition_keys:
                                url = f"https://openlibrary.org/books/{edition_keys[0]}"
                            else:
                                url = f"https://openlibrary.org{book.get('key', '')}"
                            
                            writer.writerow([
                                book_id, title, author, year, publisher,
                                isbn, format, language, url
                            ])
                            
                            count += 1
                            print(f"Processed book {count}: {title}")
                            
                            if count >= limit:
                                break
                                
                        except Exception as e:
                            print(f"Error processing book: {e}")
                            continue
                    
                    page += 1
                    time.sleep(2)
                    
                except requests.exceptions.RequestException as e:
                    print(f"Network error: {e}")
                    time.sleep(5)
                    continue
                except Exception as e:
                    print(f"Error fetching books: {e}")
                    if 'response' in locals():
                        print(f"Response status: {response.status_code}")
                        print(f"Response text: {response.text[:200]}")
                    break
                
        print(f"Total books processed: {count}")

def main():
    get_openlibrary_books('table_a.csv')
    print("Finished!")

if __name__ == "__main__":
    main()
