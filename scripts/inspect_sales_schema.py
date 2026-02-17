import sqlite3
import os

db_path = 'pharmapos.db'
if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Current columns in 'sales' table:")
cursor.execute("PRAGMA table_info(sales)")
columns = [row[1] for row in cursor.fetchall()]
for col in columns:
    print(f" - {col}")

expected = [
    "id", "receipt_number", "total_amount", "amount_paid", "payment_method", 
    "payment_reference", "gateway_response", "change_amount", "customer_id", 
    "user_id", "store_id", "synced_to_cloud", "created_at", "updated_at", 
    "sync_id", "sync_status", "last_synced_at", "is_deleted"
]

print("\nMissing columns:")
for col in expected:
    if col not in columns:
        print(f" [MISSING] {col}")

conn.close()
