
import sqlite3
import os
from desktop_app.config import DB_PATH
from desktop_app.database import init_db

def migrate():
    print(f"Starting migration for database at: {DB_PATH}")
    
    # 1. Ensure all new tables are created
    print("Initializing database (creating new tables)...")
    init_db()
    
    # 2. Add missing columns to existing tables
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("Adding 'warehouse_location' to 'products' table...")
        cursor.execute("ALTER TABLE products ADD COLUMN warehouse_location TEXT")
        conn.commit()
        print("Successfully added 'warehouse_location' column.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'warehouse_location' already exists.")
        else:
            print(f"Error adding column: {e}")
            
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
