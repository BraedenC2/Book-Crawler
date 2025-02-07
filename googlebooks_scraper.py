import requests
import csv
import time
import os
from urllib.parse import quote

def get_book_details(item):
    """Extract book details from Google Books API response"""
    try:
        volume_info = item['volumeInfo']
        
        # Extract basic information
        title = volume_info.get('title', '').strip()
        authors = volume_info.get('authors', ['Unknown'])
        author = authors[0].strip()
        
        # Extract year
        published_date = volume_info.get('publishedDate', '')
        year = published_date.split('-')[0] if published_date else ''
        
        # Extract ISBN (prefer ISBN-13)
        isbns = volume_info.get('industryIdentifiers', [])
        isbn = ''
        for isbn_data in isbns:
            if isbn_data['type'] == 'ISBN_13':
                isbn = isbn_data['identifier']
                break
        if not isbn and isbns:
            isbn = isbns[0]['identifier']
        
        # Extract additional metadata
        publisher = volume_info.get('publisher', '').strip()
        language = volume_info.get('language', 'eng').strip()
        
        return {
            'Title': title,
            'Author': author,
            'Year': year,
            'ISBN': isbn,
            'Publisher': publisher,
            'Format': 'Paperback',  # Default format
            'Language': language
        }
    except Exception as e:
        print(f"Error processing book: {str(e)}")
        return None

def main():
    api_key = 'YOUR_GOOGLE_BOOKS_API_KEY'  # Replace with actual API key
    books = []
    
    # Create output directory if it doesn't exist
    os.makedirs('website/data', exist_ok=True)
    
    # Search terms to get a good variety of books
    search_terms = [
        'bestseller', 'classic literature', 'award winning',
        'popular fiction', 'contemporary novel'
    ]
    
    for term in search_terms:
        start_index = 0
        
        while len(books) < 1000:
            try:
                # Construct API URL
                url = f"https://www.googleapis.com/books/v1/volumes"
                params = {
                    'q': quote(term),
                    'key': api_key,
                    'startIndex': start_index,
                    'maxResults': 40,
                    'printType': 'books'
                }
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if 'items' not in data:
                    break
                
                # Process each book
                for item in data['items']:
                    book_data = get_book_details(item)
                    if book_data and all(book_data.values()):
                        # Add unique ID
                        book_data['ID'] = f"gb_{len(books):06d}"
                        books.append(book_data)
                        print(f"Processed: {book_data['Title']}")
                    
                    if len(books) >= 1000:
                        break
                
                start_index += 40
                time.sleep(1)  # Respect rate limiting
                
            except Exception as e:
                print(f"Error processing search term '{term}': {str(e)}")
                break
    
    # Save to CSV
    if books:
        output_file = 'website/data/table_b.csv'
        fieldnames = ['ID', 'Title', 'Author', 'Year', 'Publisher', 'ISBN', 'Format', 'Language']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(books)
        
        print(f"\nScraped {len(books)} books to {output_file}")

if __name__ == "__main__":
    main()
