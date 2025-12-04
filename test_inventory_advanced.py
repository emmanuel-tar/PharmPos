#!/usr/bin/env python3
"""
Test script for advanced inventory operations:
- Stock allocation (FEFO)
- Stock reservations
- Stock adjustments
- Write-offs
- Transfers
- Reconciliation
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
import os

from desktop_app.database import init_db, get_engine, dispose_engine
from desktop_app.models import (
    StoreService,
    UserService,
    ProductService,
    InventoryService,
    get_session,
)
from desktop_app.auth import PasswordManager

TEST_DB = "pharmapos_test_advanced_inv.db"


def setup_test_data():
    """Initialize test DB with demo store, user, and products."""
    print("  [Setup] Initializing test database...")
    init_db(TEST_DB)
    print(f"    ✓ DB initialized at: {TEST_DB}")

    session = get_session(TEST_DB)
    store_service = StoreService(session)
    user_service = UserService(session)
    product_service = ProductService(session)

    # Get primary store
    stores = store_service.get_all_stores()
    store_id = stores[0]["id"] if stores else None
    print(f"    ✓ Using store ID: {store_id}")

    # Get or create demo user for audit
    users = user_service.get_all_users()
    user_id = users[0]["id"] if users else None
    print(f"    ✓ Using user ID: {user_id}")

    # Create test products
    test_products = [
        {
            "name": "Paracetamol 500mg",
            "sku": "PAR-500-ADV",
            "cost_price": Decimal("50"),
            "selling_price": Decimal("100"),
            "nafdac_number": "NAFDAC/001",
            "generic_name": "Acetaminophen",
            "barcode": "1111111111",
        },
        {
            "name": "Amoxicillin 250mg",
            "sku": "AMX-250-ADV",
            "cost_price": Decimal("150"),
            "selling_price": Decimal("300"),
            "nafdac_number": "NAFDAC/002",
            "generic_name": "Amoxicillin",
            "barcode": "2222222222",
        },
        {
            "name": "Ibuprofen 400mg",
            "sku": "IBU-400-ADV",
            "cost_price": Decimal("75"),
            "selling_price": Decimal("150"),
            "nafdac_number": "NAFDAC/003",
            "generic_name": "Ibuprofen",
            "barcode": "3333333333",
        },
    ]

    product_ids = {}
    for prod_data in test_products:
        # Skip if exists
        existing = product_service.get_product_by_sku(prod_data["sku"])
        if existing:
            product_ids[prod_data["sku"]] = existing["id"]
            print(f"    ✓ Reusing product: {prod_data['name']} (ID: {existing['id']})")
        else:
            prod = product_service.create_product(**prod_data)
            product_ids[prod_data["sku"]] = prod["id"]
            print(f"    ✓ Created product: {prod_data['name']} (ID: {prod['id']})")

    session.close()
    return store_id, user_id, product_ids


def test_allocate_stock_for_sale():
    """Test FEFO allocation."""
    print("\n" + "=" * 60)
    print("TEST: Allocate Stock for Sale (FEFO)")
    print("=" * 60)

    session = get_session(TEST_DB)
    inv_service = InventoryService(session)
    store_id, user_id, product_ids = 1, 1, {}

    # Create test batches with different expiry dates
    sku = "PAR-500-ADV"
    product_id = list(product_ids.values())[0] if product_ids else 1

    # Batch 1: Expires in 5 days
    exp_date_1 = date.today() + timedelta(days=5)
    batch1 = inv_service.receive_stock(
        product_id=product_id,
        store_id=store_id,
        batch_number="BATCH-001",
        quantity=50,
        expiry_date=exp_date_1,
        cost_price=Decimal("50"),
    )
    print(f"  ✓ Created batch 1 (ID: {batch1['id']}, Exp: {exp_date_1}, Qty: 50)")

    # Batch 2: Expires in 10 days
    exp_date_2 = date.today() + timedelta(days=10)
    batch2 = inv_service.receive_stock(
        product_id=product_id,
        store_id=store_id,
        batch_number="BATCH-002",
        quantity=30,
        expiry_date=exp_date_2,
        cost_price=Decimal("50"),
    )
    print(f"  ✓ Created batch 2 (ID: {batch2['id']}, Exp: {exp_date_2}, Qty: 30)")

    # Allocate 60 units (should pick batch 1 first, then batch 2 - FEFO)
    allocations = inv_service.allocate_stock_for_sale(
        product_id=product_id, store_id=store_id, quantity=60
    )
    print(f"\n  FEFO Allocation for 60 units:")
    total_allocated = 0
    for alloc in allocations:
        print(f"    - Batch ID {alloc['batch_id']}: {alloc['quantity']} units")
        total_allocated += alloc["quantity"]

    if total_allocated == 60 and allocations[0]["batch_id"] == batch1["id"]:
        print(f"  ✓ FEFO allocation correct: batch 1 allocated first (sooner expiry)")
    else:
        print(f"  ✗ FEFO allocation failed: expected 60 units with batch 1 first, got {total_allocated}")

    session.close()


def test_reserve_and_release():
    """Test stock reservations."""
    print("\n" + "=" * 60)
    print("TEST: Stock Reservations")
    print("=" * 60)

    session = get_session(TEST_DB)
    inv_service = InventoryService(session)
    store_id, user_id, product_ids = 1, 1, {}
    product_id = list(product_ids.values())[1] if len(product_ids) > 1 else 2

    # Receive stock for reservation test
    batch = inv_service.receive_stock(
        product_id=product_id,
        store_id=store_id,
        batch_number="BATCH-RES-001",
        quantity=100,
        expiry_date=date.today() + timedelta(days=30),
        cost_price=Decimal("150"),
    )
    print(f"  ✓ Created batch for reservation test (ID: {batch['id']}, Qty: 100)")

    # Reserve 25 units
    res = inv_service.reserve_stock(
        product_batch_id=batch["id"],
        quantity=25,
        reason="pending_sale",
        user_id=user_id,
    )
    if res:
        res_id = res["reservation_id"]
        print(f"  ✓ Reserved 25 units (Reservation ID: {res_id})")

        # Release reservation
        released = inv_service.release_reservation(reservation_id=res_id, user_id=user_id)
        if released:
            print(f"  ✓ Released reservation successfully")
        else:
            print(f"  ✗ Failed to release reservation")
    else:
        print(f"  ✗ Failed to reserve stock")

    session.close()


def test_adjust_and_writeoff():
    """Test stock adjustments and write-offs."""
    print("\n" + "=" * 60)
    print("TEST: Stock Adjustments and Write-offs")
    print("=" * 60)

    session = get_session(TEST_DB)
    inv_service = InventoryService(session)
    store_id, user_id, product_ids = 1, 1, {}
    product_id = list(product_ids.values())[2] if len(product_ids) > 2 else 3

    # Receive stock
    batch = inv_service.receive_stock(
        product_id=product_id,
        store_id=store_id,
        batch_number="BATCH-ADJ-001",
        quantity=50,
        expiry_date=date.today() + timedelta(days=20),
        cost_price=Decimal("75"),
    )
    print(f"  ✓ Created batch (ID: {batch['id']}, Qty: 50)")

    # Adjust inventory (e.g., physical count discrepancy)
    adjusted = inv_service.adjust_stock(
        batch_id=batch["id"],
        quantity_change=-5,
        user_id=user_id,
        reason="Physical count discrepancy",
    )
    if adjusted:
        print(f"  ✓ Adjusted batch by -5 units (Physical count)")
    else:
        print(f"  ✗ Failed to adjust stock")

    # Write-off remaining
    writeoff = inv_service.writeoff_batch(
        batch_id=batch["id"],
        quantity=45,
        user_id=user_id,
        reason="Damaged - write-off",
    )
    if writeoff:
        print(f"  ✓ Write-off 45 units successfully")
    else:
        print(f"  ✗ Failed to write-off batch")

    session.close()


def test_transfer():
    """Test stock transfer between stores."""
    print("\n" + "=" * 60)
    print("TEST: Stock Transfer Between Stores")
    print("=" * 60)

    session = get_session(TEST_DB)
    store_service = StoreService(session)
    inv_service = InventoryService(session)
    user_id = 1
    product_ids = {}
    product_id = list(product_ids.values())[0] if product_ids else 1

    # Get or create stores
    stores = store_service.get_all_stores()
    store_1_id = stores[0]["id"] if stores else None
    store_2_id = stores[1]["id"] if len(stores) > 1 else None

    if not store_2_id:
        # Create second store for transfer test
        store_2 = store_service.create_store("Branch Store", "Ibadan")
        store_2_id = store_2["id"]
        print(f"  ✓ Created second store (ID: {store_2_id})")
    else:
        print(f"  ✓ Using existing stores (1: {store_1_id}, 2: {store_2_id})")

    # Receive stock in store 1
    batch = inv_service.receive_stock(
        product_id=product_id,
        store_id=store_1_id,
        batch_number="BATCH-TRANS-001",
        quantity=30,
        expiry_date=date.today() + timedelta(days=25),
        cost_price=Decimal("50"),
    )
    print(f"  ✓ Received batch in store 1 (ID: {batch['id']}, Qty: 30)")

    # Transfer 10 units to store 2
    transfer_id = inv_service.transfer_stock_batch(
        batch_id=batch["id"],
        quantity=10,
        from_store_id=store_1_id,
        to_store_id=store_2_id,
        user_id=user_id,
    )
    if transfer_id:
        print(f"  ✓ Transferred 10 units from store 1 to store 2 (Transfer ID: {transfer_id})")
    else:
        print(f"  ✗ Failed to transfer stock")

    session.close()


def test_reconciliation():
    """Test inventory reconciliation."""
    print("\n" + "=" * 60)
    print("TEST: Inventory Reconciliation")
    print("=" * 60)

    session = get_session(TEST_DB)
    inv_service = InventoryService(session)
    user_id = 1
    store_id = 1
    product_ids = {}
    product_id = list(product_ids.values())[0] if product_ids else 1

    # Receive some stock
    batch = inv_service.receive_stock(
        product_id=product_id,
        store_id=store_id,
        batch_number="BATCH-RECON-001",
        quantity=100,
        expiry_date=date.today() + timedelta(days=30),
        cost_price=Decimal("50"),
    )
    print(f"  ✓ Created batch with 100 units (Batch ID: {batch['id']})")

    # Simulate physical count: counted 95 units (5 units missing)
    physical_counts = [{"product_id": product_id, "counted_qty": 95}]

    report = inv_service.reconcile_inventory(
        store_id=store_id, physical_counts=physical_counts, user_id=user_id
    )

    print(f"\n  Reconciliation Report:")
    print(f"    - Store: {report.get('store_id')}")
    print(f"    - Discrepancies found: {len(report.get('discrepancies', []))}")
    for disc in report.get("discrepancies", []):
        print(f"      • Product {disc['product_id']}: {disc['system_qty']} (system) vs {disc['counted_qty']} (counted) → Diff: {disc['difference']}")

    session.close()


def cleanup():
    """Clean up test database."""
    print("\n" + "=" * 60)
    print("Cleanup")
    print("=" * 60)
    try:
        dispose_engine(TEST_DB)
        os.remove(TEST_DB)
        print(f"  ✓ Removed: {TEST_DB}")
    except Exception as e:
        print(f"  ✗ Failed to remove {TEST_DB}: {e}")


def main():
    """Run all advanced inventory tests."""
    print("\n")
    print("+" + "=" * 58 + "+")
    print("| ADVANCED INVENTORY TEST SUITE                         |")
    print("+" + "=" * 58 + "+")
    print("\n")

    try:
        setup_test_data()
        test_allocate_stock_for_sale()
        test_reserve_and_release()
        test_adjust_and_writeoff()
        test_transfer()
        test_reconciliation()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS COMPLETED")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        cleanup()


if __name__ == "__main__":
    main()
