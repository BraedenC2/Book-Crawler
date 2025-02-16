import csv

# Read the CSV file and extract years
years = []
with open('data/table_a.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['Year']:  # Only add if year exists
            years.append(row['Year'])

# Print all years separated by commas
print(','.join(years))
