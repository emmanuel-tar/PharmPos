import sqlite3
import os

DB_PATH = "pharmapos.db"

def migrate_db():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found. Nothing to migrate.")
        return

    print(f"Migrating database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # List of tables that should have sync columns
    tables_to_migrate = [
        "stores",
        "users",
        "products",
        "product_batches",
        "sales",
        "stock_transfers",
        "inventory_audit",
        "suppliers",
        "purchase_receipts",
        "stock_reservations",
        "stock_adjustments",
        "backorders",
        "inventory_reconciliations",
        # "reconciliation_items", # Check if this needs it, database.py suggests yes in my recent edit
        # "sync_logs" # Should be new
    ]
    
    # Based on my recent edit to database.py, reconciliation_items DOES have sync columns.
    tables_to_migrate.append("reconciliation_items")

    columns_to_add = [
        ("sync_id", "TEXT UNIQUE"),
        ("sync_status", "TEXT DEFAULT 'pending' NOT NULL"),
        ("last_synced_at", "DATETIME"),
        ("is_deleted", "BOOLEAN DEFAULT 0 NOT NULL")
    ]

    for table in tables_to_migrate:
        print(f"Checking table: {table}")
        try:
            # Check if table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                print(f"  Table {table} does not exist. Skipping (will be created by init_db).")
                continue

            # Get existing columns
            cursor.execute(f"PRAGMA table_info({table})")
            existing_columns = [row[1] for row in cursor.fetchall()]

            for col_name, col_def in columns_to_add:
                if col_name not in existing_columns:
                    print(f"  Adding column {col_name} to {table}...")
                    try:
                        # SQLite ALTER TABLE ADD COLUMN is limited, but works for these types usually.
                        # Note: UNIQUE constraint might be tricky in ALTER TABLE in older SQLite, 
                        # but let's try. If UNIQUE fails, we might drop it for migration or handle it separately.
                        # Actually, adding a UNIQUE column with existing data might fail if we don't provide unique values.
                        # For sync_id, we need to populate it!
                        
                        if col_name == "sync_id":
                             # Add as nullable first, then populate, then maybe add unique index? 
                             # SQLite doesn't support adding constraints easily.
                             # We'll add as TEXT first.
                             cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} TEXT")
                             
                             # Generate UUIDs for existing rows
                             import uuid
                             cursor.execute(f"SELECT id FROM {table}")
                             rows = cursor.fetchall()
                             for row_id in rows:
                                 uid = str(uuid.uuid4())
                                 cursor.execute(f"UPDATE {table} SET {col_name} = ? WHERE id = ?", (uid, row_id[0]))
                             
                             # We can't easily add UNIQUE constraint via ALTER TABLE in SQLite. 
                             # We can create a unique index though.
                             cursor.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{table}_sync_id ON {table}(sync_id)")
                             print(f"    Added and populated sync_id.")

                        else:
                            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")
                            print(f"    Added {col_name}.")
                            
                    except Exception as e:
                        print(f"    Failed to add {col_name}: {e}")
        except Exception as e:
            print(f"  Error checking {table}: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate_db()
