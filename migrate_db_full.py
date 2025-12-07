import sqlite3
import os
import uuid

DB_PATH = "pharmapos.db"

def migrate_db_full():
    """Add all missing columns to existing database tables."""
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found. Nothing to migrate.")
        return

    print(f"Migrating database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get existing columns for each table
    def get_columns(table_name):
        cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cursor.fetchall()]

    # Add missing columns to stores table
    print("Checking stores table...")
    stores_columns = get_columns("stores")
    
    if "phone" not in stores_columns:
        print("  Adding phone column to stores...")
        cursor.execute("ALTER TABLE stores ADD COLUMN phone TEXT")
    
    if "email" not in stores_columns:
        print("  Adding email column to stores...")
        cursor.execute("ALTER TABLE stores ADD COLUMN email TEXT")
    
    if "is_active" not in stores_columns:
        print("  Adding is_active column to stores...")
        cursor.execute("ALTER TABLE stores ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL")

    # Add missing columns to products table
    print("Checking products table...")
    products_columns = get_columns("products")
    
    if "category" not in products_columns:
        print("  Adding category column to products...")
        cursor.execute("ALTER TABLE products ADD COLUMN category TEXT")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate_db_full()
