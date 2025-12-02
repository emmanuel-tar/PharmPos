"""
PharmaPOS NG - Integration Test

Verifies all components work together correctly.
"""

import sys
import os
from pathlib import Path

# Add project to path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def test_imports() -> bool:
    """Test all imports work."""
    print("Testing imports...")
    try:
        from desktop_app import (
            init_db,
            get_session,
            StoreService,
            UserService,
            ProductService,
            InventoryService,
            SalesService,
            AuthenticationService,
            SalesTransaction,
            BatchManager,
            SalesReporter,
        )
        print("✓ All imports successful\n")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}\n")
        return False


def test_database() -> bool:
    """Test database initialization."""
    print("Testing database...")
    try:
        from desktop_app import init_db, get_session
        
        # Use test database
        test_db = "test_pharmapos.db"
        init_db(test_db)
        
        session = get_session(test_db)
        session.close()
        
        print("✓ Database initialization successful\n")
        
        # Cleanup
        if os.path.exists(test_db):
            os.remove(test_db)
        
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}\n")
        return False


def test_authentication() -> bool:
    """Test authentication system."""
    print("Testing authentication...")
    try:
        from desktop_app.auth import PasswordManager, AuthenticationService
        from desktop_app import init_db
        
        # Test password hashing
        password = "test123"
        hashed = PasswordManager.hash_password(password)
        if not PasswordManager.verify_password(password, hashed):
            raise Exception("Password verification failed")
        
        # Test authentication service
        test_db = "test_auth.db"
        init_db(test_db)
        
        auth = AuthenticationService(test_db)
        success = auth.register_user("testuser", "password123", role="cashier")
        
        session = auth.login("testuser", "password123")
        if not session:
            raise Exception("Login failed")
        
        print("✓ Authentication system working\n")
        
        # Cleanup
        if os.path.exists(test_db):
            os.remove(test_db)
        
        return True
    except Exception as e:
        print(f"✗ Authentication test failed: {e}\n")
        return False


def test_models() -> bool:
    """Test data models and services."""
    print("Testing data models...")
    try:
        from desktop_app import (
            init_db,
            get_session,
            StoreService,
            UserService,
            ProductService,
        )
        from desktop_app.auth import PasswordManager
        from decimal import Decimal
        
        test_db = "test_models.db"
        init_db(test_db)
        
        session = get_session(test_db)
        
        # Create store
        store_service = StoreService(session)
        store = store_service.create_store("Test Store", "123 Main St", is_primary=True)
        if not store:
            raise Exception("Failed to create store")
        
        # Create user
        user_service = UserService(session)
        password_hash = PasswordManager.hash_password("test123")
        user = user_service.create_user(
            "testuser", password_hash, role="admin", store_id=store["id"]
        )
        if not user:
            raise Exception("Failed to create user")
        
        # Create product
        product_service = ProductService(session)
        product = product_service.create_product(
            "Test Product",
            "TEST-001",
            Decimal("100"),
            Decimal("200"),
            "NAFDAC/001",
        )
        if not product:
            raise Exception("Failed to create product")
        
        session.close()
        print("✓ Data models working correctly\n")
        
        # Cleanup
        if os.path.exists(test_db):
            os.remove(test_db)
        
        return True
    except Exception as e:
        print(f"✗ Models test failed: {e}\n")
        return False


def test_sales() -> bool:
    """Test sales module."""
    print("Testing sales module...")
    try:
        from desktop_app.sales import PaymentProcessor
        from decimal import Decimal
        
        # Test payment validation
        total = Decimal("1000")
        paid = Decimal("1500")
        
        is_valid, msg = PaymentProcessor.validate_payment(total, paid, "cash")
        if not is_valid:
            raise Exception("Payment validation failed")
        
        # Test change calculation
        success, change = PaymentProcessor.process_cash_payment(total, paid)
        if not success or change != Decimal("500"):
            raise Exception("Change calculation failed")
        
        print("✓ Sales module working\n")
        return True
    except Exception as e:
        print(f"✗ Sales test failed: {e}\n")
        return False


def test_reports() -> bool:
    """Test reporting module."""
    print("Testing reports module...")
    try:
        from desktop_app import init_db, SalesReporter, InventoryReporter
        from datetime import date
        
        test_db = "test_reports.db"
        init_db(test_db)
        
        # Test reporters
        sales_rep = SalesReporter(test_db)
        daily = sales_rep.get_daily_sales(1, date.today())
        if daily is None:
            raise Exception("Sales report failed")
        sales_rep.close()
        
        inv_rep = InventoryReporter(test_db)
        valuation = inv_rep.get_stock_valuation(1)
        if valuation is None:
            raise Exception("Inventory report failed")
        inv_rep.close()
        
        print("✓ Reports module working\n")
        
        # Cleanup
        if os.path.exists(test_db):
            os.remove(test_db)
        
        return True
    except Exception as e:
        print(f"✗ Reports test failed: {e}\n")
        return False


def main() -> None:
    """Run all tests."""
    print("\n" + "="*60)
    print("  PharmaPOS NG - Integration Tests")
    print("="*60 + "\n")

    tests = [
        ("Imports", test_imports),
        ("Database", test_database),
        ("Authentication", test_authentication),
        ("Data Models", test_models),
        ("Sales Module", test_sales),
        ("Reports Module", test_reports),
    ]

    results = {}
    for name, test_func in tests:
        results[name] = test_func()

    # Summary
    print("="*60)
    print("  Test Summary")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! System is ready to use.")
        return
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please review errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
