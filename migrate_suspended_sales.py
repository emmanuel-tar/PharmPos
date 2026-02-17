import sqlite3
import os

db_path = "pharmapos.db"

def create_table_if_not_exists(cursor, table_name, sql):
    print(f"Checking table '{table_name}'...")
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    if not cursor.fetchone():
        print(f"Creating table '{table_name}'...")
        cursor.execute(sql)
    else:
        print(f"Table '{table_name}' already exists.")

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Create suspended_sales
        ss_sql = """
        CREATE TABLE suspended_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT,
            total_amount NUMERIC(10, 2) NOT NULL,
            customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL ON UPDATE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
            store_id INTEGER NOT NULL REFERENCES stores(id) ON DELETE RESTRICT ON UPDATE CASCADE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
        """
        create_table_if_not_exists(cursor, "suspended_sales", ss_sql)
        
        # 2. Create suspended_sale_items
        ssi_sql = """
        CREATE TABLE suspended_sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            suspended_sale_id INTEGER NOT NULL REFERENCES suspended_sales(id) ON DELETE CASCADE ON UPDATE CASCADE,
            product_batch_id INTEGER NOT NULL REFERENCES product_batches(id) ON DELETE RESTRICT ON UPDATE CASCADE,
            quantity INTEGER NOT NULL,
            unit_price NUMERIC(10, 2) NOT NULL
        )
        """
        create_table_if_not_exists(cursor, "suspended_sale_items", ssi_sql)
        
        conn.commit()
        conn.close()
        print("\nDatabase migration for suspended sales tables complete.")
    except Exception as e:
        print(f"Error during migration: {e}")
else:
    print(f"Database file not found at {db_path}")
