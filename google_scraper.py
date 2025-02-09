import csv
import asyncio
import aiohttp
import time
from pathlib import Path

def create_html_folder():
    html_folder = Path("website/data/html2")
    html_folder.mkdir(parents=True, exist_ok=True)
    print(f"HTML folder created at: {html_folder.absolute()}")
    return html_folder

async def download_page(url, folder, session, semaphore):
    async with semaphore:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124'
            }
            async with session.get(url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    content = await response.text()
                    # Use the ID from the URL as filename
                    if 'id=' in url:
                        book_id = url.split('id=')[1].split('&')[0]
                        filename = f"{book_id}.html"
                    else:
                        filename = f"{url.replace('https://', '').replace('/', '_')}.html"
                    filepath = folder / filename
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Saved: {filename}")
                    return True
                else:
                    print(f"Error {response.status}: {url}")
                    return False
        except Exception as e:
            print(f"Failed {url}: {str(e)}")
            return False

async def process_urls(urls, folder):
    semaphore = asyncio.Semaphore(5)  # 5 concurrent downloads so it isn't so slow (using async btw)
    successful = 0
    total = len(urls)
    
    async with aiohttp.ClientSession() as session:
        for i, url in enumerate(urls, 1):
            print(f"\nProcessing {i}/{total}: {url}")
            if await download_page(url, folder, session, semaphore):
                successful += 1
            # Add delay between requests so the website doesn't block us with too many requests
            await asyncio.sleep(1)
            
            if i % 10 == 0:  # Status update every 10 URLs so we know it's still working
                print(f"\nProgress: {i}/{total} URLs processed ({successful} successful)")

    return successful

async def main():
    html_folder = create_html_folder()
    csv_path = Path("website/data/table_b.csv")
    
    # Get URLs from the CSV file (table_b)
    urls = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        print(f"CSV Headers: {reader.fieldnames}")
        
        # Debug first few rows
        print("\nChecking first few rows:")
        for i, row in enumerate(reader):
            if 'URL' in row and row['URL'].strip():
                url = row['URL'].strip()
                if 'google' in url.lower():
                    urls.append(url)
                    print(f"Found Google URL: {url}")
            
            if i < 3:
                print(f"\nRow {i+1}:")
                print(f"Title: {row.get('Title', 'No title')}")
                print(f"URL: {row.get('URL', 'No URL')}")
    
    print(f"\nFound {len(urls)} Google URLs to process")
    if urls:
        start_time = time.time()
        successful = await process_urls(urls, html_folder)
        elapsed_time = time.time() - start_time
        print(f"\nFinished! {successful} out of {len(urls)} files downloaded")
        print(f"Total time: {elapsed_time/60:.1f} minutes")
    else:
        print("No valid URLs found! Make sure URLs contain 'google'")

if __name__ == "__main__":
    asyncio.run(main())
