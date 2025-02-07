import requests
import json
import csv
import time

def get_google_books(output_file, limit=1000):
    print("Starting Google Books crawler...")
    
    search_queries = [
        # Highly popular fiction categories
        "subject:fiction+best+sellers",
        "new+york+times+bestseller",
        # Major book awards
        "pulitzer+prize+winner+book",
        "national+book+award+winner",
        # Popular genres with high publication rates
        "popular+romance+novels",
        "best+selling+thriller+books",
        "top+mystery+books",
        # Specific popular series/authors
        "harry+potter+rowling",
        "stephen+king+books",
        "john+grisham+books",
        "dan+brown+books",
        "james+patterson+books"
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ID', 'Title', 'Author', 'Year', 'Publisher', 'ISBN', 'Format', 'Language', 'URL'])
        
        count = 0
        
        for query in search_queries:
            if count >= limit:
                break
                
            start_index = 0
            while count < limit:
                try:
                    url = (f"https://www.googleapis.com/books/v1/volumes?"
                          f"q={query}"
                          f"&startIndex={start_index}"
                          f"&maxResults=40"
                          f"&printType=books"
                          f"&orderBy=relevance"
                          f"&langRestrict=en")
                    
                    print(f"Fetching books for '{query}' from index {start_index}...")
                    
                    response = requests.get(url)
                    response.raise_for_status()
                    data = response.json()
                    
                    items = data.get('items', [])
                    if not items:
                        print(f"No more books found for query '{query}'")
                        break
                    
                    print(f"Found {len(items)} books on this page")
                    
                    for book in items:
                        try:
                            info = book.get('volumeInfo', {})
                            
                            # Skip books without titles or authors
                            if not info.get('title') or not info.get('authors'):
                                continue
                                
                            # Extract book details
                            book_id = f"gb_{book.get('id', '')}"
                            title = info.get('title', '')
                            authors = ', '.join(info.get('authors', []))
                            
                            # Handle date formats
                            published_date = info.get('publishedDate', '')
                            year = published_date[:4] if published_date else ''
                            
                            publisher = info.get('publisher', '')
                            
                            # Get ISBN (try ISBN-13 first, then ISBN-10)
                            identifiers = info.get('industryIdentifiers', [])
                            isbn = ''
                            for identifier in identifiers:
                                if identifier.get('type') in ['ISBN_13', 'ISBN_10']:
                                    isbn = identifier.get('identifier', '')
                                    break
                            
                            format = 'Paperback'  # Default value
                            language = info.get('language', '')
                            url = info.get('infoLink', '')
                            
                            writer.writerow([
                                book_id, title, authors, year, publisher,
                                isbn, format, language, url
                            ])
                            
                            count += 1
                            print(f"Processed book {count}: {title}")
                            
                            if count >= limit:
                                break
                                
                        except Exception as e:
                            print(f"Error processing book: {e}")
                            continue
                            
                    start_index += 40
                    time.sleep(2)  # Increased delay between requests
                    
                except Exception as e:
                    print(f"Error fetching books: {e}")
                    if 'response' in locals():
                        print(f"Response status: {response.status_code}")
                        print(f"Response text preview: {response.text[:200]}")
                    break
                    
        print(f"Total books processed: {count}")

def main():
    get_google_books('table_b.csv')
    print("Finished!")

if __name__ == "__main__":
    main()
