import sqlite3
import os

db_path = 'pharmapos.db'
if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get existing columns
cursor.execute("PRAGMA table_info(products)")
existing_columns = [row[1] for row in cursor.fetchall()]

if 'image_path' not in existing_columns:
    print("Adding column 'image_path' to 'products' table...")
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN image_path TEXT")
        conn.commit()
        print("Column added successfully.")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Column 'image_path' already exists.")

conn.close()
