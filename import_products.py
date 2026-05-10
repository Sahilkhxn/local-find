import sqlite3, csv, os

DB_PATH = os.path.join(os.path.dirname(__file__), 'localfind.db')
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS category_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    product TEXT NOT NULL
)
""")

cur.execute("DELETE FROM category_products")

cat_map = {
    'Electronics': 'electronics',
    'Kirana': 'kirana',
    'Clothing': 'kapde',
    'Pharmacy': 'dawai',
    'Jewellery': 'jewellery',
    'Furniture': 'furniture',
}

csv_path = os.path.join(os.path.dirname(__file__), 'shop_products_list.csv')
count = 0
with open(csv_path, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        cat = cat_map.get(row['Category'].strip(), row['Category'].strip().lower())
        prod = row['Product'].strip()
        cur.execute("INSERT INTO category_products (category, product) VALUES (?,?)", (cat, prod))
        count += 1

conn.commit()
conn.close()
print(f"✅ {count} products import ho gaye!")