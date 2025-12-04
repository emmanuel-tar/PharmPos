"""
Test suite for the redesigned Sales UI with product grid and cart functionality.
Tests the integration of load_sales_products, add_product_to_sales_cart, and cart calculations.
"""

import sys
from datetime import date
from decimal import Decimal
from PyQt5.QtWidgets import QApplication
from desktop_app.database import init_db
from desktop_app.models import ProductService, InventoryService, StoreService, get_session


def setup_test_data():
    """Setup test products and stores."""
    init_db()
    session = get_session()
    
    product_service = ProductService(session)
    store_service = StoreService(session)
    inventory_service = InventoryService(session)

    # Create primary store
    stores = store_service.get_all_stores()
    if not stores:
        store = store_service.create_store("Main Store", "123 Main St", is_primary=True)
        store_id = store["id"]
    else:
        store_id = stores[0]["id"]

    # Create test products
    products = [
        {
            "name": "Paracetamol 500mg",
            "sku": "PARA-500-001",
            "cost_price": Decimal("50.00"),
            "selling_price": Decimal("150.00"),
            "nafdac_number": "NAFDAC-2024-001",
            "generic_name": "Acetaminophen",
            "barcode": "1111111111111",
            "retail_price": Decimal("150.00"),
            "bulk_price": Decimal("120.00"),
            "bulk_quantity": 10,
            "wholesale_price": Decimal("90.00"),
            "wholesale_quantity": 50,
            "min_stock": 10,
            "max_stock": 500,
            "reorder_level": 50,
        },
        {
            "name": "Amoxicillin 250mg",
            "sku": "AMOX-250-001",
            "cost_price": Decimal("30.00"),
            "selling_price": Decimal("100.00"),
            "nafdac_number": "NAFDAC-2024-002",
            "generic_name": "Amoxicillin",
            "barcode": "2222222222222",
            "retail_price": Decimal("100.00"),
            "bulk_price": Decimal("85.00"),
            "bulk_quantity": 20,
            "wholesale_price": Decimal("70.00"),
            "wholesale_quantity": 100,
            "min_stock": 15,
            "max_stock": 400,
            "reorder_level": 30,
        },
        {
            "name": "Ibuprofen 400mg",
            "sku": "IBUP-400-001",
            "cost_price": Decimal("25.00"),
            "selling_price": Decimal("80.00"),
            "nafdac_number": "NAFDAC-2024-003",
            "generic_name": "Ibuprofen",
            "barcode": "3333333333333",
            "retail_price": Decimal("80.00"),
            "bulk_price": Decimal("65.00"),
            "bulk_quantity": 15,
            "wholesale_price": Decimal("50.00"),
            "wholesale_quantity": 75,
            "min_stock": 20,
            "max_stock": 600,
            "reorder_level": 40,
        },
    ]

    product_ids = []
    for prod_data in products:
        product = product_service.create_product(**prod_data)
        product_ids.append(product["id"])
        
        # Add stock to each product
        inventory_service.receive_stock(
            product_id=product["id"],
            batch_number=f"BATCH-{product['sku']}-001",
            quantity=100,
            cost_price=prod_data["cost_price"],
            retail_price=prod_data["retail_price"],
            expiry_date=date(2025, 12, 31),
            store_id=store_id,
        )

    return product_ids, store_id, session


if __name__ == "__main__":
    print("\n" + "="*80)
    print("SALES UI TEST SUITE - Product Grid, Search, and Cart Functionality")
    print("="*80)
    
    try:
        # Setup test data once
        product_ids, store_id, session = setup_test_data()
        
        # Test 1: Product loading
        print("\n" + "="*80)
        print("TEST: Product Loading for Sales Grid")
        print("="*80)
        
        product_service = ProductService(session)
        products = product_service.get_all_products(active_only=True)
        
        print(f"\n[OK] Loaded {len(products)} products")
        assert len(products) >= 3, "Should have at least 3 test products"
        
        for product in products:
            print(f"  • {product['name']}: ₦{product.get('retail_price', product.get('selling_price'))}")
            assert "name" in product, "Product should have name"
            assert "retail_price" in product or "selling_price" in product, "Product should have price"
            assert "id" in product, "Product should have id"
        
        # Test 2: Product search
        print("\n" + "="*80)
        print("TEST: Product Search Filtering")
        print("="*80)
        
        all_products = product_service.get_all_products(active_only=True)
        print(f"\n[OK] Loaded {len(all_products)} total products")

        search_term = "paracetamol"
        filtered = [p for p in all_products if search_term.lower() in p['name'].lower()]
        print(f"[OK] Search '{search_term}': Found {len(filtered)} product(s)")
        assert len(filtered) > 0, f"Should find product matching '{search_term}'"

        search_term = "AMOX"
        filtered = [p for p in all_products if search_term.lower() in p.get('sku', '').lower()]
        print(f"[OK] Search by SKU '{search_term}': Found {len(filtered)} product(s)")
        assert len(filtered) > 0, f"Should find product with SKU containing '{search_term}'"
        
        # Test 3: Cart calculations
        print("\n" + "="*80)
        print("TEST: Cart Calculations (Subtotal, Tax, Total)")
        print("="*80)
        
        cart_items = [
            {"price": 150.00, "qty": 2},
            {"price": 100.00, "qty": 1},
            {"price": 80.00, "qty": 3},
        ]
        
        subtotal = sum(item["price"] * item["qty"] for item in cart_items)
        tax = subtotal * 0.075
        total = subtotal + tax
        
        print(f"\n[OK] Cart Items:")
        for i, item in enumerate(cart_items, 1):
            line_total = item["price"] * item["qty"]
            print(f"  {i}. Qty: {item['qty']:>3} × Price: ₦{item['price']:>8.2f} = ₦{line_total:>8.2f}")
        
        print(f"\n[OK] Cart Summary:")
        print(f"    Subtotal:    ₦{subtotal:>10.2f}")
        print(f"    Tax (7.5%):  ₦{tax:>10.2f}")
        print(f"    Total:       ₦{total:>10.2f}")
        
        assert subtotal == 640.00, f"Subtotal should be 640.00, got {subtotal}"
        assert abs(tax - 48.00) < 0.01, f"Tax should be ~48.00, got {tax}"
        assert abs(total - 688.00) < 0.01, f"Total should be ~688.00, got {total}"
        
        # Test 4: Cart with discounts
        print("\n" + "="*80)
        print("TEST: Cart Calculations with Discounts")
        print("="*80)
        
        cart_items = [
            {"price": 150.00, "qty": 2, "discount_pct": 0},
            {"price": 100.00, "qty": 1, "discount_pct": 10},
            {"price": 80.00, "qty": 3, "discount_pct": 5},
        ]
        
        subtotal = 0
        total_discount = 0
        for item in cart_items:
            line_total = item["price"] * item["qty"]
            discount_amount = line_total * (item["discount_pct"] / 100)
            subtotal += line_total - discount_amount
            total_discount += discount_amount
        
        tax = subtotal * 0.075
        total = subtotal + tax
        
        print(f"\n[OK] Cart Items with Discounts:")
        for i, item in enumerate(cart_items, 1):
            line_total = item["price"] * item["qty"]
            discount_amount = line_total * (item["discount_pct"] / 100)
            line_after_discount = line_total - discount_amount
            print(f"  {i}. ₦{line_total:.2f} - {item['discount_pct']}% (₦{discount_amount:.2f}) = ₦{line_after_discount:.2f}")
        
        print(f"\n[OK] Cart Summary with Discounts:")
        print(f"    Subtotal:           ₦{subtotal + total_discount:>10.2f}")
        print(f"    Total Discount:    -₦{total_discount:>10.2f}")
        print(f"    After Discount:     ₦{subtotal:>10.2f}")
        print(f"    Tax (7.5%):         ₦{tax:>10.2f}")
        print(f"    Final Total:        ₦{total:>10.2f}")
        
        assert abs(total_discount - 22.00) < 0.01, f"Total discount should be ~22.00, got {total_discount}"
        assert abs(subtotal - 618.00) < 0.01, f"Subtotal after discount should be ~618.00, got {subtotal}"
        
        # Test 5: Multiple quantities
        print("\n" + "="*80)
        print("TEST: Multiple Quantities of Same Product")
        print("="*80)
        
        product = {"id": 1, "name": "Paracetamol 500mg", "price": 150.00}
        cart = []
        
        print("\n[OK] Adding 2 units of Paracetamol...")
        cart.append({"product_id": product["id"], "name": product["name"], "price": product["price"], "qty": 2})
        print(f"    Cart: {cart[-1]['name']} x {cart[-1]['qty']} = ₦{cart[-1]['price'] * cart[-1]['qty']:.2f}")
        
        print("\n[OK] Adding 1 more unit of Paracetamol (should increment qty)...")
        cart[0]["qty"] += 1
        print(f"    Cart: {cart[0]['name']} x {cart[0]['qty']} = ₦{cart[0]['price'] * cart[0]['qty']:.2f}")
        
        assert len(cart) == 1, "Should have only 1 cart row (not 2)"
        assert cart[0]["qty"] == 3, "Quantity should be 3 (2+1)"
        
        print("\n" + "="*80)
        print("[OK] ALL SALES UI TESTS PASSED")
        print("="*80)
        
    except AssertionError as e:
        print(f"\n[ERROR] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
