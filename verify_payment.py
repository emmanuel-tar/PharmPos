"""
Verification script for Payment Gateway Integration.
Tests the backend logic for recording online payments.
"""

import sys
import os
from decimal import Decimal

# Add project root to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from desktop_app.database import init_db, get_engine, sales, sale_items, product_batches, products, stores, users
from desktop_app.sales import SalesTransaction
from desktop_app.models import get_session
from sqlalchemy import text

def setup_test_data():
    """Setup minimal test data."""
    if os.path.exists("test_payment.db"):
        try:
            os.remove("test_payment.db")
        except:
            pass
            
    init_db("test_payment.db")
    engine = get_engine("test_payment.db")
    
    with engine.connect() as conn:
        # Create store
        conn.execute(text("INSERT OR IGNORE INTO stores (id, name, is_primary) VALUES (1, 'Test Store', 1)"))
        
        # Create user
        conn.execute(text("INSERT OR IGNORE INTO users (id, username, password_hash, role, store_id) VALUES (1, 'admin', 'hash', 'admin', 1)"))
        
        # Create product
        conn.execute(text("INSERT OR IGNORE INTO products (id, name, sku, cost_price, selling_price, retail_price, nafdac_number) VALUES (1, 'Test Product', 'SKU001', 100, 150, 150, 'NAFDAC-001')"))
        
        # Create batch
        conn.execute(text("INSERT OR IGNORE INTO product_batches (id, product_id, store_id, batch_number, expiry_date, quantity, cost_price) VALUES (1, 1, 1, 'BATCH001', '2025-12-31', 100, 100)"))
        
        conn.commit()

def verify_online_payment():
    """Test recording a sale with Paystack payment."""
    print("Setting up test data...")
    setup_test_data()
    
    print("Initializing SalesTransaction...")
    sales_tx = SalesTransaction("test_payment.db")
    
    # Verify data visibility
    from desktop_app.database import users, stores
    print("Checking users...")
    u = sales_tx.session.execute(text("SELECT * FROM users")).fetchall()
    print(f"Users: {u}")
    s = sales_tx.session.execute(text("SELECT * FROM stores")).fetchall()
    print(f"Stores: {s}")
    
    # Create cart
    cart = [
        {
            "batch_id": 1,
            "quantity": 2,
            "unit_price": 150.0
        }
    ]
    
    payment_method = "paystack"
    amount_paid = Decimal("300.00")
    reference = "TX-TEST-12345"
    gateway_response = '{"status": "success", "amount": 30000}'
    
    print(f"Finalizing sale with {payment_method} and reference {reference}...")
    success, message, sale = sales_tx.finalize_sale(
        user_id=1,
        store_id=1,
        cart=cart,
        payment_method=payment_method,
        amount_paid=amount_paid,
        payment_reference=reference,
        gateway_response=gateway_response
    )
    
    if not success:
        print(f"FAILED: {message}")
        sys.exit(1)
        
    print(f"Sale successful! Receipt: {sale['receipt_number']}")
    
    # Verify in database
    session = get_session("test_payment.db")
    db_sale = session.execute(
        text("SELECT payment_method, payment_reference, gateway_response FROM sales WHERE receipt_number = :rn"),
        {"rn": sale['receipt_number']}
    ).fetchone()
    
    print("\nVerifying Database Record:")
    print(f"Payment Method: {db_sale[0]}")
    print(f"Reference: {db_sale[1]}")
    print(f"Response: {db_sale[2]}")
    
    assert db_sale[0] == "paystack", f"Expected paystack, got {db_sale[0]}"
    assert db_sale[1] == reference, f"Expected {reference}, got {db_sale[1]}"
    assert db_sale[2] == gateway_response, "Gateway response mismatch"
    
    print("\n[OK] Payment Integration Verified Successfully")

if __name__ == "__main__":
    try:
        verify_online_payment()
    except Exception as e:
        print(f"\n[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()
        # Also print the inner exception if available
        if hasattr(e, 'orig'):
            print(f"Original error: {e.orig}")
        sys.exit(1)
