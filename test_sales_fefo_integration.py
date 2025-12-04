"""
Test: Sales Integration with FEFO Allocation
Tests the complete sales flow including:
- Creating batches with different expiry dates
- Using SalesService to create a sale
- Verifying FEFO allocation is applied correctly
- Checking inventory deduction after sale
"""

import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from desktop_app.database import metadata, product_batches, inventory_audit, init_db
from desktop_app.models import (
    ProductService,
    StoreService,
    InventoryService,
    SalesService,
)


def test_sales_with_fefo():
    """Test sales creation with FEFO allocation."""
    
    # Setup
    db_path = "sqlite:///test_sales_fefo_integration.db"
    engine = create_engine(db_path, echo=False)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    
    session = Session(engine)
    
    print("=" * 70)
    print("SALES INTEGRATION WITH FEFO ALLOCATION TEST")
    print("=" * 70)
    
    try:
        # --- Setup: Create store ---
        print("\n[Setup] Creating test store...")
        store_service = StoreService(session)
        store = store_service.create_store(
            name="PharmaPOS Store",
            address="Lagos",
            is_primary=True,
        )
        print(f"  ✓ Store created: {store['name']} (ID: {store['id']})")
        
        # --- Setup: Create product ---
        print("\n[Setup] Creating test product...")
        product_service = ProductService(session)
        product = product_service.create_product(
            name="Paracetamol 500mg",
            sku="PARA-500",
            cost_price=Decimal("100"),
            selling_price=Decimal("200"),
            nafdac_number="NAFDAC/2020/123",
            generic_name="Paracetamol",
            barcode="4902011234567",
            description="Pain reliever and fever reducer"
        )
        print(f"  ✓ Product created: {product['name']} (ID: {product['id']})")
        
        # --- Setup: Create batches with different expiry dates ---
        print("\n[Receiving] Adding stock batches with different expiry dates...")
        inv_service = InventoryService(session)
        
        today = date.today()
        batch1_data = {
            "product_id": product["id"],
            "store_id": store["id"],
            "batch_number": "LOT-EXP-001",
            "quantity": 100,
            "expiry_date": today + timedelta(days=30),  # Expires in 30 days (FIRST)
            "cost_price": Decimal("100"),
        }
        batch1 = inv_service.receive_stock(**batch1_data)
        print(f"  ✓ Batch 1 (expires {batch1_data['expiry_date']}): 100 units")
        
        batch2_data = {
            "product_id": product["id"],
            "store_id": store["id"],
            "batch_number": "LOT-EXP-002",
            "quantity": 50,
            "expiry_date": today + timedelta(days=180),  # Expires in 180 days (SECOND)
            "cost_price": Decimal("100"),
        }
        batch2 = inv_service.receive_stock(**batch2_data)
        print(f"  ✓ Batch 2 (expires {batch2_data['expiry_date']}): 50 units")
        
        batch3_data = {
            "product_id": product["id"],
            "store_id": store["id"],
            "batch_number": "LOT-EXP-003",
            "quantity": 75,
            "expiry_date": today + timedelta(days=365),  # Expires in 365 days (THIRD)
            "cost_price": Decimal("100"),
        }
        batch3 = inv_service.receive_stock(**batch3_data)
        print(f"  ✓ Batch 3 (expires {batch3_data['expiry_date']}): 75 units")
        
        print(f"\n  Total stock received: 225 units (100 + 50 + 75)")
        
        # --- Test 1: Allocate 60 units (should come from batch 1 only) ---
        print("\n[FEFO Test 1] Allocating 60 units for sale...")
        allocation = inv_service.allocate_stock_for_sale(
            product_id=product["id"],
            store_id=store["id"],
            quantity=60,
        )
        
        print(f"  Allocation result:")
        for batch_alloc in allocation:
            print(f"    - Batch {batch_alloc['batch_id']}: {batch_alloc['quantity']} units")
        
        assert len(allocation) == 1, "Expected single batch allocation"
        assert allocation[0]["batch_id"] == batch1["id"], "Expected batch 1 (earliest expiry)"
        assert allocation[0]["quantity"] == 60, "Expected 60 units from batch 1"
        print(f"  ✓ FEFO correctly selected batch 1 (expires first)")
        
        # --- Test 2: Create sale with 60 units ---
        print("\n[Sale] Creating sales transaction...")
        sales_service = SalesService(session)
        
        sale_items = [
            {
                "batch_id": allocation[0]["batch_id"],
                "quantity": allocation[0]["quantity"],
                "unit_price": Decimal("200"),
            }
        ]
        
        sale = sales_service.create_sale(
            user_id=1,
            store_id=store["id"],
            items=sale_items,
            payment_method="cash",
            amount_paid=Decimal("12000"),  # 60 * 200
        )
        
        print(f"  ✓ Sale created: Receipt #{sale['receipt_number']}")
        print(f"    - Total: ₦{sale['total_amount']:.2f}")
        print(f"    - Amount Paid: ₦{sale['amount_paid']:.2f}")
        print(f"    - Change: ₦{sale['change_amount']:.2f}")
        
        # --- Test 3: Verify inventory deduction ---
        print("\n[Inventory] Verifying stock levels after sale...")
        remaining_inventory = inv_service.get_store_inventory(store["id"])
        
        print(f"  Remaining batches:")
        for batch_info in remaining_inventory:
            days_to_expiry = (batch_info['expiry_date'] - today).days
            print(f"    - Batch {batch_info['id']} ({batch_info['batch_number']}): "
                  f"{batch_info['quantity']} units "
                  f"(expires in {days_to_expiry} days)")
        
        # Batch 1 should have 40 remaining (100 - 60)
        batch1_remaining = next((b for b in remaining_inventory if b['id'] == batch1['id']), None)
        assert batch1_remaining is not None, "Batch 1 should still exist"
        assert batch1_remaining['quantity'] == 40, f"Batch 1 should have 40 units, got {batch1_remaining['quantity']}"
        print(f"  ✓ Batch 1 reduced from 100 to 40 units")
        
        # Batch 2 and 3 should be unchanged
        batch2_remaining = next((b for b in remaining_inventory if b['id'] == batch2['id']), None)
        batch3_remaining = next((b for b in remaining_inventory if b['id'] == batch3['id']), None)
        
        assert batch2_remaining['quantity'] == 50, "Batch 2 should still have 50 units"
        assert batch3_remaining['quantity'] == 75, "Batch 3 should still have 75 units"
        print(f"  ✓ Batch 2 unchanged: 50 units")
        print(f"  ✓ Batch 3 unchanged: 75 units")
        
        # --- Test 4: Allocate remaining batch 1 + start of batch 2 ---
        print("\n[FEFO Test 2] Allocating 60 more units (should use batch 1 + batch 2)...")
        allocation2 = inv_service.allocate_stock_for_sale(
            product_id=product["id"],
            store_id=store["id"],
            quantity=60,
        )
        
        print(f"  Allocation result:")
        total_allocated = 0
        for batch_alloc in allocation2:
            print(f"    - Batch {batch_alloc['batch_id']}: {batch_alloc['quantity']} units")
            total_allocated += batch_alloc['quantity']
        
        assert total_allocated == 60, f"Expected 60 units total, got {total_allocated}"
        
        # Should be batch 1 (40 units remaining) + batch 2 (20 units)
        assert len(allocation2) == 2, "Expected 2 batches in allocation"
        assert allocation2[0]["batch_id"] == batch1["id"], "First should be batch 1 (earliest expiry)"
        assert allocation2[0]["quantity"] == 40, "Batch 1 should contribute 40 units"
        assert allocation2[1]["batch_id"] == batch2["id"], "Second should be batch 2"
        assert allocation2[1]["quantity"] == 20, "Batch 2 should contribute 20 units"
        print(f"  ✓ FEFO correctly split allocation: 40 from batch 1 + 20 from batch 2")
        
        session.close()
        engine.dispose()  # Close all connections
        
        # --- Summary ---
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        print("\nSummary:")
        print("  ✓ Batches created with different expiry dates")
        print("  ✓ FEFO allocation correctly prioritizes batches by expiry date")
        print("  ✓ Sales integration creates transactions and deducts inventory")
        print("  ✓ Multiple batch allocation works correctly")
        print("  ✓ Inventory levels updated accurately after sales")
        
        # Cleanup
        import os
        import time
        time.sleep(0.5)  # Wait for connections to close
        if os.path.exists("test_sales_fefo_integration.db"):
            try:
                os.remove("test_sales_fefo_integration.db")
                print("\n✓ Cleaned up: test_sales_fefo_integration.db")
            except Exception:
                pass  # File still in use, skip cleanup
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        session.close()
        engine.dispose()
        import os
        import time
        time.sleep(0.5)
        if os.path.exists("test_sales_fefo_integration.db"):
            try:
                os.remove("test_sales_fefo_integration.db")
            except Exception:
                pass
        sys.exit(1)
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        session.close()
        engine.dispose()
        import os
        import time
        time.sleep(0.5)
        if os.path.exists("test_sales_fefo_integration.db"):
            try:
                os.remove("test_sales_fefo_integration.db")
            except Exception:
                pass
        sys.exit(1)


if __name__ == "__main__":
    test_sales_with_fefo()
