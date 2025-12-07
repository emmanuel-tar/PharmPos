"""
Database Verification Script for PharmaPOS

This script performs comprehensive verification of the database schema,
checking for table existence, column presence, and data integrity.
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from desktop_app.config import DATABASE_PATH


class DatabaseVerifier:
    """Comprehensive database verification utility."""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.errors = []
        self.warnings = []
        self.success_count = 0
        
    def connect(self):
        """Connect to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            print(f"[OK] Connected to database: {self.db_path}")
            self.success_count += 1
            return True
        except Exception as e:
            self.errors.append(f"Failed to connect to database: {e}")
            return False
    
    def verify_table_exists(self, table_name):
        """Check if a table exists."""
        try:
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            result = self.cursor.fetchone()
            if result:
                print(f"  [OK] Table '{table_name}' exists")
                self.success_count += 1
                return True
            else:
                self.errors.append(f"Table '{table_name}' does not exist")
                return False
        except Exception as e:
            self.errors.append(f"Error checking table '{table_name}': {e}")
            return False
    
    def verify_columns(self, table_name, expected_columns):
        """Verify that a table has all expected columns."""
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            actual_columns = {row[1] for row in self.cursor.fetchall()}
            
            missing = set(expected_columns) - actual_columns
            extra = actual_columns - set(expected_columns)
            
            if missing:
                self.errors.append(f"Table '{table_name}' missing columns: {missing}")
            
            if extra:
                self.warnings.append(f"Table '{table_name}' has extra columns: {extra}")
            
            if not missing:
                print(f"  [OK] All expected columns present in '{table_name}'")
                self.success_count += 1
                return True
            return False
        except Exception as e:
            self.errors.append(f"Error verifying columns for '{table_name}': {e}")
            return False
    
    def verify_sync_columns(self, table_name):
        """Verify that sync columns exist and have correct types."""
        sync_columns = ['sync_id', 'sync_status', 'last_synced_at', 'is_deleted']
        return self.verify_columns(table_name, sync_columns)
    
    def test_crud_operations(self):
        """Test basic CRUD operations on stores table."""
        print("\n--- Testing CRUD Operations ---")
        try:
            # Create
            test_store_name = f"Test Store {datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.cursor.execute("""
                INSERT INTO stores (name, address, phone, email, is_primary, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (test_store_name, "Test Address", "1234567890", "test@test.com", 0, 1))
            store_id = self.cursor.lastrowid
            print(f"  [OK] CREATE: Inserted test store with ID {store_id}")
            self.success_count += 1
            
            # Read
            self.cursor.execute("SELECT * FROM stores WHERE id = ?", (store_id,))
            store = self.cursor.fetchone()
            if store:
                print(f"  [OK] READ: Retrieved store '{store[1]}'")
                self.success_count += 1
            else:
                self.errors.append("Failed to read inserted store")
            
            # Update
            self.cursor.execute("""
                UPDATE stores SET address = ? WHERE id = ?
            """, ("Updated Address", store_id))
            self.cursor.execute("SELECT address FROM stores WHERE id = ?", (store_id,))
            updated_address = self.cursor.fetchone()[0]
            if updated_address == "Updated Address":
                print(f"  [OK] UPDATE: Updated store address")
                self.success_count += 1
            else:
                self.errors.append("Failed to update store")
            
            # Delete
            self.cursor.execute("DELETE FROM stores WHERE id = ?", (store_id,))
            self.cursor.execute("SELECT * FROM stores WHERE id = ?", (store_id,))
            if not self.cursor.fetchone():
                print(f"  [OK] DELETE: Deleted test store")
                self.success_count += 1
            else:
                self.errors.append("Failed to delete store")
            
            # Rollback to not affect actual data
            self.conn.rollback()
            print("  [OK] Rolled back test changes")
            self.success_count += 1
            
            return True
        except Exception as e:
            self.errors.append(f"CRUD test failed: {e}")
            self.conn.rollback()
            return False
    
    def verify_foreign_keys(self):
        """Verify foreign key relationships."""
        print("\n--- Verifying Foreign Key Relationships ---")
        try:
            # Check if foreign keys are enabled
            self.cursor.execute("PRAGMA foreign_keys")
            fk_status = self.cursor.fetchone()[0]
            if fk_status:
                print("  [OK] Foreign keys are enabled")
                self.success_count += 1
            else:
                self.warnings.append("Foreign keys are not enabled")
            
            # List all foreign keys
            tables = ['users', 'products', 'product_batches', 'sales', 'sale_items', 
                     'stock_transfers', 'reservations', 'backorders', 
                     'inventory_reconciliations', 'reconciliation_items']
            
            for table in tables:
                self.cursor.execute(f"PRAGMA foreign_key_list({table})")
                fks = self.cursor.fetchall()
                if fks:
                    print(f"  [OK] Table '{table}' has {len(fks)} foreign key(s)")
                    self.success_count += 1
            
            return True
        except Exception as e:
            self.errors.append(f"Foreign key verification failed: {e}")
            return False
    
    def run_full_verification(self):
        """Run complete database verification."""
        print("=" * 60)
        print("PharmaPOS Database Verification")
        print("=" * 60)
        print(f"Database: {self.db_path}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        if not self.connect():
            return False
        
        # Define expected schema
        tables_schema = {
            'stores': ['id', 'name', 'address', 'phone', 'email', 'is_primary', 'is_active', 
                      'created_at', 'updated_at', 'sync_id', 'sync_status', 'last_synced_at', 'is_deleted'],
            'users': ['id', 'username', 'password_hash', 'full_name', 'role', 'store_id', 
                     'is_active', 'created_at', 'updated_at', 'sync_id', 'sync_status', 
                     'last_synced_at', 'is_deleted'],
            'products': ['id', 'name', 'sku', 'barcode', 'description', 'category', 'generic_name',
                        'cost_price', 'selling_price', 'retail_price', 'bulk_price', 'bulk_quantity',
                        'wholesale_price', 'wholesale_quantity', 'min_stock', 'max_stock', 
                        'reorder_level', 'nafdac_number', 'is_active', 'created_at', 'updated_at',
                        'sync_id', 'sync_status', 'last_synced_at', 'is_deleted'],
            'product_batches': ['id', 'product_id', 'store_id', 'batch_number', 'quantity',
                               'cost_price', 'expiry_date', 'received_date', 'received_by',
                               'sync_id', 'sync_status', 'last_synced_at', 'is_deleted'],
            'sales': ['id', 'store_id', 'user_id', 'receipt_number', 'customer_name',
                     'subtotal', 'tax', 'discount', 'total', 'payment_method', 'amount_paid',
                     'change_given', 'sale_date', 'sync_id', 'sync_status', 'last_synced_at', 'is_deleted'],
            'sale_items': ['id', 'sale_id', 'product_id', 'batch_id', 'quantity', 'unit_price',
                          'discount_percent', 'line_total', 'sync_id', 'sync_status', 
                          'last_synced_at', 'is_deleted'],
            'stock_transfers': ['id', 'from_store_id', 'to_store_id', 'product_id', 'batch_id',
                               'quantity', 'transfer_date', 'transferred_by', 'status', 'notes',
                               'sync_id', 'sync_status', 'last_synced_at', 'is_deleted'],
            'reservations': ['id', 'store_id', 'product_id', 'batch_id', 'quantity',
                            'customer_name', 'customer_phone', 'reservation_date', 'expiry_date',
                            'status', 'notes', 'sync_id', 'sync_status', 'last_synced_at', 'is_deleted'],
            'backorders': ['id', 'store_id', 'product_id', 'quantity', 'customer_name',
                          'customer_phone', 'order_date', 'expected_date', 'status', 'notes',
                          'sync_id', 'sync_status', 'last_synced_at', 'is_deleted'],
            'inventory_reconciliations': ['id', 'store_id', 'reconciliation_date', 'reconciled_by',
                                         'notes', 'sync_id', 'sync_status', 'last_synced_at', 'is_deleted'],
            'reconciliation_items': ['id', 'reconciliation_id', 'product_id', 'batch_id',
                                    'expected_quantity', 'actual_quantity', 'variance', 'notes',
                                    'sync_id', 'sync_status', 'last_synced_at', 'is_deleted'],
            'sync_logs': ['id', 'sync_date', 'sync_type', 'records_sent', 'records_received',
                         'status', 'error_message'],
        }
        
        print("\n--- Verifying Tables and Columns ---")
        for table_name, expected_columns in tables_schema.items():
            if self.verify_table_exists(table_name):
                self.verify_columns(table_name, expected_columns)
        
        # Test CRUD operations
        self.test_crud_operations()
        
        # Verify foreign keys
        self.verify_foreign_keys()
        
        # Print summary
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"[OK] Successful checks: {self.success_count}")
        print(f"[!] Warnings: {len(self.warnings)}")
        print(f"[X] Errors: {len(self.errors)}")
        
        if self.warnings:
            print("\n[!] WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if self.errors:
            print("\n[X] ERRORS:")
            for error in self.errors:
                print(f"  - {error}")
        
        print("=" * 60)
        
        # Close connection
        if self.conn:
            self.conn.close()
        
        return len(self.errors) == 0


if __name__ == "__main__":
    verifier = DatabaseVerifier(DATABASE_PATH)
    success = verifier.run_full_verification()
    
    if success:
        print("\n[OK] Database verification PASSED!")
        sys.exit(0)
    else:
        print("\n[FAIL] Database verification FAILED!")
        sys.exit(1)
