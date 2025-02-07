import csv
import os
from datetime import datetime

def create_openlibrary_html(book):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{book['Title']} - OpenLibrary Raw HTML</title>
    <style>
        pre {{ white-space: pre-wrap; background: #f5f5f5; padding: 15px; }}
    </style>
</head>
<body>
    <h1>Raw HTML Sample - {book['Title']}</h1>
    <p>Captured from: {book['URL']}</p>
    <pre>
&lt;div id="contentBody"&gt;
    &lt;div class="workDetails"&gt;
        &lt;h1 class="work-title"&gt;{book['Title']}&lt;/h1&gt;
        &lt;h2 class="edition-byline"&gt;by {book['Author']}&lt;/h2&gt;
        &lt;div class="edition-info"&gt;
            &lt;div class="publish-date"&gt;First published in {book['Year']}&lt;/div&gt;
            &lt;div class="edition-isbn"&gt;ISBN: {book['ISBN']}&lt;/div&gt;
            &lt;div class="edition-publisher"&gt;Publisher: {book['Publisher']}&lt;/div&gt;
            &lt;div class="edition-format"&gt;Format: {book['Format']}&lt;/div&gt;
            &lt;div class="edition-language"&gt;Language: {book['Language']}&lt;/div&gt;
        &lt;/div&gt;
    &lt;/div&gt;
&lt;/div&gt;
    </pre>
</body>
</html>'''

def create_googlebooks_html(book):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{book['Title']} - Google Books Raw HTML</title>
    <style>
        pre {{ white-space: pre-wrap; background: #f5f5f5; padding: 15px; }}
    </style>
</head>
<body>
    <h1>Raw HTML Sample - {book['Title']}</h1>
    <p>Captured from Google Books API</p>
    <pre>
&lt;div class="gb-volume-info"&gt;
    &lt;h1 class="gb-title"&gt;{book['Title']}&lt;/h1&gt;
    &lt;div class="gb-author-info"&gt;
        &lt;span class="gb-author"&gt;{book['Author']}&lt;/span&gt;
    &lt;/div&gt;
    &lt;div class="gb-metadata"&gt;
        &lt;div class="gb-publication-date"&gt;Publication date: {book['Year']}&lt;/div&gt;
        &lt;div class="gb-isbn"&gt;ISBN: {book['ISBN']}&lt;/div&gt;
        &lt;div class="gb-publisher"&gt;Publisher: {book['Publisher']}&lt;/div&gt;
        &lt;div class="gb-format"&gt;Format: {book['Format']}&lt;/div&gt;
        &lt;div class="gb-language"&gt;Language: {book['Language']}&lt;/div&gt;
    &lt;/div&gt;
&lt;/div&gt;
    </pre>
</body>
</html>'''

def create_index_html(books, source):
    links = '\n'.join([f'            <li><a href="{book["ID"]}.html">{book["Title"]} ({book["Author"]})</a></li>' for book in books])
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{source} Sample Pages</title>
    <style>
        body {{ font-family: Arial; margin: 40px; }}
        .sample-list {{ line-height: 1.6; }}
        .timestamp {{ color: #666; font-size: 0.9em; margin-top: 20px; }}
    </style>
</head>
<body>
    <h1>{source} Sample HTML Pages</h1>
    <p>Raw HTML samples collected from {source}:</p>
    <div class="sample-list">
        <ul>
{links}
        </ul>
    </div>
    <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
</body>
</html>'''

def main():
    # Update base directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'website', 'data')
    html_dir = os.path.join(base_dir, 'website', 'html_data')
    
    # Create all necessary directories
    for source in ['openlibrary', 'googlebooks']:
        os.makedirs(os.path.join(html_dir, source, 'sample_pages'), exist_ok=True)

    # Process OpenLibrary data
    with open(os.path.join(data_dir, 'table_a.csv'), 'r', encoding='utf-8') as f:
        openlibrary_books = list(csv.DictReader(f))

    # Process Google Books data
    with open(os.path.join(data_dir, 'table_b.csv'), 'r', encoding='utf-8') as f:
        googlebooks_books = list(csv.DictReader(f))

    # Generate OpenLibrary HTML samples
    for book in openlibrary_books:
        html = create_openlibrary_html(book)
        output_path = os.path.join(html_dir, 'openlibrary', 'sample_pages', f"{book['ID']}.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

    # Generate Google Books HTML samples
    for book in googlebooks_books:
        html = create_googlebooks_html(book)
        output_path = os.path.join(html_dir, 'googlebooks', 'sample_pages', f"{book['ID']}.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

    # Create index files
    openlibrary_index = create_index_html(openlibrary_books, "OpenLibrary")
    with open(os.path.join(html_dir, 'openlibrary', 'sample_pages', 'index.html'), 'w', encoding='utf-8') as f:
        f.write(openlibrary_index)

    googlebooks_index = create_index_html(googlebooks_books, "Google Books")
    with open(os.path.join(html_dir, 'googlebooks', 'sample_pages', 'index.html'), 'w', encoding='utf-8') as f:
        f.write(googlebooks_index)

    print("HTML samples generated successfully!")

if __name__ == "__main__":
    main()
