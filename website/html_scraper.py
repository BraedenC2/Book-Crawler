import os
import csv
import asyncio
import aiohttp
import time
import random
from urllib.parse import urlparse, urlsplit
from pathlib import Path
from itertools import islice

def create_html_folder():
    # Remove the '../' from the path
    html_folder = Path("website/data/html")
    html_folder.mkdir(parents=True, exist_ok=True)
    print(f"HTML folder created/verified at: {html_folder.absolute()}")
    return html_folder

def sanitize_filename(url):
    # Create a safe filename from URL
    parsed = urlparse(url)
    filename = parsed.netloc + parsed.path.replace('/', '_')
    if not filename.endswith('.html'):
        filename += '.html'
    return filename.replace(':', '_')

async def save_html_async(url, folder, session, semaphore, retries=5):
    try:
        async with semaphore:  # Limit concurrent connections
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5'
            }
            
            domain = urlsplit(url).netloc
            
            for attempt in range(retries):
                try:
                    # Add random delay between requests to same domain
                    await asyncio.sleep(2 + random.random() * 3)  # 2-5 seconds delay
                    
                    async with session.get(url, headers=headers, timeout=60) as response:
                        if response.status == 200:
                            content = await response.text()
                            filename = sanitize_filename(url)
                            filepath = folder / filename
                            
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(content)
                            print(f"Successfully saved HTML for: {url}")
                            return True
                        elif response.status == 429:  # Too Many Requests
                            wait_time = 30 + (attempt * 30) + (random.random() * 30)
                            print(f"Rate limited for {domain}. Waiting {wait_time:.0f} seconds...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            print(f"Error {response.status} for URL: {url}")
                            if attempt < retries - 1:
                                wait_time = (2 ** attempt) + random.random()  # Exponential backoff
                                await asyncio.sleep(wait_time)
                                continue
                except Exception as e:
                    if attempt < retries - 1:
                        wait_time = (2 ** attempt) + random.random()
                        await asyncio.sleep(wait_time)
                        continue
                    print(f"Error scraping {url}: {str(e)}")
            return False
                    
    except Exception as e:
        print(f"Fatal error with {url}: {str(e)}")
        return False

async def process_url_batch(urls, html_folder, batch_size=20):
    # Reduce concurrent connections to 5
    semaphore = asyncio.Semaphore(5)
    
    # Group URLs by domain
    domain_groups = {}
    for url in urls:
        domain = urlsplit(url).netloc
        if domain not in domain_groups:
            domain_groups[domain] = []
        domain_groups[domain].append(url)
    
    async with aiohttp.ClientSession() as session:
        total = len(urls)
        processed = 0
        
        # Process each domain separately
        for domain, domain_urls in domain_groups.items():
            print(f"\nProcessing domain: {domain}")
            
            for i in range(0, len(domain_urls), batch_size):
                batch = domain_urls[i:i + batch_size]
                batch_num = (processed + i) // batch_size + 1
                print(f"\nProcessing batch {batch_num} ({processed+1}-{processed+len(batch)}/{total})")
                
                tasks = []
                for url in batch:
                    if url.strip():
                        task = save_html_async(url, html_folder, session, semaphore)
                        tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                success = sum(1 for r in results if r)
                print(f"Batch complete: {success}/{len(batch)} successful")
                
                # Longer delay between batches
                await asyncio.sleep(5)
                
                processed += len(batch)

def get_url_column_name(headers):
    # Common variations of URL column names
    url_columns = ['url', 'URL', 'link', 'Link', 'href', 'web_url', 'web_link']
    for column in url_columns:
        if column in headers:
            return column
    return None

def process_csv_files():
    # Remove the '../' from the path
    csv_folder = Path("website/data")
    if not csv_folder.exists():
        print(f"Error: CSV folder not found at {csv_folder.absolute()}")
        return

    html_folder = create_html_folder()
    urls_to_process = []
    
    # Process each CSV file
    for csv_file in csv_folder.glob("*.csv"):
        print(f"\nReading {csv_file.name}:")
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                
                # Determine URL column based on file
                url_column = None
                if 'table_a.csv' in csv_file.name:
                    url_column = next((col for col in ['URL', 'url', 'Link', 'link'] if col in headers), None)
                elif 'table_b.csv' in csv_file.name:
                    url_column = 'preview_link'
                
                if url_column and url_column in headers:
                    file_urls = [row[url_column].strip() for row in reader if row.get(url_column)]
                    urls_to_process.extend(file_urls)
                    print(f"Found {len(file_urls)} URLs in {csv_file.name}")
                else:
                    print(f"No suitable URL column found in {csv_file.name}")
                    
        except Exception as e:
            print(f"Error reading {csv_file.name}: {str(e)}")

    if not urls_to_process:
        print("No URLs found in CSV files!")
        return
    
    # Remove duplicates while preserving order
    urls_to_process = list(dict.fromkeys(urls_to_process))
    
    print(f"\nStarting to process {len(urls_to_process)} unique URLs...")
    start_time = time.time()
    
    # Process URLs in batches
    asyncio.run(process_url_batch(urls_to_process, html_folder))
    
    total_time = time.time() - start_time
    print(f"\nCompleted! Total time: {total_time/60:.1f} minutes")
    print(f"Files saved in: {html_folder.absolute()}")

if __name__ == "__main__":
    process_csv_files()
