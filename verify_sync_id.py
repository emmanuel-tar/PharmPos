
import os
import sys
from decimal import Decimal
from datetime import date, datetime

# Add project root to path
sys.path.append(os.getcwd())

from desktop_app.database import init_db, get_engine, stores, users, products, product_batches, sales, stock_transfers, stock_reservations, backorders, inventory_reconciliations
from desktop_app.models import get_session, StoreService, UserService, ProductService, InventoryService, SalesService, StockTransferService
from sqlalchemy import select

def verify_sync_id():
    print("Initializing DB...")
    db_path = "test_sync.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    init_db(db_path)
    session = get_session(db_path)
    
    try:
        print("Testing Store Creation...")
        store_service = StoreService(session)
        store = store_service.create_store("Test Store", "123 Test St", False)
        store_rec = session.execute(select(stores).where(stores.c.id == store['id'])).fetchone()
        print(f"Store Sync ID: {store_rec.sync_id}")
        assert store_rec.sync_id is not None
        
        print("Testing User Creation...")
        user_service = UserService(session)
        user = user_service.create_user("testuser", "hash", "admin", store['id'])
        user_rec = session.execute(select(users).where(users.c.id == user['id'])).fetchone()
        print(f"User Sync ID: {user_rec.sync_id}")
        assert user_rec.sync_id is not None
        
        print("Testing Product Creation...")
        product_service = ProductService(session)
        product = product_service.create_product(
            "Test Product", "SKU123", Decimal("100.00"), Decimal("150.00"), "NAFDAC123"
        )
        prod_rec = session.execute(select(products).where(products.c.id == product['id'])).fetchone()
        print(f"Product Sync ID: {prod_rec.sync_id}")
        assert prod_rec.sync_id is not None
        
        print("Testing Stock Receipt (Batch)...")
        inventory_service = InventoryService(session)
        batch = inventory_service.receive_stock(
            product['id'], store['id'], "BATCH001", 100, date(2025, 12, 31), Decimal("100.00")
        )
        batch_rec = session.execute(select(product_batches).where(product_batches.c.id == batch['id'])).fetchone()
        print(f"Batch Sync ID: {batch_rec.sync_id}")
        assert batch_rec.sync_id is not None
        
        print("Testing Sale Creation...")
        sales_service = SalesService(session)
        sale_items = [{"batch_id": batch['id'], "quantity": 1, "unit_price": Decimal("150.00")}]
        sale = sales_service.create_sale(
            user['id'], store['id'], sale_items, "cash", Decimal("150.00")
        )
        sale_rec = session.execute(select(sales).where(sales.c.id == sale['id'])).fetchone()
        print(f"Sale Sync ID: {sale_rec.sync_id}")
        assert sale_rec.sync_id is not None
        
        print("Testing Stock Transfer...")
        transfer_service = StockTransferService(session)
        # Create another store
        store2 = store_service.create_store("Store 2")
        transfer = transfer_service.initiate_transfer(
            product['id'], "BATCH001", 5, store['id'], store2['id']
        )
        transfer_rec = session.execute(select(stock_transfers).where(stock_transfers.c.id == transfer['id'])).fetchone()
        print(f"Transfer Sync ID: {transfer_rec.sync_id}")
        assert transfer_rec.sync_id is not None
        
        print("Testing Reservation...")
        reservation = inventory_service.reserve_stock(
            batch['id'], 2, "hold", user['id']
        )
        res_rec = session.execute(select(stock_reservations).where(stock_reservations.c.id == reservation['reservation_id'])).fetchone()
        print(f"Reservation Sync ID: {res_rec.sync_id}")
        assert res_rec.sync_id is not None
        
        print("Testing Backorder...")
        backorder = inventory_service.create_backorder(
            product['id'], store['id'], 10, None, "test", user['id']
        )
        bo_rec = session.execute(select(backorders).where(backorders.c.id == backorder['backorder_id'])).fetchone()
        print(f"Backorder Sync ID: {bo_rec.sync_id}")
        assert bo_rec.sync_id is not None
        
        print("Testing Reconciliation...")
        recon = inventory_service.reconcile_inventory(
            store['id'], [{"product_batch_id": batch['id'], "counted_qty": 90}], user['id']
        )
        recon_rec = session.execute(select(inventory_reconciliations).where(inventory_reconciliations.c.id == recon['reconciliation_id'])).fetchone()
        print(f"Reconciliation Sync ID: {recon_rec.sync_id}")
        assert recon_rec.sync_id is not None
        
        print("ALL TESTS PASSED!")
        
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
        # if os.path.exists(db_path):
        #     os.remove(db_path)

if __name__ == "__main__":
    verify_sync_id()
