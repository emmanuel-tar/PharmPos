"""
Script to dump the actual database schema for documentation.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("pharmapos.db")

def dump_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("=" * 80)
    print("ACTUAL DATABASE SCHEMA")
    print("=" * 80)
    
    for table in tables:
        print(f"\n### Table: {table}")
        print("-" * 80)
        
        # Get columns
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        print("Columns:")
        for col in columns:
            col_id, name, type_, notnull, default, pk = col
            nullable = "NOT NULL" if notnull else "NULL"
            pk_str = "PRIMARY KEY" if pk else ""
            default_str = f"DEFAULT {default}" if default else ""
            print(f"  - {name}: {type_} {nullable} {pk_str} {default_str}".strip())
        
        # Get foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        fks = cursor.fetchall()
        if fks:
            print("\nForeign Keys:")
            for fk in fks:
                id_, seq, table_ref, from_col, to_col, on_update, on_delete, match = fk
                print(f"  - {from_col} -> {table_ref}({to_col})")
    
    print("\n" + "=" * 80)
    conn.close()

if __name__ == "__main__":
    dump_schema()
