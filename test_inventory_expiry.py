"""
Simple test script to verify expiry behavior in InventoryService.
Run with: python test_inventory_expiry.py
"""
from datetime import date, timedelta
from decimal import Decimal
import os
import sys

project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from desktop_app.database import init_db
from desktop_app.models import get_session, StoreService, ProductService, InventoryService
from sqlalchemy import text

DB_PATH = "pharmapos_test.db"

# Cleanup previous test db
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

# Initialize fresh DB
init_db(DB_PATH)

session = get_session(DB_PATH)
store_svc = StoreService(session)
prod_svc = ProductService(session)
inv_svc = InventoryService(session)

# Create or reuse primary store
from sqlalchemy import text
existing = session.execute(text("SELECT id FROM stores WHERE is_primary = 1")).fetchone()
if existing:
    store_id = existing[0]
    print(f"Reusing existing primary store (id={store_id})")
else:
    store = store_svc.create_store("Test Store", "Test Address", is_primary=True)
    store_id = store["id"]

# Create product
prod = prod_svc.create_product(
    name="TestMed",
    sku="TM001",
    cost_price=Decimal("10.00"),
    selling_price=Decimal("15.00"),
    nafdac_number="NAF-TEST-001",
)
prod_id = prod["id"]

# Create three batches: expired, near-expiry, far-expiry
today = date.today()
expired_date = today - timedelta(days=5)
near_date = today + timedelta(days=5)
far_date = today + timedelta(days=60)

b1 = inv_svc.receive_stock(prod_id, store_id, "BATCH-EXP", 10, expired_date, Decimal("9.00"))
b2 = inv_svc.receive_stock(prod_id, store_id, "BATCH-NEAR", 20, near_date, Decimal("9.50"))
b3 = inv_svc.receive_stock(prod_id, store_id, "BATCH-FAR", 30, far_date, Decimal("9.75"))

print("Batches created:")
print(b1)
print(b2)
print(b3)

# Determine a valid user_id for audit entries
user_row = session.execute(text("SELECT id FROM users WHERE is_active = 1 LIMIT 1")).fetchone()
if user_row:
    test_user_id = user_row[0]
else:
    # Create a quick test user
    session.execute(text("INSERT INTO users (username, password_hash, role, is_active) VALUES ('testuser', 'x', 'admin', 1)"))
    session.commit()
    test_user_id = session.execute(text("SELECT id FROM users WHERE username = 'testuser' LIMIT 1")).scalar()

# Run expire_batches_within_days for next 10 days (should expire BATCH-NEAR and BATCH-EXP)
expired_count = inv_svc.expire_batches_within_days(store_id, 10, user_id=test_user_id)
print(f"Expired count (within 10 days): {expired_count}")

# Verify quantities
rows = session.execute(text("SELECT batch_number, quantity FROM product_batches WHERE store_id = :s"), {"s": store_id}).fetchall()
print("Post-expiry batch quantities:")
for r in rows:
    print(r[0], r[1])

# Check audit entries
audit_rows = session.execute(text("SELECT change_type, COUNT(*) FROM inventory_audit GROUP BY change_type")).fetchall()
print("Inventory audit summary:")
for r in audit_rows:
    print(r[0], r[1])

# Clean up DB session
session.close()

# Basic assertions (exit non-zero on failure)
expected_expired = 2
if expired_count != expected_expired:
    print(f"Test failed: expected {expected_expired} expired, got {expired_count}")
    sys.exit(2)

print("Expiry test passed.")
sys.exit(0)
