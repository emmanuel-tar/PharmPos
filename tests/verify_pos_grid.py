
import sys
import os
from unittest.mock import MagicMock
from PyQt5.QtWidgets import QApplication

def test_pos_grid_fixes():
    app = QApplication(sys.argv)
    
    # Mock Services
    mock_product_service = MagicMock()
    mock_inventory_service = MagicMock()
    mock_category_service = MagicMock()
    
    categories = [{'id': 1, 'name': 'Pain Killers'}]
    mock_category_service.get_all_categories.return_value = categories
    
    products = [
        {'id': 1, 'name': 'Panadol', 'sku': 'PAN001', 'category': 'Pain Killers', 'selling_price': 50.0, 'image_path': None},
    ]
    mock_product_service.get_all_products.return_value = products
    
    # Mock InventoryService
    mock_inventory_service.get_store_inventory.return_value = [
        {'id': 101, 'product_id': 1, 'batch_number': 'B1', 'retail_price': 60.0, 'quantity': 100},
    ]
    
    mock_inventory_service.get_fefo_batch.return_value = {'id': 101, 'batch_number': 'B1', 'retail_price': 60.0, 'quantity': 100}

    # Import POSView
    # This will fail if Theme.SURFACE_LIGHT is missing or imports are bad
    try:
        from ui.views.pos import POSView
        print("Import successful.")
    except Exception as e:
        print(f"Import failed: {e}")
        sys.exit(1)
    
    pos = POSView(
        product_service=mock_product_service, 
        inventory_service=mock_inventory_service,
        category_service=mock_category_service
    )
    
    # Test 1: Catalog Loading (should use ProductCard)
    print("Testing catalog update...")
    try:
        pos.update_catalog(products)
        print("Catalog updated successfully.")
    except Exception as e:
        print(f"Catalog update failed: {e}")
        sys.exit(1)

    # Test 2: Add to Cart (should call add_batch_to_cart)
    print("Testing add to cart...")
    try:
        pos.add_product_to_cart(products[0])
        print(f"Cart size: {len(pos.cart)}")
        if len(pos.cart) == 1:
            print("Item added to cart successfully.")
        else:
            print("Item NOT added to cart.")
            sys.exit(1)
    except Exception as e:
        print(f"Add to cart failed: {e}")
        sys.exit(1)
    
    print("All grid fix tests passed!")

if __name__ == "__main__":
    try:
        test_pos_grid_fixes()
    except Exception as e:
        print(f"Test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
