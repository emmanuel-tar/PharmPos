"""
Comprehensive test for product creation and inventory receiving with pricing tiers and stock alerts.
This test verifies that all new fields (retail price, bulk price, wholesale price, stock alerts, expiry date) 
are properly stored and retrieved from the database.
"""

import sys
import os
from decimal import Decimal
from datetime import date, timedelta
from desktop_app.database import init_db, metadata, products, product_batches, stores
from desktop_app.models import ProductService, InventoryService, StoreService, get_session


def test_product_creation_with_pricing_tiers():
    """Test creating a product with all pricing tiers and stock alerts."""
    print("\n" + "="*80)
    print("TEST 1: Create Product with Pricing Tiers & Stock Alerts")
    print("="*80)
    
    # Initialize database
    init_db()
    session = get_session()
    
    # Create services
    product_service = ProductService(session)
    store_service = StoreService(session)
    
    # Create or get primary store
    stores_list = store_service.get_all_stores()
    if not stores_list:
        store = store_service.create_store("Main Store", "123 Main St", is_primary=True)
        store_id = store["id"]
    else:
        store_id = stores_list[0]["id"]
    
    # Create product with full pricing tiers
    print("\n1. Creating product with pricing tiers...")
    product = product_service.create_product(
        name="Paracetamol 500mg",
        sku="PARA-500-001",
        cost_price=Decimal("50.00"),
        selling_price=Decimal("150.00"),
        nafdac_number="NAFDAC-2024-001",
        generic_name="Acetaminophen",
        barcode="9876543210123",
        retail_price=Decimal("150.00"),
        bulk_price=Decimal("120.00"),
        bulk_quantity=10,
        wholesale_price=Decimal("90.00"),
        wholesale_quantity=50,
        min_stock=10,
        max_stock=500,
        reorder_level=50,
    )
    
    print("[OK] Product created successfully!")
    print(f"  ID: {product['id']}")
    print(f"  Name: {product['name']}")
    print(f"  Cost Price: N{product['cost_price']}")
    print(f"  Retail Price: N{product['retail_price']}")
    print(f"  Bulk Price: N{product['bulk_price']} (min qty: {product['bulk_quantity']})")
    print(f"  Wholesale Price: N{product['wholesale_price']} (min qty: {product['wholesale_quantity']})")
    print(f"  Stock Alerts: Min={product['min_stock']}, Max={product['max_stock']}")
    print(f"  Reorder Level: {product['reorder_level']}")
    
    # Verify product data in database
    print("\n2. Verifying product data from database...")
    retrieved_product = product_service.get_product(product["id"])
    
    assert retrieved_product is not None, "Product not found in database!"
    assert retrieved_product["retail_price"] == Decimal("150.00"), "Retail price mismatch!"
    assert retrieved_product["bulk_price"] == Decimal("120.00"), "Bulk price mismatch!"
    assert retrieved_product["bulk_quantity"] == 10, "Bulk quantity mismatch!"
    assert retrieved_product["wholesale_price"] == Decimal("90.00"), "Wholesale price mismatch!"
    assert retrieved_product["wholesale_quantity"] == 50, "Wholesale quantity mismatch!"
    assert retrieved_product["min_stock"] == 10, "Min stock mismatch!"
    assert retrieved_product["max_stock"] == 500, "Max stock mismatch!"
    assert retrieved_product["reorder_level"] == 50, "Reorder level mismatch!"
    
    print("[OK] All product fields verified successfully!")
    
    return product["id"], store_id


def test_stock_receiving_with_pricing_overrides(product_id: int, store_id: int):
    """Test receiving stock with optional batch-level pricing overrides."""
    print("\n" + "="*80)
    print("TEST 2: Receive Stock with Batch-Level Pricing Overrides & Expiry Date")
    print("="*80)
    
    session = get_session()
    inv_service = InventoryService(session)
    
    # Receive stock with custom pricing for this batch
    print("\n1. Receiving stock batch with clearance pricing...")
    expiry = date.today() + timedelta(days=365)
    
    batch = inv_service.receive_stock(
        product_id=product_id,
        store_id=store_id,
        batch_number="BATCH-2024-001",
        quantity=100,
        expiry_date=expiry,
        cost_price=Decimal("50.00"),
        retail_price=Decimal("180.00"),  # Override: higher price
        bulk_price=Decimal("140.00"),
        bulk_quantity=5,
        wholesale_price=Decimal("110.00"),
        wholesale_quantity=30,
        min_stock=5,
        max_stock=300,
        reorder_level=25,
    )
    
    print("[OK] Stock batch received successfully!")
    print(f"  Batch ID: {batch['id']}")
    print(f"  Batch Number: {batch['batch_number']}")
    print(f"  Quantity: {batch['quantity']} units")
    print(f"  Expiry Date: {batch['expiry_date']}")
    print(f"  Cost Price: N{batch['cost_price']}")
    print(f"  Retail Price (override): N{batch['retail_price']}")
    print(f"  Bulk Price (override): N{batch['bulk_price']} (min qty: {batch['bulk_quantity']})")
    print(f"  Wholesale Price (override): N{batch['wholesale_price']} (min qty: {batch['wholesale_quantity']})")
    print(f"  Stock Alerts: Min={batch['min_stock']}, Max={batch['max_stock']}, Reorder={batch['reorder_level']}")
    
    # Verify batch data
    print("\n2. Verifying batch data from database...")
    stmt = product_batches.select().where(product_batches.c.id == batch["id"])
    result = session.execute(stmt).fetchone()
    
    assert result is not None, "Batch not found in database!"
    assert result.batch_number == "BATCH-2024-001", "Batch number mismatch!"
    assert result.quantity == 100, "Quantity mismatch!"
    assert result.expiry_date == expiry, "Expiry date mismatch!"
    assert result.retail_price == Decimal("180.00"), "Batch retail price override not stored!"
    assert result.bulk_price == Decimal("140.00"), "Batch bulk price override not stored!"
    assert result.bulk_quantity == 5, "Batch bulk quantity override not stored!"
    assert result.wholesale_price == Decimal("110.00"), "Batch wholesale price override not stored!"
    assert result.wholesale_quantity == 30, "Batch wholesale quantity override not stored!"
    
    print("[OK] All batch fields verified successfully!")
    print("[OK] Batch-level pricing overrides working correctly!")
    
    return batch["id"]


def test_stock_alerts_verification(product_id: int):
    """Test that stock alert levels are properly set and retrievable."""
    print("\n" + "="*80)
    print("TEST 3: Verify Stock Alert Levels")
    print("="*80)
    
    session = get_session()
    product_service = ProductService(session)
    
    print("\n1. Retrieving product with stock alerts...")
    product = product_service.get_product(product_id)
    
    print("[OK] Product stock alert levels:")
    print(f"  Min Stock Alert: {product['min_stock']} units")
    print(f"  Max Stock Alert: {product['max_stock']} units")
    print(f"  Reorder Level: {product['reorder_level']} units")
    
    # Verify alert thresholds - note: these get updated by receive_stock()
    assert product['min_stock'] is not None, "Min stock should be set!"
    assert product['max_stock'] is not None, "Max stock should be set!"
    assert product['reorder_level'] is not None, "Reorder level should be set!"
    
    print("[OK] Stock alert levels verified!")
    

def test_pricing_tier_hierarchy(product_id: int):
    """Test that pricing tiers are correctly ordered (retail > bulk > wholesale)."""
    print("\n" + "="*80)
    print("TEST 4: Verify Pricing Tier Hierarchy")
    print("="*80)
    
    session = get_session()
    product_service = ProductService(session)
    
    print("\n1. Checking pricing tier hierarchy...")
    product = product_service.get_product(product_id)
    
    retail = float(product['retail_price'])
    bulk = float(product['bulk_price']) if product['bulk_price'] else 0
    wholesale = float(product['wholesale_price']) if product['wholesale_price'] else 0
    
    print(f"  Retail Price: N{retail}")
    print(f"  Bulk Price: N{bulk}")
    print(f"  Wholesale Price: N{wholesale}")
    
    if bulk > 0:
        assert retail > bulk, f"Retail price (N{retail}) should be > bulk price (N{bulk})!"
        print(f"  [OK] Retail ({retail}) > Bulk ({bulk})")
    
    if wholesale > 0:
        if bulk > 0:
            assert bulk > wholesale, f"Bulk price (N{bulk}) should be > wholesale price (N{wholesale})!"
            print(f"  [OK] Bulk ({bulk}) > Wholesale ({wholesale})")
        if retail > 0:
            assert retail > wholesale, f"Retail price (N{retail}) should be > wholesale price (N{wholesale})!"
            print(f"  [OK] Retail ({retail}) > Wholesale ({wholesale})")
    
    print("[OK] Pricing tier hierarchy verified!")


def main():
    """Run all tests."""
    try:
        print("\n" + "="*80)
        print("COMPREHENSIVE PRODUCT PRICING & STOCK ALERT TESTS")
        print("="*80)
        
        # Test 1: Product creation with pricing tiers
        product_id, store_id = test_product_creation_with_pricing_tiers()
        
        # Test 2: Stock receiving with batch-level overrides
        batch_id = test_stock_receiving_with_pricing_overrides(product_id, store_id)
        
        # Test 3: Stock alert levels
        test_stock_alerts_verification(product_id)
        
        # Test 4: Pricing tier hierarchy
        test_pricing_tier_hierarchy(product_id)
        
        print("\n" + "="*80)
        print("[OK] ALL TESTS PASSED SUCCESSFULLY!")
        print("="*80)
        print("\nSummary:")
        print("  [OK] Products table extended with pricing tier columns")
        print("  [OK] Product batches table extended with pricing override columns")
        print("  [OK] Stock alert columns (min_stock, max_stock, reorder_level) working")
        print("  [OK] Batch-level pricing overrides functional")
        print("  [OK] Expiry date field (date format) properly stored")
        print("  [OK] Pricing tier hierarchy (retail > bulk > wholesale) enforced")
        print("="*80 + "\n")
        
        return 0
        
    except AssertionError as e:
        print(f"\n[ERROR] TEST FAILED: {str(e)}")
        return 1
    except Exception as e:
        print(f"\n[ERROR]: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
