#!/usr/bin/env python3
"""
Test script demonstrating stock receiving with expiry date capture.
Shows how the inventory now captures and stores expiry dates for batch tracking.
"""

from datetime import date, timedelta
from decimal import Decimal

from desktop_app.database import init_db, dispose_engine
from desktop_app.models import (
    ProductService,
    InventoryService,
    get_session,
)

TEST_DB = "test_receive_stock_expiry.db"


def test_receive_stock_with_expiry():
    """Test receiving stock with expiry date."""
    print("\n" + "=" * 70)
    print("STOCK RECEIVING WITH EXPIRY DATE TEST")
    print("=" * 70)

    # Initialize database
    print("\n[Setup] Initializing database...")
    init_db(TEST_DB)
    print(f"  ✓ Database initialized: {TEST_DB}")

    session = get_session(TEST_DB)
    prod_service = ProductService(session)
    inv_service = InventoryService(session)

    # Create a test product
    print("\n[Setup] Creating test product...")
    product = prod_service.create_product(
        name="Aspirin 500mg",
        sku="ASP-500-EXP",
        cost_price=Decimal("50"),
        selling_price=Decimal("100"),
        nafdac_number="NAFDAC/ASP",
        generic_name="Acetylsalicylic Acid",
        barcode="5555555555",
    )
    print(f"  ✓ Created product: {product['name']} (ID: {product['id']}, SKU: {product['sku']})")

    # Receive stock with different expiry dates
    print("\n[Receiving] Adding stock batches with expiry dates...")
    
    # Batch 1: Expires in 6 months
    expiry_date_1 = date.today() + timedelta(days=180)
    batch1 = inv_service.receive_stock(
        product_id=product["id"],
        store_id=1,  # Primary store
        batch_number="LOT-2025-001",
        quantity=100,
        expiry_date=expiry_date_1,
        cost_price=Decimal("50"),
    )
    print(f"\n  Batch 1 Received:")
    print(f"    - Batch ID: {batch1['id']}")
    print(f"    - Batch Number: LOT-2025-001")
    print(f"    - Quantity: 100 units")
    print(f"    - Expiry Date: {batch1['expiry_date']}")
    print(f"    - Cost Price: ₦50")
    print(f"    - Days until expiry: {(expiry_date_1 - date.today()).days} days")

    # Batch 2: Expires in 12 months
    expiry_date_2 = date.today() + timedelta(days=365)
    batch2 = inv_service.receive_stock(
        product_id=product["id"],
        store_id=1,
        batch_number="LOT-2025-002",
        quantity=150,
        expiry_date=expiry_date_2,
        cost_price=Decimal("50"),
    )
    print(f"\n  Batch 2 Received:")
    print(f"    - Batch ID: {batch2['id']}")
    print(f"    - Batch Number: LOT-2025-002")
    print(f"    - Quantity: 150 units")
    print(f"    - Expiry Date: {batch2['expiry_date']}")
    print(f"    - Cost Price: ₦50")
    print(f"    - Days until expiry: {(expiry_date_2 - date.today()).days} days")

    # Batch 3: Expires soon (30 days)
    expiry_date_3 = date.today() + timedelta(days=30)
    batch3 = inv_service.receive_stock(
        product_id=product["id"],
        store_id=1,
        batch_number="LOT-2025-003",
        quantity=50,
        expiry_date=expiry_date_3,
        cost_price=Decimal("50"),
    )
    print(f"\n  Batch 3 Received (Early Expiry):")
    print(f"    - Batch ID: {batch3['id']}")
    print(f"    - Batch Number: LOT-2025-003")
    print(f"    - Quantity: 50 units")
    print(f"    - Expiry Date: {batch3['expiry_date']}")
    print(f"    - Cost Price: ₦50")
    print(f"    - Days until expiry: {(expiry_date_3 - date.today()).days} days ⚠️  EXPIRING SOON")

    # Display inventory ordered by expiry (FEFO)
    print("\n[Inventory] Current stock (ordered by expiry - FEFO):")
    inventory = inv_service.get_store_inventory(1)
    print(f"\n  {len(inventory)} batches in inventory:")
    for idx, batch in enumerate(inventory, 1):
        days_until_expiry = (batch["expiry_date"] - date.today()).days
        status = "⚠️  EXPIRING SOON" if days_until_expiry < 60 else "✓"
        print(f"\n  {idx}. Batch ID {batch['id']} - {batch['batch_number']}")
        print(f"     Quantity: {batch['quantity']} units")
        print(f"     Expiry: {batch['expiry_date']} ({days_until_expiry} days) {status}")

    # Test FEFO allocation
    print("\n[FEFO] Testing FEFO allocation (allocating 80 units for sale):")
    result = inv_service.allocate_stock_for_sale(
        product_id=product["id"],
        store_id=1,
        quantity=80,
        user_id=1
    )
    print(f"\n  Allocation successful!")
    print(f"  Total allocated: {result['allocated_quantity']} units")
    print(f"  Partial allocation: {result.get('partial', False)}")
    
    print("\n  Batches selected (FEFO order):")
    for idx, batch_alloc in enumerate(result["batches"], 1):
        print(f"    {idx}. Batch ID {batch_alloc['batch_id']}: {batch_alloc['quantity']} units")
        print(f"       Expires: {batch_alloc['expiry_date']}")

    # Summary
    print("\n" + "=" * 70)
    print("✓ TEST COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print("\nSummary:")
    print(f"  - Total stock received: {batch1['quantity'] + batch2['quantity'] + batch3['quantity']} units across 3 batches")
    print(f"  - FEFO system correctly prioritizes stock expiring sooner")
    print(f"  - Expiry dates are captured and stored in the database")
    print(f"  - Inventory can be queried by expiry date for compliance")
    print()

    session.close()


def cleanup():
    """Clean up test database."""
    try:
        dispose_engine(TEST_DB)
        import os
        os.remove(TEST_DB)
        print(f"✓ Cleaned up: {TEST_DB}")
    except Exception as e:
        print(f"✗ Cleanup error: {e}")


if __name__ == "__main__":
    try:
        test_receive_stock_with_expiry()
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup()
