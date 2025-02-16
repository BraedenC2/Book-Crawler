import csv

# Read the CSV file and extract languages
languages = []
with open('data/table_a.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['Language']:  # Only add if language exists
            languages.append(row['Language'])

# Print all languages separated by commas
print(','.join(languages))
