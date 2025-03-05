import csv
from difflib import SequenceMatcher
import re

def normalize_text(text):
    if not text:
        return ''
    # Convert to lowercase and remove special characters and removes whitespace
    text = re.sub(r'[^\w\s]', '', text.lower())
    return ' '.join(text.split())

def normalize_isbn(isbn):
    if not isbn:
        return ''
    # This removes all non-digit characters
    return re.sub(r'[^0-9X]', '', isbn.upper())

def exact_match(str1, str2):
    """Check if two strings match exactly after normalization"""
    if not str1 or not str2:
        return False
    return normalize_text(str1) == normalize_text(str2)

def is_similar(str1, str2, threshold=0.85):
    """Check if two strings are very similar"""
    if not str1 or not str2:
        return False
    return SequenceMatcher(None, normalize_text(str1), normalize_text(str2)).ratio() >= threshold

def create_blocking_key(record, blocking_fields):
    """Create a blocking key from specified fields to group similar records"""
    key_parts = []
    for field in blocking_fields:
        if field in record:
            value = normalize_text(record[field])[:3]
            key_parts.append(value)
    return '_'.join(key_parts)

def get_key_column_name(headers):
    """Determine the key column name from headers"""
    # Common key column names in order of preference incase I decided to change it later for crawling for more books
    key_names = ['ID', 'Id', 'id', 'KEY', 'Key', 'key']
    for name in key_names:
        if name in headers:
            return name
    return 'ID'  # Default ofc

def match_tables(table_a_path, table_b_path, output_path):
    # Read tables and get headers
    with open(table_a_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        table_a_headers = reader.fieldnames
        table_a = list(reader)
    
    with open(table_b_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        table_b_headers = reader.fieldnames
        table_b = list(reader)
    
    key_a = get_key_column_name(table_a_headers)
    key_b = get_key_column_name(table_b_headers)
    
    output_headers = [
        'ID',
        f'ltable_{key_a.lower()}',
        f'rtable_{key_b.lower()}'
    ]
    
    for header in table_a_headers:
        if header != key_a:
            output_headers.append(f'ltable_{header}')
    for header in table_b_headers:
        if header != key_b:
            output_headers.append(f'rtable_{header}')
    
    blocking_fields = ['Title', 'Author']
    blocks = {}
    for record in table_b:
        block_key = create_blocking_key(record, blocking_fields)
        if block_key not in blocks:
            blocks[block_key] = []
        blocks[block_key].append(record)
    
    matches = []
    matched_pairs = set()
    
    for record_a in table_a:
        block_key = create_blocking_key(record_a, blocking_fields)
        if block_key not in blocks:
            continue
        
        for record_b in blocks[block_key]:
            pair_key = (record_a[key_a], record_b[key_b])
            if pair_key in matched_pairs:
                continue
            
            match_score = 0
            total_weight = 0
            
            field_weights = {
                'Title': 0.4,
                'Author': 0.4,
                'ISBN': 0.2,
            }
            
            for field, weight in field_weights.items():
                if field in record_a and field in record_b:
                    if is_similar(record_a[field], record_b[field]):
                        match_score += weight
                    total_weight += weight
            
            if total_weight > 0:
                final_score = match_score / total_weight
                if final_score >= 0.8:
                    match_record = {
                        'ID': len(matches),
                        f'ltable_{key_a.lower()}': record_a[key_a],
                        f'rtable_{key_b.lower()}': record_b[key_b]
                    }
                    
                    for header in table_a_headers:
                        if header != key_a:
                            match_record[f'ltable_{header}'] = record_a[header]
                    for header in table_b_headers:
                        if header != key_b:
                            match_record[f'rtable_{header}'] = record_b[header]
                    
                    matches.append(match_record)
                    matched_pairs.add(pair_key)
    
    # output the table ->
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=output_headers)
        writer.writeheader()
        writer.writerows(matches)
    
    return len(matches)

if __name__ == "__main__":
    matches = match_tables('data/table_a.csv', 'data/table_b.csv', 'data/table_c.csv')
    print(f"Found {matches} matching record pairs")
