import sqlite3
import os

db_path = "pharmapos.db"

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get columns for purchase_receipts
        cursor.execute("PRAGMA table_info(purchase_receipts)")
        print("purchase_receipts columns:")
        for row in cursor.fetchall():
            print(f"- {row[1]} ({row[2]})")
            
        print("\npurchase_receipt_items columns:")
        cursor.execute("PRAGMA table_info(purchase_receipt_items)")
        for row in cursor.fetchall():
            print(f"- {row[1]} ({row[2]})")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"Database file not found at {db_path}")
