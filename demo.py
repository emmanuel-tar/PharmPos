"""
PharmaPOS NG - Demo Script

This script demonstrates the core functionality of the pharmacy management system.
Run this to test the system without the GUI.
"""

from datetime import date, timedelta
from decimal import Decimal
import sys
import os

# Add the project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from desktop_app.database import init_db
from desktop_app.auth import AuthenticationService, PasswordManager
from desktop_app.models import (
    StoreService,
    UserService,
    ProductService,
    InventoryService,
    SalesService,
    get_session,
)
from desktop_app.sales import PaymentProcessor
from desktop_app.inventory import BatchManager, InventoryAlerts
from desktop_app.reports import SalesReporter, InventoryReporter


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_setup() -> None:
    """Initialize database and create demo data."""
    print_section("1. DATABASE INITIALIZATION")
    
    # Initialize database
    db_path = "pharmapos_demo.db"
    init_db(db_path)
    print(f"✓ Database initialized: {db_path}")

    # Create session
    session = get_session(db_path)

    # Create services
    store_service = StoreService(session)
    user_service = UserService(session)
    product_service = ProductService(session)
    inventory_service = InventoryService(session)

    # Create stores
    print("\nCreating stores...")
    store1 = store_service.create_store(
        "Main Pharmacy", "123 Main Street, Lagos", is_primary=True
    )
    print(f"✓ Created store: {store1['name']} (ID: {store1['id']})")

    store2 = store_service.create_store(
        "Branch Pharmacy", "456 Branch Avenue, Abuja"
    )
    print(f"✓ Created store: {store2['name']} (ID: {store2['id']})")

    # Create users with hashed passwords
    print("\nCreating users...")
    admin_hash = PasswordManager.hash_password("admin123")
    admin = user_service.create_user(
        "admin", admin_hash, role="admin", store_id=store1["id"]
    )
    print(f"✓ Created admin user: {admin['username']}")

    cashier_hash = PasswordManager.hash_password("cashier123")
    cashier = user_service.create_user(
        "cashier1", cashier_hash, role="cashier", store_id=store1["id"]
    )
    print(f"✓ Created cashier user: {cashier['username']}")

    # Create products
    print("\nCreating products...")
    products_data = [
        ("Paracetamol 500mg", "PAR-500", Decimal("50"), Decimal("100"), "NAFDAC/001"),
        ("Amoxicillin 250mg", "AMX-250", Decimal("150"), Decimal("300"), "NAFDAC/002"),
        ("Ibuprofen 400mg", "IBU-400", Decimal("75"), Decimal("150"), "NAFDAC/003"),
    ]

    created_products = []
    for name, sku, cost, selling, nafdac in products_data:
        product = product_service.create_product(
            name=name,
            sku=sku,
            cost_price=cost,
            selling_price=selling,
            nafdac_number=nafdac,
        )
        created_products.append(product)
        print(f"✓ Created product: {name}")

    # Receive stock
    print("\nReceiving stock into inventory...")
    expiry_date = date.today() + timedelta(days=365)
    
    batch1 = inventory_service.receive_stock(
        product_id=created_products[0]["id"],
        store_id=store1["id"],
        batch_number="BATCH-001",
        quantity=100,
        expiry_date=expiry_date,
        cost_price=Decimal("50"),
    )
    print(f"✓ Received batch: {batch1['batch_number']} ({batch1['quantity']} units)")

    batch2 = inventory_service.receive_stock(
        product_id=created_products[1]["id"],
        store_id=store1["id"],
        batch_number="BATCH-002",
        quantity=50,
        expiry_date=expiry_date,
        cost_price=Decimal("150"),
    )
    print(f"✓ Received batch: {batch2['batch_number']} ({batch2['quantity']} units)")

    session.close()
    return db_path, created_products, store1, admin


def demo_authentication(db_path: str) -> None:
    """Demonstrate authentication and user management."""
    print_section("2. AUTHENTICATION & USER MANAGEMENT")

    auth_service = AuthenticationService(db_path)

    # Register new user
    print("Registering new user...")
    success = auth_service.register_user("manager1", "manager123", role="manager")
    print(f"✓ User registered: manager1")

    # Login
    print("\nAttempting login...")
    session = auth_service.login("admin", "admin123")
    if session:
        print(f"✓ Login successful for user: {session.username}")
        print(f"  Role: {session.role}")
        print(f"  Session ID: {session.session_id[:20]}...")
    else:
        print("✗ Login failed")

    # Invalid login
    print("\nAttempting invalid login...")
    session = auth_service.login("admin", "wrongpassword")
    if not session:
        print("✓ Correctly rejected invalid credentials")

    # Logout
    if session:
        auth_service.logout(session.session_id)
        print("✓ Logout successful")


def demo_sales(db_path: str, products: list, store: dict, user: dict) -> None:
    """Demonstrate sales transactions."""
    print_section("3. SALES TRANSACTIONS")

    session = get_session(db_path)
    sales_service = SalesService(session)
    inventory_service = InventoryService(session)

    # Get batches
    inventory = inventory_service.get_store_inventory(store["id"])
    print(f"Current inventory: {len(inventory)} batches")

    # Create sale
    print("\nProcessing sale...")
    items = [
        {
            "batch_id": inventory[0]["id"],
            "quantity": 5,
            "unit_price": Decimal("100"),
        },
    ]

    sale = sales_service.create_sale(
        user_id=user["id"],
        store_id=store["id"],
        items=items,
        payment_method="cash",
        amount_paid=Decimal("600"),
    )

    print(f"✓ Sale completed successfully")
    print(f"  Receipt: {sale['receipt_number']}")
    print(f"  Total: ₦{sale['total_amount']:.2f}")
    print(f"  Change: ₦{sale['change_amount']:.2f}")

    # Verify stock was updated
    updated_inventory = inventory_service.get_store_inventory(store["id"])
    print(f"\n✓ Inventory updated: {len(updated_inventory)} batches remain")

    session.close()


def demo_inventory_management(db_path: str, store: dict) -> None:
    """Demonstrate inventory management features."""
    print_section("4. INVENTORY MANAGEMENT")

    session = get_session(db_path)
    inventory_service = InventoryService(session)

    # Get stock status
    print("Stock Status:")
    inventory = inventory_service.get_store_inventory(store["id"])
    total_qty = sum(b["quantity"] for b in inventory)
    total_value = sum(b["quantity"] * (b["cost_price"] or 0) for b in inventory)
    print(f"✓ Total items in stock: {total_qty}")
    print(f"✓ Total stock value: ₦{total_value:.2f}")
    print(f"✓ Number of batches: {len(inventory)}")

    # Check expiring items
    print("\nExpiring Items (within 30 days):")
    expiring = inventory_service.get_expiring_batches(store["id"], days=30)
    if expiring:
        for batch in expiring:
            print(
                f"  - Batch {batch['batch_number']}: "
                f"{batch['quantity']} units, expires {batch['expiry_date']}"
            )
    else:
        print("  ✓ No items expiring soon")

    session.close()


def demo_alerts(db_path: str, store: dict) -> None:
    """Demonstrate inventory alerts system."""
    print_section("5. INVENTORY ALERTS")

    alerts_service = InventoryAlerts(db_path)
    alerts = alerts_service.generate_alerts(store["id"])

    print(f"Total alerts: {alerts['total_alerts']}\n")

    for alert in alerts["alerts"]:
        alert_type = alert["type"].upper()
        print(f"[{alert_type}] {alert['message']} ({alert['items']} items)")

    alerts_service.close()


def demo_reports(db_path: str, store: dict) -> None:
    """Demonstrate reporting features."""
    print_section("6. REPORTING & ANALYTICS")

    # Sales Reports
    print("Sales Reports:")
    sales_reporter = SalesReporter(db_path)
    daily_report = sales_reporter.get_daily_sales(store["id"], date.today())
    print(f"  Transactions today: {daily_report['transaction_count']}")
    print(f"  Revenue today: ₦{daily_report['total_revenue']:.2f}")

    # Inventory Reports
    print("\nInventory Reports:")
    inventory_reporter = InventoryReporter(db_path)
    valuation = inventory_reporter.get_stock_valuation(store["id"])
    print(f"  Total items: {valuation['total_items_in_stock']}")
    print(f"  Inventory value: ₦{valuation['total_inventory_value']:.2f}")

    sales_reporter.close()
    inventory_reporter.close()


def main() -> None:
    """Run complete demo."""
    print("\n" + "="*60)
    print("  PharmaPOS NG - DEMO")
    print("  Pharmacy Billing & Inventory Management System")
    print("="*60)

    # Run demo sections
    db_path, products, store, user = demo_setup()
    demo_authentication(db_path)
    demo_sales(db_path, products, store, user)
    demo_inventory_management(db_path, store)
    demo_alerts(db_path, store)
    demo_reports(db_path, store)

    print_section("DEMO COMPLETE")
    print(f"Database: {db_path}")
    print("\nTo start the desktop application, run: python app.py")


if __name__ == "__main__":
    main()
