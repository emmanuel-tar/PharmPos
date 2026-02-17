import sqlite3
import os

db_path = "pharmapos.db"

def fix_table(cursor, table_name, expected_columns):
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    for col_name, col_type in expected_columns:
        if col_name not in existing_columns:
            print(f"Adding column '{col_name}' to '{table_name}'...")
            try:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Failed to add '{col_name}': {e}")

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Fix purchase_receipts
        pr_cols = [
            ("purchase_order_id", "INTEGER"),
            ("product_id", "INTEGER"),
            ("batch_id", "INTEGER"),
            ("received_quantity", "INTEGER DEFAULT 0"),
            ("actual_cost_price", "NUMERIC(10, 2)"),
            ("received_date", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("received_by", "INTEGER"),
            ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("sync_id", "TEXT"),
            ("sync_status", "TEXT DEFAULT 'pending'"),
            ("last_synced_at", "DATETIME"),
            ("is_deleted", "BOOLEAN DEFAULT 0")
        ]
        fix_table(cursor, "purchase_receipts", pr_cols)
        
        # 2. Fix purchase_receipt_items
        pri_cols = [
            ("receipt_id", "INTEGER"),
            ("product_id", "INTEGER"),
            ("batch_number", "TEXT"),
            ("expiry_date", "DATE"),
            ("quantity", "INTEGER DEFAULT 0"),
            ("cost_price", "NUMERIC(10, 2)"),
            ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
        ]
        fix_table(cursor, "purchase_receipt_items", pri_cols)
        
        conn.commit()
        conn.close()
        print("\nDatabase migration for procurement tables complete.")
    except Exception as e:
        print(f"Error during migration: {e}")
else:
    print(f"Database file not found at {db_path}")
