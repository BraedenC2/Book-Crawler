import requests
from bs4 import BeautifulSoup
import csv
import time
import os
from urllib.parse import urljoin

def get_book_details(url):
    """Extract book details from an OpenLibrary page"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract book details
        title = soup.find('h1', class_='work-title').text.strip()
        author = soup.find('h2', class_='edition-byline').text.replace('by', '').strip()
        year = soup.find('div', class_='publish-date').text.split()[-1].strip()
        isbn = soup.find('div', class_='edition-isbn').text.replace('ISBN:', '').strip()
        publisher = soup.find('div', class_='edition-publisher').text.strip()
        
        # Get additional metadata
        format_elem = soup.find('div', class_='edition-format')
        book_format = format_elem.text.strip() if format_elem else 'Paperback'
        
        language_elem = soup.find('div', class_='edition-language')
        language = language_elem.text.strip() if language_elem else 'eng'
        
        return {
            'Title': title,
            'Author': author,
            'Year': year,
            'ISBN': isbn,
            'Publisher': publisher,
            'Format': book_format,
            'Language': language,
            'URL': url
        }
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")
        return None

def main():
    base_url = "https://openlibrary.org"
    books = []
    seen_urls = set()
    
    # Create output directory if it doesn't exist
    os.makedirs('website/data', exist_ok=True)
    
    # Process popular books pages
    for page in range(1, 51):  # Collect ~1000 books
        try:
            url = f"{base_url}/trending/daily?page={page}"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find book links
            for book_link in soup.find_all('a', class_='work-title'):
                book_url = urljoin(base_url, book_link['href'])
                
                if book_url not in seen_urls:
                    seen_urls.add(book_url)
                    
                    # Get book details
                    book_data = get_book_details(book_url)
                    if book_data:
                        # Add unique ID
                        book_data['ID'] = f"ol_{len(books):06d}"
                        books.append(book_data)
                        print(f"Processed: {book_data['Title']}")
                    
                    # Respect rate limiting
                    time.sleep(1)
                
                if len(books) >= 1000:
                    break
            
            if len(books) >= 1000:
                break
                
        except Exception as e:
            print(f"Error processing page {page}: {str(e)}")
            continue
    
    # Save to CSV
    if books:
        output_file = 'website/data/table_a.csv'
        fieldnames = ['ID', 'Title', 'Author', 'Year', 'Publisher', 'ISBN', 'Format', 'Language', 'URL']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(books)
        
        print(f"\nScraped {len(books)} books to {output_file}")

if __name__ == "__main__":
    main()
