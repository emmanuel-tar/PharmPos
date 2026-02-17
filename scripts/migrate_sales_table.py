import sqlite3
import os

db_path = 'pharmapos.db'
if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get existing columns
cursor.execute("PRAGMA table_info(sales)")
existing_columns = [row[1] for row in cursor.fetchall()]

# Define missing columns to add
# Column name, Type, Default (optional)
to_add = [
    ("payment_reference", "TEXT", "NULL"),
    ("gateway_response", "TEXT", "NULL"),
    ("customer_id", "INTEGER", "NULL"),
    ("synced_to_cloud", "BOOLEAN", "0"),
    ("updated_at", "DATETIME", "CURRENT_TIMESTAMP"),
    ("sync_id", "TEXT", "NULL"),
    ("sync_status", "TEXT", "'pending'"),
    ("last_synced_at", "DATETIME", "NULL"),
    ("is_deleted", "BOOLEAN", "0")
]

added_count = 0
for col_name, col_type, default in to_add:
    if col_name not in existing_columns:
        print(f"Adding column '{col_name}'...")
        try:
            sql = f"ALTER TABLE sales ADD COLUMN {col_name} {col_type} DEFAULT {default}"
            cursor.execute(sql)
            added_count += 1
        except Exception as e:
            print(f"Error adding {col_name}: {e}")

conn.commit()
conn.close()

if added_count > 0:
    print(f"Migration completed. Added {added_count} columns.")
else:
    print("No columns were missing. Schema is up to date.")
