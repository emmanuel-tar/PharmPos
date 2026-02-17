import sqlite3
import os

db_path = "pharmapos.db"

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='purchase_receipts'")
        row = cursor.fetchone()
        if row:
            print("Full SQL for purchase_receipts:")
            print(row[0])
        else:
            print("Table purchase_receipts not found.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"Database file not found at {db_path}")
