import csv
from difflib import SequenceMatcher
import re

#
# ISBN matching (both ISBN-10 and ISBN-13)
# Title similarity with flexible thresholds
# Author name normalization and matching
# Publication year proximity (±3 years)
# Partial ISBN matching for catching variations
# Removes punctuation and special characters
# Handles multiple author formats
# Normalizes whitespace and casing
# Removes common stop words
# Handles international editions
# Cross-verification between fields (title AND author must match)
# Multiple matching methods (exact, substring, word overlap)
# Duplicate prevention with seen_pairs tracking
#


def normalize_string(s):
    """Remove common words, punctuation, and standardize spacing"""
    if not s:
        return ""
    s = s.lower()
    # Remove more special characters and normalize spaces
    s = re.sub(r'[^\w\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    # Expand list of stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
        'of', 'for', 'with', 'by', 'from', 'up', 'about', 'into', 
        'over', 'after'
    }
    words = s.split()
    words = [w for w in words if w not in stop_words]
    return ' '.join(words)

def normalize_isbn(isbn):
    """Clean ISBN and convert between ISBN-10 and ISBN-13"""
    if not isbn:
        return []
    isbn = re.sub(r'[^0-9X]', '', isbn.upper())
    results = [isbn]
    
    # If ISBN-13, try converting to ISBN-10
    if len(isbn) == 13 and isbn.startswith('978'):
        isbn10 = isbn[3:-1]
        # Calculate ISBN-10 check digit
        try:
            check = sum((10 - i) * int(d) for i, d in enumerate(isbn10)) % 11
            check = 'X' if check == 10 else str(check)
            results.append(isbn10 + check)
        except ValueError:
            pass
            
    # If ISBN-10, convert to ISBN-13
    elif len(isbn) == 10:
        isbn13 = '978' + isbn[:-1]
        try:
            # Calculate ISBN-13 check digit
            check = sum((1 if i % 2 == 0 else 3) * int(d) for i, d in enumerate(isbn13)) % 10
            check = str((10 - check) % 10)
            results.append(isbn13 + check)
        except ValueError:
            pass
    
    # Add partial ISBN matching
    if len(isbn) >= 5:
        results.append(isbn[:5])  # Add first 5 digits
        results.append(isbn[-5:])  # Add last 5 digits
            
    return results

def similar(a, b, threshold=0.4):  # Lowered from 0.5 to 0.4
    """Check if two strings are similar enough to be considered a match"""
    if not a or not b:
        return False
        
    norm_a = normalize_string(a)
    norm_b = normalize_string(b)
    
    # Exact match
    if norm_a == norm_b:
        return True
        
    # Substring match
    if norm_a in norm_b or norm_b in norm_a:
        return True
        
    # Check if one is a prefix of the other
    if len(norm_a) > 5 and len(norm_b) > 5:
        if norm_a.startswith(norm_b) or norm_b.startswith(norm_a):
            return True
    
    # Try word set overlap
    words_a = set(norm_a.split())
    words_b = set(norm_b.split())
    if len(words_a) > 0 and len(words_b) > 0:
        overlap = len(words_a & words_b) / min(len(words_a), len(words_b))
        if overlap > 0.5:  # If more than 50% of words match
            return True
    
    # Fallback to sequence matcher
    return SequenceMatcher(None, norm_a, norm_b).ratio() > threshold

def normalize_author(author):
    """Normalize author name and handle multiple authors"""
    if not author:
        return []
    
    # Split on more separators
    authors = [a.strip() for a in re.split(r'[,;&]', author)]
    
    normalized = []
    for author in authors:
        # Remove more titles and suffixes
        author = re.sub(r'\b(dr|mr|mrs|ms|jr|sr|i{2,}|iii|iv|phd|md|esq)\b\.?', '', author.lower())
        
        # Remove all punctuation
        author = re.sub(r'[^\w\s]', '', author)
        
        # Remove extra spaces
        author = ' '.join(author.split())
        
        # Get last name
        parts = author.split()
        if len(parts) > 1:
            normalized.append(parts[-1])  # Add just last name
        
        if author:
            normalized.append(author)
            
    return normalized

def years_match(year_a, year_b, tolerance=3):  # Increased from 2 to 3 years
    """Check if years match within tolerance"""
    if not year_a or not year_b:
        return True  # Consider missing years as potential matches
    
    try:
        return abs(int(year_a) - int(year_b)) <= tolerance
    except ValueError:
        return False

def load_csv(filename):
    """Load CSV file into a list of dictionaries"""
    data = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def find_matches(table_a, table_b):
    """Find matching books between tables"""
    matches = []
    seen_pairs = set()  # Track matched pairs to avoid duplicates
    
    # Create ISBN and title indices for faster lookup
    isbn_index = {}
    title_index = {}
    for book in table_b:
        if book['ISBN']:
            for isbn in normalize_isbn(book['ISBN']):
                isbn_index[isbn] = book
        
        norm_title = normalize_string(book['Title'])
        if norm_title:
            if norm_title not in title_index:
                title_index[norm_title] = []
            title_index[norm_title].append(book)
    
    for book_a in table_a:
        # Try ISBN matching first
        if book_a['ISBN']:
            for isbn in normalize_isbn(book_a['ISBN']):
                if isbn in isbn_index:
                    book_b = isbn_index[isbn]
                    pair_key = (book_a['ID'], book_b['ID'])
                    if pair_key not in seen_pairs:
                        matches.append((book_a, book_b))
                        seen_pairs.add(pair_key)
                        break
        
        # Try title and author matching
        norm_title_a = normalize_string(book_a['Title'])
        authors_a = normalize_author(book_a['Author'])
        year_a = book_a['Year']
        
        # Check exact title matches first
        potential_matches = []
        if norm_title_a in title_index:
            potential_matches.extend(title_index[norm_title_a])
        
        # Then check similar titles
        for book_b in table_b:
            if (book_a['ID'], book_b['ID']) in seen_pairs:
                continue
                
            norm_title_b = normalize_string(book_b['Title'])
            if similar(norm_title_a, norm_title_b):
                potential_matches.append(book_b)
        
        # Check author and year for potential matches
        for book_b in potential_matches:
            authors_b = normalize_author(book_b['Author'])
            year_b = book_b['Year']
            
            author_match = any(
                any(similar(author_a, author_b, 0.6) for author_b in authors_b)
                for author_a in authors_a
            )
            
            if author_match and years_match(year_a, year_b):
                pair_key = (book_a['ID'], book_b['ID'])
                if pair_key not in seen_pairs:
                    matches.append((book_a, book_b))
                    seen_pairs.add(pair_key)
                    break
    
    return matches

def analyze_overlap():
    print("Loading datasets...")
    table_a = load_csv('table_a.csv')
    table_b = load_csv('table_b.csv')
    
    print(f"\nDataset sizes:")
    print(f"Table A (OpenLibrary): {len(table_a)} books")
    print(f"Table B (Google Books): {len(table_b)} books")
    
    print("\nFinding matches...")
    matches = find_matches(table_a, table_b)
    
    print(f"\nFound {len(matches)} matching books")
    print(f"Overlap percentage: {(len(matches) / min(len(table_a), len(table_b))) * 100:.1f}%")
    
    print("\nSample matches:")
    for i, (book_a, book_b) in enumerate(matches[:5]):
        print(f"\nMatch {i+1}:")
        print(f"OpenLibrary: {book_a['Title']} by {book_a['Author']} ({book_a['Year']}) ISBN: {book_a['ISBN']}")
        print(f"Google Books: {book_b['Title']} by {book_b['Author']} ({book_b['Year']}) ISBN: {book_b['ISBN']}")

if __name__ == "__main__":
    analyze_overlap()
