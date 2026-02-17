
import sys
from unittest.mock import MagicMock
from PyQt5.QtWidgets import QApplication

def test_pos_refinement():
    app = QApplication(sys.argv)
    
    # Mock Services
    mock_product_service = MagicMock()
    mock_inventory_service = MagicMock()
    mock_category_service = MagicMock()
    
    categories = [{'id': 1, 'name': 'Pain Killers'}, {'id': 2, 'name': 'Beverages'}]
    mock_category_service.get_all_categories.return_value = categories
    
    products = [
        {'id': 1, 'name': 'Panadol', 'sku': 'PAN001', 'category': 'Pain Killers', 'selling_price': 50.0},
        {'id': 2, 'name': 'Coca Cola', 'sku': 'COC001', 'category': 'Beverages', 'selling_price': 100.0}
    ]
    mock_product_service.get_all_products.return_value = products
    
    # Mock InventoryService
    mock_inventory_service.get_store_inventory.return_value = [
        {'id': 101, 'product_id': 1, 'batch_number': 'B1', 'retail_price': 60.0, 'quantity': 100},
        {'id': 102, 'product_id': 2, 'batch_number': 'B2', 'retail_price': 120.0, 'quantity': 50}
    ]
    
    def mock_get_fefo_batch(pid, sid):
        if pid == 1:
            return {'id': 101, 'batch_number': 'B1', 'retail_price': 60.0, 'quantity': 100}
        if pid == 2:
            return {'id': 102, 'batch_number': 'B2', 'retail_price': 120.0, 'quantity': 50}
        return None

    mock_inventory_service.get_fefo_batch.side_effect = mock_get_fefo_batch

    # Import POSView
    from ui.views.pos import POSView
    
    pos = POSView(
        product_service=mock_product_service, 
        inventory_service=mock_inventory_service,
        category_service=mock_category_service
    )
    
    # Test 1: Category Filtering
    print(f"Initial Category: {pos.current_category}")
    pos.filter_by_category('Beverages')
    print(f"New Category: {pos.current_category}")
    
    # Check if get_all_products was called with category='Beverages'
    # It might have been called multiple times (init + filter)
    found_call = False
    for call in mock_product_service.get_all_products.call_args_list:
        if call.kwargs.get('category') == 'Beverages':
            found_call = True
            break
    
    if not found_call:
        print(f"FAILED: get_all_products was not called with category='Beverages'")
        print(f"Actual calls: {mock_product_service.get_all_products.call_args_list}")
        sys.exit(1)

    # Test 2: Cart Price Fix
    pos.cart = []
    # Add Coca Cola (Price should be 120.0 from batch retail_price)
    pos.add_product_to_cart({'id': 2, 'name': 'Coca Cola'})
    print(f"Cart Item Price: {pos.cart[0]['price']}")
    assert pos.cart[0]['price'] == 120.0
    
    # Test 3: VAT Calculation
    # Subtotal should be 120.0
    # VAT (7.5%) should be 9.0
    # Total should be 129.0
    print(f"Subtotal Label: {pos.subtotal_label.text()}")
    print(f"VAT Label: {pos.vat_label.text()}")
    print(f"Total Label: {pos.total_label.text()}")
    
    if "120.00" not in pos.subtotal_label.text():
        print(f"FAILED: Subtotal label incorrect: {pos.subtotal_label.text()}")
        sys.exit(1)
    if "9.00" not in pos.vat_label.text():
        print(f"FAILED: VAT label incorrect: {pos.vat_label.text()}")
        sys.exit(1)
    if "129.00" not in pos.total_label.text():
        print(f"FAILED: Total label incorrect: {pos.total_label.text()}")
        sys.exit(1)
    
    print("All refinement tests passed!")

if __name__ == "__main__":
    try:
        test_pos_refinement()
    except Exception as e:
        print(f"Test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
