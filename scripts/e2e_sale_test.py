"""
End-to-end test: create product, receive stock, perform sale, save receipt.
Run: python scripts/e2e_sale_test.py
"""
from datetime import datetime, timedelta
from decimal import Decimal
import os

from desktop_app.database import init_db
from desktop_app.models import get_session, ProductService, InventoryService, SalesService, StoreService
from desktop_app.thermal_printer import ThermalPrinter, format_receipt


def main():
    print("Initializing DB (if needed)...")
    init_db()

    session = get_session()

    store_service = StoreService(session)
    store = store_service.get_primary_store()
    if not store:
        store = store_service.create_store(name="Main Pharmacy", address="Lagos, Nigeria", is_primary=True)

    store_id = store["id"]

    product_service = ProductService(session)
    inventory_service = InventoryService(session)
    sales_service = SalesService(session)

    # Create a test product with unique SKU
    sku = f"TEST-SKU-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    product = product_service.create_product(
        name="Test Painkiller",
        sku=sku,
        cost_price=Decimal("100.00"),
        selling_price=Decimal("150.00"),
        nafdac_number="NAF-TEST-001",
        barcode=sku,
        retail_price=Decimal("150.00"),
        bulk_price=Decimal("140.00"),
        bulk_quantity=10,
        min_stock=5,
        max_stock=1000,
    )
    print(f"Created product: {product['id']} (SKU={sku})")

    # Receive stock for the product
    expiry = (datetime.now() + timedelta(days=365)).date()
    batch = inventory_service.receive_stock(
        product_id=product["id"],
        store_id=store_id,
        batch_number=f"BATCH-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        quantity=20,
        expiry_date=expiry,
        cost_price=Decimal("100.00"),
        retail_price=Decimal("150.00"),
    )
    print(f"Received stock batch: {batch['id']} qty={batch['quantity']}")

    # Prepare sale: 3 units
    qty_to_sell = 3
    allocations = inventory_service.allocate_stock_for_sale(product_id=product['id'], store_id=store_id, quantity=qty_to_sell)
    if not allocations or sum(a['quantity'] for a in allocations) < qty_to_sell:
        raise SystemExit("Insufficient stock for test sale")

    # Build items list with unit_price from product retail_price
    items = []
    unit_price = Decimal(str(product.get('retail_price', product.get('selling_price', 0))))
    for alloc in allocations:
        items.append({
            'batch_id': alloc['batch_id'],
            'quantity': alloc['quantity'],
            'unit_price': float(unit_price),
        })

    total = sum(Decimal(str(it['quantity'])) * Decimal(str(it['unit_price'])) for it in items)
    amount_paid = total

    # Create sale
    sale = sales_service.create_sale(
        user_id=1,
        store_id=store_id,
        items=items,
        payment_method='cash',
        amount_paid=Decimal(str(amount_paid)),
    )

    print(f"Sale created: id={sale['id']} receipt={sale['receipt_number']}")

    # Format and save receipt using ThermalPrinter fallback
    receipt_text = format_receipt(
        receipt_number=sale['receipt_number'],
        items=[{'product_name': product['name'], 'quantity': qty_to_sell, 'unit_price': float(unit_price)}],
        subtotal=float(total),
        tax=0.0,
        total=float(total),
        payment_method='cash',
        amount_paid=float(amount_paid),
        change=0.0,
        store=store,
    )

    printer = ThermalPrinter(backend=None)
    res = printer.print_text(receipt_text)
    if res.get('status') == 'saved':
        print(f"Receipt saved to: {res.get('path')}")
    else:
        print("Receipt printed to device (status=printed)")


if __name__ == '__main__':
    main()
