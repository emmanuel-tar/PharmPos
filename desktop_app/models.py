"""
PharmaPOS NG - Data Models and Services Layer

This module provides SQLAlchemy ORM models and business logic services
for managing stores, users, products, sales, and inventory.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

from desktop_app.database import (
    get_engine,
    metadata,
    stores,
    users,
    products,
    product_batches,
    sales,
    sale_items,
    stock_transfers,
    inventory_audit,
    suppliers,
    purchase_orders,
    purchase_order_items,
    purchase_receipts,
    purchase_receipt_items,
)


# --- Store Service -----------------------------------------------------------
class StoreService:
    """Service for managing stores."""

    def __init__(self, session: Session):
        self.session = session

    def create_store(
        self, name: str, address: str = "", is_primary: bool = False
    ) -> dict:
        """Create a new store."""
        stmt = stores.insert().values(
            name=name,
            address=address,
            is_primary=is_primary,
            sync_id=str(uuid.uuid4()),
        )
        result = self.session.execute(stmt)
        self.session.commit()
        return {
            "id": result.inserted_primary_key[0],
            "name": name,
            "address": address,
            "is_primary": is_primary,
        }

    def get_store(self, store_id: int) -> Optional[dict]:
        """Get store by ID."""
        stmt = select(stores).where(stores.c.id == store_id)
        result = self.session.execute(stmt).fetchone()
        return dict(result._mapping) if result else None

    def get_all_stores(self) -> List[dict]:
        """Get all stores."""
        stmt = select(stores).order_by(stores.c.name)
        results = self.session.execute(stmt).fetchall()
        return [dict(row._mapping) for row in results]

    def get_primary_store(self) -> Optional[dict]:
        """Get the primary store."""
        stmt = select(stores).where(stores.c.is_primary == True)
        result = self.session.execute(stmt).fetchone()
        return dict(result._mapping) if result else None

    def update_store(self, store_id: int, **kwargs) -> bool:
        """Update store details."""
        stmt = stores.update().where(stores.c.id == store_id).values(**kwargs)
        self.session.execute(stmt)
        self.session.commit()
        return True

    def delete_store(self, store_id: int) -> bool:
        """Delete store (careful: cascading deletes)."""
        stmt = stores.delete().where(stores.c.id == store_id)
        self.session.execute(stmt)
        self.session.commit()
        return True


# --- User Service -----------------------------------------------------------
class UserService:
    """Service for managing users and authentication."""

    def __init__(self, session: Session):
        self.session = session

    def create_user(
        self,
        username: str,
        password_hash: str,
        role: str = "cashier",
        store_id: Optional[int] = None,
    ) -> dict:
        """Create a new user."""
        stmt = users.insert().values(
            username=username,
            password_hash=password_hash,
            role=role,
            store_id=store_id,
            sync_id=str(uuid.uuid4()),
        )
        result = self.session.execute(stmt)
        self.session.commit()
        return {
            "id": result.inserted_primary_key[0],
            "username": username,
            "role": role,
            "store_id": store_id,
        }

    def get_user(self, user_id: int) -> Optional[dict]:
        """Get user by ID."""
        stmt = select(users).where(users.c.id == user_id)
        result = self.session.execute(stmt).fetchone()
        return dict(result._mapping) if result else None

    def get_user_by_username(self, username: str) -> Optional[dict]:
        """Get user by username."""
        stmt = select(users).where(users.c.username == username)
        result = self.session.execute(stmt).fetchone()
        return dict(result._mapping) if result else None

    def get_all_users(self) -> List[dict]:
        """Get all active users."""
        stmt = select(users).where(users.c.is_active == True)
        results = self.session.execute(stmt).fetchall()
        return [dict(row._mapping) for row in results]

    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user details."""
        stmt = users.update().where(users.c.id == user_id).values(**kwargs)
        self.session.execute(stmt)
        self.session.commit()
        return True

    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user."""
        return self.update_user(user_id, is_active=False)


# --- Product Service --------------------------------------------------------
class ProductService:
    """Service for managing products in the catalog."""

    def __init__(self, session: Session):
        self.session = session

    def create_product(
        self,
        name: str,
        sku: str,
        cost_price: Decimal,
        selling_price: Decimal,
        nafdac_number: str,
        generic_name: str = "",
        barcode: str = "",
        description: str = "",
        retail_price: Decimal = None,
        bulk_price: Decimal = None,
        bulk_quantity: int = None,
        wholesale_price: Decimal = None,
        wholesale_quantity: int = None,
        min_stock: int = 0,
        max_stock: int = 9999,
        reorder_level: int = None,
    ) -> dict:
        """Create a new product with pricing tiers and stock alerts."""
        stmt = products.insert().values(
            name=name,
            sku=sku,
            cost_price=cost_price,
            selling_price=selling_price,
            nafdac_number=nafdac_number,
            generic_name=generic_name,
            barcode=barcode,
            description=description,
            retail_price=retail_price or selling_price,
            bulk_price=bulk_price,
            bulk_quantity=bulk_quantity,
            wholesale_price=wholesale_price,
            wholesale_quantity=wholesale_quantity,
            min_stock=min_stock,
            max_stock=max_stock,
            reorder_level=reorder_level,
            sync_id=str(uuid.uuid4()),
        )
        result = self.session.execute(stmt)
        self.session.commit()
        return {
            "id": result.inserted_primary_key[0],
            "name": name,
            "sku": sku,
            "cost_price": float(cost_price),
            "selling_price": float(selling_price),
            "retail_price": float(retail_price or selling_price),
            "bulk_price": float(bulk_price) if bulk_price is not None else None,
            "bulk_quantity": int(bulk_quantity) if bulk_quantity is not None else None,
            "wholesale_price": float(wholesale_price) if wholesale_price is not None else None,
            "wholesale_quantity": int(wholesale_quantity) if wholesale_quantity is not None else None,
            "min_stock": int(min_stock),
            "max_stock": int(max_stock),
            "reorder_level": int(reorder_level) if reorder_level is not None else None,
        }

    def get_product(self, product_id: int) -> Optional[dict]:
        """Get product by ID."""
        stmt = select(products).where(products.c.id == product_id)
        result = self.session.execute(stmt).fetchone()
        return dict(result._mapping) if result else None

    def get_product_by_sku(self, sku: str) -> Optional[dict]:
        """Get product by SKU."""
        stmt = select(products).where(products.c.sku == sku)
        result = self.session.execute(stmt).fetchone()
        return dict(result._mapping) if result else None

    def get_product_by_barcode(self, barcode: str) -> Optional[dict]:
        """Get product by barcode."""
        stmt = select(products).where(products.c.barcode == barcode)
        result = self.session.execute(stmt).fetchone()
        return dict(result._mapping) if result else None

    def get_all_products(self, active_only: bool = True) -> List[dict]:
        """Get all products."""
        if active_only:
            stmt = select(products).where(products.c.is_active == True)
        else:
            stmt = select(products)
        results = self.session.execute(stmt).fetchall()
        return [dict(row._mapping) for row in results]

    def update_product(self, product_id: int, **kwargs) -> bool:
        """Update product details."""
        stmt = products.update().where(products.c.id == product_id).values(**kwargs)
        self.session.execute(stmt)
        self.session.commit()
        return True

    def deactivate_product(self, product_id: int) -> bool:
        """Deactivate a product."""
        return self.update_product(product_id, is_active=False)


# --- Inventory Service (Batch & Stock) ---------------------------------------
class InventoryService:
    """Service for managing product batches and stock levels."""

    def __init__(self, session: Session):
        self.session = session

    def receive_stock(
        self,
        product_id: int,
        store_id: int,
        batch_number: str,
        quantity: int,
        expiry_date: date,
        cost_price: Decimal,
        retail_price: Decimal = None,
        bulk_price: Decimal = None,
        bulk_quantity: int = None,
        wholesale_price: Decimal = None,
        wholesale_quantity: int = None,
        min_stock: int = 0,
        max_stock: int = 9999,
        reorder_level: int = None,
    ) -> dict:
        """Record receipt of new stock batch with comprehensive pricing."""
        # Insert batch with all pricing info
        stmt = product_batches.insert().values(
            product_id=product_id,
            store_id=store_id,
            batch_number=batch_number,
            quantity=quantity,
            expiry_date=expiry_date,
            cost_price=cost_price,
            retail_price=retail_price,
            bulk_price=bulk_price,
            bulk_quantity=bulk_quantity,
            wholesale_price=wholesale_price,
            wholesale_quantity=wholesale_quantity,
            sync_id=str(uuid.uuid4()),
        )
        result = self.session.execute(stmt)
        batch_id = result.inserted_primary_key[0]

        # Update product master with stock alert levels and pricing
        product_update = (
            products.update()
            .where(products.c.id == product_id)
            .values(
                min_stock=min_stock,
                max_stock=max_stock,
                reorder_level=reorder_level if reorder_level else quantity // 2,
                retail_price=retail_price or cost_price * Decimal("1.5"),
                bulk_price=bulk_price,
                bulk_quantity=bulk_quantity,
                wholesale_price=wholesale_price,
                wholesale_quantity=wholesale_quantity,
            )
        )
        self.session.execute(product_update)
        self.session.commit()

        return {
            "id": batch_id,
            "product_id": product_id,
            "batch_number": batch_number,
            "quantity": quantity,
            "expiry_date": expiry_date,
            "cost_price": cost_price,
            "retail_price": retail_price,
            "bulk_price": bulk_price,
            "bulk_quantity": bulk_quantity,
            "wholesale_price": wholesale_price,
            "wholesale_quantity": wholesale_quantity,
            "min_stock": min_stock,
            "max_stock": max_stock,
            "reorder_level": reorder_level,
        }

    def get_batch(self, batch_id: int) -> Optional[dict]:
        """Get batch by ID."""
        stmt = select(product_batches).where(product_batches.c.id == batch_id)
        result = self.session.execute(stmt).fetchone()
        return dict(result._mapping) if result else None

    def get_store_inventory(self, store_id: int) -> List[dict]:
        """Get all batches in store, ordered by expiry date (FEFO)."""
        stmt = (
            select(product_batches)
            .where(product_batches.c.store_id == store_id)
            .where(product_batches.c.quantity > 0)
            .order_by(product_batches.c.expiry_date)
        )
        results = self.session.execute(stmt).fetchall()
        return [dict(row._mapping) for row in results]

    def get_product_stock(self, product_id: int, store_id: int) -> int:
        """Get total quantity in stock for a product in a store."""
        stmt = select(func.sum(product_batches.c.quantity)).where(
            and_(
                product_batches.c.product_id == product_id,
                product_batches.c.store_id == store_id,
                product_batches.c.quantity > 0,
            )
        )
        result = self.session.execute(stmt).scalar()
        return result or 0

    def get_available_batches(self, product_id: int, store_id: int, quantity_needed: int = None) -> List[dict]:
        """Get all available batches for a product in FEFO order (earliest expiry first)."""
        stmt = (
            select(product_batches)
            .where(product_batches.c.product_id == product_id)
            .where(product_batches.c.store_id == store_id)
            .where(product_batches.c.quantity > 0)
            .order_by(product_batches.c.expiry_date)
        )
        results = self.session.execute(stmt).fetchall()
        batches = [dict(row._mapping) for row in results]
        return batches

    def allocate_stock_for_sale(self, product_id: int, store_id: int, quantity: int) -> List[dict]:
        """Allocate stock for a sale using FEFO. Returns list of allocations: [{batch_id, quantity}]."""
        if quantity <= 0:
            return []

        # Select available batches FEFO
        stmt = (
            select(product_batches)
            .where(product_batches.c.product_id == product_id)
            .where(product_batches.c.store_id == store_id)
            .where(product_batches.c.quantity > 0)
            .order_by(product_batches.c.expiry_date)
        )
        results = self.session.execute(stmt).fetchall()
        remaining = int(quantity)
        allocations = []

        for row in results:
            batch = dict(row._mapping)
            if remaining <= 0:
                break
            available = int(batch.get("quantity", 0) or 0)
            if available <= 0:
                continue
            take = min(available, remaining)
            allocations.append({"batch_id": batch["id"], "quantity": take})
            remaining -= take

        return allocations


    def reserve_stock(self, product_batch_id: int, quantity: int, reason: str, user_id: int) -> Optional[dict]:
        """Reserve (hold) a quantity on a specific batch."""
        from desktop_app.database import stock_reservations
        
        batch = self.get_batch(product_batch_id)
        if not batch or batch["quantity"] < quantity:
            return None # Insufficient stock

        stmt = stock_reservations.insert().values(
            product_batch_id=product_batch_id,
            quantity=quantity,
            reason=reason,
            status="active",
            user_id=user_id,
            sync_id=str(uuid.uuid4()),
        )
        result = self.session.execute(stmt)
        self.session.commit()
        
        reservation_id = result.inserted_primary_key[0]
        
        # Deduct stock
        self.update_batch_quantity(
            batch_id=product_batch_id,
            quantity_change=-quantity,
            change_type="reserved",
            user_id=user_id,
            reference_id=reservation_id,
            notes=f"Reserve: {reason}",
        )
        
        return {
            "reservation_id": reservation_id,
            "product_batch_id": product_batch_id,
            "quantity": quantity,
            "reason": reason,
        }

    def release_reservation(self, reservation_id: int, user_id: int) -> bool:
        """Release a reservation, returning quantity to available stock."""
        from desktop_app.database import stock_reservations
        
        stmt = select(stock_reservations).where(stock_reservations.c.id == reservation_id)
        result = self.session.execute(stmt).fetchone()
        if not result:
            return False
        reservation = dict(result._mapping)
        
        if reservation["status"] != "active":
            return False

        # Update status
        update_stmt = (
            stock_reservations.update()
            .where(stock_reservations.c.id == reservation_id)
            .values(status="released")
        )
        self.session.execute(update_stmt)
        
        # Return quantity to batch
        return self.update_batch_quantity(
            batch_id=reservation["product_batch_id"],
            quantity_change=reservation["quantity"],
            change_type="release",
            user_id=user_id,
            reference_id=reservation_id,
            notes="Release reservation",
        )

    def adjust_stock(self, batch_id: int, quantity_change: int, user_id: int, reason: str = "adjustment") -> bool:
        """Adjust batch quantity (positive or negative) and log audit."""
        return self.update_batch_quantity(
            batch_id=batch_id,
            quantity_change=quantity_change,
            change_type=reason,
            user_id=user_id,
            notes=f"Adjustment: {reason}",
        )

    def writeoff_batch(self, batch_id: int, quantity: Optional[int], user_id: int, reason: str = "writeoff") -> bool:
        """Write off `quantity` from a batch (or full batch if quantity is None)."""
        batch = self.get_batch(batch_id)
        if not batch:
            return False

        prev = int(batch.get("quantity", 0) or 0)
        to_remove = prev if quantity is None else min(prev, int(quantity))
        if to_remove <= 0:
            return False

        return self.update_batch_quantity(
            batch_id=batch_id,
            quantity_change=-to_remove,
            change_type="writeoff",
            user_id=user_id,
            notes=f"Write-off: {reason}",
        )


    def transfer_stock(self, product_id: int, batch_number: str, quantity: int, from_store_id: int, to_store_id: int, user_id: int) -> Optional[int]:
        """Transfer stock from one store to another. Creates transfer record and adjusts batches."""
        from desktop_app.database import stock_transfers
        from datetime import datetime

        if quantity <= 0:
            return None

        # Find batches to deduct in from_store_id ordered FEFO
        stmt = (
            select(product_batches)
            .where(product_batches.c.product_id == product_id)
            .where(product_batches.c.store_id == from_store_id)
            .where(product_batches.c.quantity > 0)
            .order_by(product_batches.c.expiry_date)
        )
        results = self.session.execute(stmt).fetchall()
        remaining = int(quantity)
        allocations = []
        for row in results:
            if remaining <= 0:
                break
            batch = dict(row._mapping)
            avail = int(batch.get("quantity", 0) or 0)
            if avail <= 0:
                continue
            take = min(avail, remaining)
            allocations.append((batch["id"], take, batch["batch_number"], batch.get("expiry_date")))
            remaining -= take

        if remaining > 0:
            return None # Not enough stock

        # Create transfer record
        transfer_stmt = stock_transfers.insert().values(
            product_id=product_id,
            batch_number=batch_number,
            quantity=quantity,
            from_store_id=from_store_id,
            to_store_id=to_store_id,
            status="pending",
            sync_id=str(uuid.uuid4()),
        )
        transfer_result = self.session.execute(transfer_stmt)
        transfer_id = transfer_result.inserted_primary_key[0]

        # Deduct from source batches and add/increment target batch(s)
        for bid, qty_taken, bnum, expiry in allocations:
            # deduct
            self.update_batch_quantity(
                batch_id=bid,
                quantity_change=-qty_taken,
                change_type="transfer_out",
                user_id=user_id,
                reference_id=transfer_id,
                notes=f"Transfer out to store {to_store_id}",
            )

            # try to find existing batch in target store with same batch_number
            target_stmt = select(product_batches).where(
                product_batches.c.product_id == product_id,
                product_batches.c.store_id == to_store_id,
                product_batches.c.batch_number == bnum,
            )
            tgt = self.session.execute(target_stmt).fetchone()
            if tgt:
                tgt_dict = dict(tgt._mapping)
                # increase quantity
                self.update_batch_quantity(
                    batch_id=tgt_dict["id"],
                    quantity_change=qty_taken,
                    change_type="transfer_in",
                    user_id=user_id,
                    reference_id=transfer_id,
                    notes=f"Transfer in from store {from_store_id}",
                )
            else:
                # create new batch in target
                ins = product_batches.insert().values(
                    product_id=product_id,
                    store_id=to_store_id,
                    batch_number=bnum,
                    expiry_date=expiry,
                    quantity=qty_taken,
                    sync_id=str(uuid.uuid4()),
                )
                self.session.execute(ins)

        # mark transfer as received for now (simplified)
        upd = stock_transfers.update().where(stock_transfers.c.id == transfer_id).values(status="received", received_date=datetime.now())
        self.session.execute(upd)
        self.session.commit()
        return transfer_id

    def reconcile_inventory(self, store_id: int, physical_counts: List[dict], user_id: int) -> dict:
        """Reconcile physical counts against recorded batches."""
        from desktop_app.database import inventory_reconciliations, reconciliation_items
        from datetime import datetime

        # Create reconciliation record
        recon_stmt = inventory_reconciliations.insert().values(
            store_id=store_id,
            started_at=datetime.now(),
            user_id=user_id,
            sync_id=str(uuid.uuid4()),
        )
        recon_result = self.session.execute(recon_stmt)
        reconciliation_id = recon_result.inserted_primary_key[0]

        report = {"adjustments": [], "reconciliation_id": reconciliation_id}
        total_variance = 0

        for item in physical_counts:
            batch_id = item.get("product_batch_id")
            counted = int(item.get("counted_qty", 0))
            
            if batch_id:
                batch = self.get_batch(batch_id)
                if not batch: continue
                recorded = int(batch.get("quantity", 0) or 0)
                diff = counted - recorded
                
                # Record item
                item_stmt = reconciliation_items.insert().values(
                    reconciliation_id=reconciliation_id,
                    product_batch_id=batch_id,
                    system_quantity=recorded,
                    counted_quantity=counted,
                    difference=diff,
                    sync_id=str(uuid.uuid4()),
                )
                self.session.execute(item_stmt)

                if diff != 0:
                    self.adjust_stock(batch_id, diff, user_id, "reconciliation")
                    report["adjustments"].append({"batch_id": batch_id, "delta": diff})
                    total_variance += abs(diff)

        self.session.commit()
        return report

    def get_expiring_batches(self, store_id: int, days: int = 30) -> List[dict]:
        """Get batches expiring within N days."""
        from datetime import timedelta, datetime
        cutoff_date = datetime.now().date() + timedelta(days=days)
        stmt = (
            select(product_batches)
            .where(product_batches.c.store_id == store_id)
            .where(product_batches.c.expiry_date <= cutoff_date)
            .where(product_batches.c.quantity > 0)
            .order_by(product_batches.c.expiry_date)
        )
        results = self.session.execute(stmt).fetchall()
        return [dict(row._mapping) for row in results]

    def get_expired_batches(self, store_id: int) -> List[dict]:
        """Return batches whose expiry_date is before today and still have quantity."""
        from datetime import datetime
        today = datetime.now().date()
        stmt = (
            select(product_batches)
            .where(product_batches.c.store_id == store_id)
            .where(product_batches.c.expiry_date < today)
            .where(product_batches.c.quantity > 0)
            .order_by(product_batches.c.expiry_date)
        )
        results = self.session.execute(stmt).fetchall()
        return [dict(row._mapping) for row in results]


    def expire_batch(self, batch_id: int, user_id: int, notes: str = "Expired - auto") -> bool:
        """Mark a single batch as expired by zeroing quantity and logging an audit entry."""
        batch = self.get_batch(batch_id)
        if not batch:
            return False

        qty = batch.get("quantity", 0) or 0
        if qty <= 0:
            return False

        return self.update_batch_quantity(
            batch_id=batch_id,
            quantity_change=-qty,
            change_type="expired",
            user_id=user_id,
            notes=notes,
        )

    def expire_batches_older_than(self, store_id: int, days: int, user_id: int) -> int:
        """Expire all batches in a store older than `days`."""
        from datetime import timedelta, datetime
        cutoff = datetime.now().date() - timedelta(days=days)
        stmt = (
            select(product_batches.c.id)
            .where(product_batches.c.store_id == store_id)
            .where(product_batches.c.expiry_date <= cutoff)
            .where(product_batches.c.quantity > 0)
        )
        results = self.session.execute(stmt).fetchall()
        batch_ids = [row[0] for row in results]
        expired_count = 0
        for bid in batch_ids:
            if self.expire_batch(bid, user_id, notes=f"Bulk expire older than {days} days"):
                expired_count += 1
        return expired_count

    def expire_batches_within_days(self, store_id: int, days: int, user_id: int) -> int:
        """Expire all batches that will expire within the next `days` days."""
        from datetime import timedelta, datetime
        cutoff = datetime.now().date() + timedelta(days=days)
        stmt = (
            select(product_batches.c.id)
            .where(product_batches.c.store_id == store_id)
            .where(product_batches.c.expiry_date <= cutoff)
            .where(product_batches.c.quantity > 0)
        )
        results = self.session.execute(stmt).fetchall()
        batch_ids = [row[0] for row in results]
        expired_count = 0
        for bid in batch_ids:
            if self.expire_batch(bid, user_id, notes=f"Bulk expire within next {days} days"):
                expired_count += 1
        return expired_count

    def update_batch_quantity(self, batch_id: int, quantity_change: int, change_type: str, user_id: int, reference_id: Optional[int] = None, notes: str = "") -> bool:
        """Update batch quantity and log the change in audit trail."""
        from desktop_app.database import inventory_audit
        
        batch = self.get_batch(batch_id)
        if not batch:
            return False

        previous_qty = batch["quantity"]
        new_qty = previous_qty + quantity_change

        # Update batch
        stmt = (
            product_batches.update()
            .where(product_batches.c.id == batch_id)
            .values(quantity=new_qty)
        )
        self.session.execute(stmt)

        # Log to audit trail
        audit_stmt = inventory_audit.insert().values(
            product_batch_id=batch_id,
            previous_quantity=previous_qty,
            new_quantity=new_qty,
            change_type=change_type,
            reference_id=reference_id,
            notes=notes,
            user_id=user_id,
            sync_id=str(uuid.uuid4()),
        )
        self.session.execute(audit_stmt)
        self.session.commit()
        return True

    def confirm_reservation(self, reservation_id: int, user_id: int, reference_id: Optional[int] = None) -> bool:
        """Confirm a reservation and deduct as sale."""
        from desktop_app.database import stock_reservations
        
        stmt = select(stock_reservations).where(stock_reservations.c.id == reservation_id)
        result = self.session.execute(stmt).fetchone()
        if not result:
            return False
        reservation = dict(result._mapping)
        
        if reservation["status"] != "active":
            return False

        # Update status
        update_stmt = (
            stock_reservations.update()
            .where(stock_reservations.c.id == reservation_id)
            .values(status="confirmed")
        )
        self.session.execute(update_stmt)

        # Log to audit (quantity already deducted on reserve)
        return self.update_batch_quantity(
            batch_id=reservation["product_batch_id"],
            quantity_change=0,
            change_type="confirm_reserve",
            user_id=user_id,
            reference_id=reference_id or reservation_id,
            notes="Confirm reservation as sale",
        )

    def create_backorder(self, product_id: int, store_id: int, quantity: int, customer_id: Optional[int], notes: str, user_id: int) -> Optional[dict]:
        """Create a backorder."""
        from desktop_app.database import backorders
        
        stmt = backorders.insert().values(
            product_id=product_id,
            store_id=store_id,
            quantity_requested=quantity,
            customer_name=str(customer_id) if customer_id else None,
            notes=notes,
            user_id=user_id,
            status="pending",
            sync_id=str(uuid.uuid4()),
        )
        result = self.session.execute(stmt)
        self.session.commit()
        
        backorder_id = result.inserted_primary_key[0]
        return {
            "backorder_id": backorder_id,
            "product_id": product_id,
            "quantity": quantity,
            "status": "pending",
        }


# --- Sales Service -----------------------------------------------------------
class SalesService:
    """Service for processing sales transactions."""

    def __init__(self, session: Session):
        self.session = session
        self.inventory_service = InventoryService(session)

    def create_sale(
        self,
        user_id: int,
        store_id: int,
        items: List[dict],  # [{batch_id, quantity, unit_price}, ...]
        payment_method: str,
        amount_paid: Decimal,
        payment_reference: Optional[str] = None,
        gateway_response: Optional[str] = None,
    ) -> dict:
        """Create a complete sale transaction with items."""
        # Calculate total
        total_amount = sum(
            Decimal(str(item["quantity"])) * Decimal(str(item["unit_price"]))
            for item in items
        )
        change_amount = amount_paid - total_amount

        # Generate receipt number
        receipt_number = self._generate_receipt_number(store_id)

        # Create sale
        sale_stmt = sales.insert().values(
            receipt_number=receipt_number,
            total_amount=total_amount,
            amount_paid=amount_paid,
            payment_method=payment_method,
            change_amount=change_amount,
            user_id=user_id,
            store_id=store_id,
            payment_reference=payment_reference,
            gateway_response=gateway_response,
            sync_id=str(uuid.uuid4()),
        )
        sale_result = self.session.execute(sale_stmt)
        sale_id = sale_result.inserted_primary_key[0]

        # Add sale items and update inventory
        for item in items:
            item_stmt = sale_items.insert().values(
                sale_id=sale_id,
                product_batch_id=item["batch_id"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
            )
            self.session.execute(item_stmt)

            # Update batch quantity (negative for sale)
            self.inventory_service.update_batch_quantity(
                batch_id=item["batch_id"],
                quantity_change=-item["quantity"],
                change_type="sale",
                user_id=user_id,
                reference_id=sale_id,
            )

        self.session.commit()
        return {
            "id": sale_id,
            "receipt_number": receipt_number,
            "total_amount": float(total_amount),
            "amount_paid": float(amount_paid),
            "change_amount": float(change_amount),
        }

    def get_sale(self, sale_id: int) -> Optional[dict]:
        """Get sale details."""
        stmt = select(sales).where(sales.c.id == sale_id)
        result = self.session.execute(stmt).fetchone()
        return dict(result._mapping) if result else None

    def get_sale_items(self, sale_id: int) -> List[dict]:
        """Get all items in a sale."""
        stmt = select(sale_items).where(sale_items.c.sale_id == sale_id)
        results = self.session.execute(stmt).fetchall()
        return [dict(row._mapping) for row in results]

    def get_sales_by_date(
        self, store_id: int, start_date: date, end_date: date
    ) -> List[dict]:
        """Get sales within date range."""
        stmt = (
            select(sales)
            .where(sales.c.store_id == store_id)
            .where(
                and_(
                    func.date(sales.c.created_at) >= start_date,
                    func.date(sales.c.created_at) <= end_date,
                )
            )
            .order_by(sales.c.created_at.desc())
        )
        results = self.session.execute(stmt).fetchall()
        return [dict(row._mapping) for row in results]

    def _generate_receipt_number(self, store_id: int) -> str:
        """Generate unique receipt number."""
        from datetime import datetime

        stmt = select(func.count(sales.c.id)).where(sales.c.store_id == store_id)
        count = self.session.execute(stmt).scalar() or 0
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"RCP-{store_id}-{timestamp}-{count + 1:05d}"


# --- Stock Transfer Service --------------------------------------------------
class StockTransferService:
    """Service for managing stock transfers between stores."""

    def __init__(self, session: Session):
        self.session = session
        self.inventory_service = InventoryService(session)

    def initiate_transfer(
        self,
        product_id: int,
        batch_number: str,
        quantity: int,
        from_store_id: int,
        to_store_id: int,
    ) -> dict:
        """Initiate a stock transfer request."""
        stmt = stock_transfers.insert().values(
            product_id=product_id,
            batch_number=batch_number,
            quantity=quantity,
            from_store_id=from_store_id,
            to_store_id=to_store_id,
            status="pending",
            sync_id=str(uuid.uuid4()),
        )
        result = self.session.execute(stmt)
        self.session.commit()
        return {
            "id": result.inserted_primary_key[0],
            "status": "pending",
            "quantity": quantity,
        }

    def receive_transfer(self, transfer_id: int, received_quantity: int) -> bool:
        """Receive a pending transfer at destination store."""
        transfer_stmt = select(stock_transfers).where(
            stock_transfers.c.id == transfer_id
        )
        transfer = self.session.execute(transfer_stmt).fetchone()
        if not transfer:
            return False

        transfer_dict = dict(transfer._mapping)

        # Update transfer status
        update_stmt = (
            stock_transfers.update()
            .where(stock_transfers.c.id == transfer_id)
            .values(
                status="received",
                received_date=datetime.now(),
            )
        )
        self.session.execute(update_stmt)
        self.session.commit()
        return True

    def get_pending_transfers(self, store_id: int) -> List[dict]:
        """Get pending transfers for a store."""
        stmt = (
            select(stock_transfers)
            .where(stock_transfers.c.to_store_id == store_id)
            .where(stock_transfers.c.status == "pending")
        )
        results = self.session.execute(stmt).fetchall()
        return [dict(row._mapping) for row in results]


# --- Supplier Service --------------------------------------------------------
class SupplierService:
    """Service for managing suppliers."""

    def __init__(self, session: Session):
        self.session = session

    def create_supplier(
        self,
        name: str,
        contact: str = "",
        address: str = "",
    ) -> dict:
        """Create a new supplier."""
        stmt = suppliers.insert().values(
            name=name,
            contact=contact,
            address=address,
            sync_id=str(uuid.uuid4()),
        )
        result = self.session.execute(stmt)
        self.session.commit()
        return {
            "id": result.inserted_primary_key[0],
            "name": name,
            "contact": contact,
            "address": address,
        }

    def get_supplier(self, supplier_id: int) -> Optional[dict]:
        """Get supplier by ID."""
        stmt = select(suppliers).where(suppliers.c.id == supplier_id)
        result = self.session.execute(stmt).fetchone()
        return dict(result._mapping) if result else None

    def get_all_suppliers(self) -> List[dict]:
        """Get all suppliers."""
        stmt = select(suppliers).order_by(suppliers.c.name)
        results = self.session.execute(stmt).fetchall()
        return [dict(row._mapping) for row in results]

    def update_supplier(self, supplier_id: int, **kwargs) -> bool:
        """Update supplier details."""
        stmt = suppliers.update().where(suppliers.c.id == supplier_id).values(**kwargs)
        self.session.execute(stmt)
        self.session.commit()
        return True

    def delete_supplier(self, supplier_id: int) -> bool:
        """Delete supplier (careful: cascading deletes)."""
        stmt = suppliers.delete().where(suppliers.c.id == supplier_id)
        self.session.execute(stmt)
        self.session.commit()
        return True


# --- Purchase Order Service --------------------------------------------------
class PurchaseOrderService:
    """Service for managing purchase orders and related operations."""

    def __init__(self, session: Session):
        self.session = session
        self.inventory_service = InventoryService(session)

    def create_purchase_order(
        self,
        supplier_id: int,
        store_id: int,
        user_id: int,
        items: List[dict],  # [{product_id, quantity_ordered, expected_cost_price, notes}]
        expected_delivery_date: Optional[date] = None,
        notes: str = "",
    ) -> dict:
        """Create a new purchase order with items."""
        # Calculate total expected amount
        total_expected = sum(
            Decimal(str(item["quantity_ordered"])) * Decimal(str(item.get("expected_cost_price", 0)))
            for item in items
        )

        # Generate PO number
        po_number = self._generate_po_number(store_id)

        # Create PO
        po_stmt = purchase_orders.insert().values(
            po_number=po_number,
            supplier_id=supplier_id,
            store_id=store_id,
            user_id=user_id,
            total_expected_amount=total_expected,
            status="draft",
            expected_delivery_date=expected_delivery_date,
            notes=notes,
            sync_id=str(uuid.uuid4()),
        )
        po_result = self.session.execute(po_stmt)
        po_id = po_result.inserted_primary_key[0]

        # Add PO items
        for item in items:
            item_stmt = purchase_order_items.insert().values(
                purchase_order_id=po_id,
                product_id=item["product_id"],
                quantity_ordered=item["quantity_ordered"],
                expected_cost_price=item.get("expected_cost_price"),
                notes=item.get("notes", ""),
            )
            self.session.execute(item_stmt)

        self.session.commit()
        return {
            "id": po_id,
            "po_number": po_number,
            "supplier_id": supplier_id,
            "total_expected_amount": float(total_expected),
            "status": "draft",
        }

    def submit_purchase_order(self, po_id: int, user_id: int) -> bool:
        """Submit PO for approval."""
        stmt = purchase_orders.update().where(purchase_orders.c.id == po_id).values(
            status="submitted"
        )
        self.session.execute(stmt)
        self.session.commit()
        return True

    def approve_purchase_order(self, po_id: int, approver_id: int, comments: str = "") -> bool:
        """Approve a purchase order."""
        stmt = purchase_orders.update().where(purchase_orders.c.id == po_id).values(
            status="approved",
            approved_by=approver_id,
            approved_at=datetime.now(),
        )
        self.session.execute(stmt)
        self.session.commit()
        return True

    def reject_purchase_order(self, po_id: int, approver_id: int, comments: str = "") -> bool:
        """Reject a purchase order."""
        stmt = purchase_orders.update().where(purchase_orders.c.id == po_id).values(
            status="rejected",
            approved_by=approver_id,
            approved_at=datetime.now(),
        )
        self.session.execute(stmt)
        self.session.commit()
        return True

    def receive_goods(
        self,
        po_id: int,
        user_id: int,
        receipts: List[dict],  # [{product_id, batch_number, expiry_date, received_quantity, actual_cost_price}]
    ) -> dict:
        """Receive goods against a purchase order."""
        # Create receipt record
        receipt_stmt = purchase_receipts.insert().values(
            purchase_order_id=po_id,
            received_by=user_id,
            sync_id=str(uuid.uuid4()),
        )
        receipt_result = self.session.execute(receipt_stmt)
        receipt_id = receipt_result.inserted_primary_key[0]

        total_received_value = Decimal("0")

        # Process each receipt item
        for receipt in receipts:
            product_id = receipt["product_id"]
            batch_number = receipt["batch_number"]
            expiry_date = receipt["expiry_date"]
            quantity = receipt["received_quantity"]
            cost_price = Decimal(str(receipt["actual_cost_price"]))

            total_received_value += quantity * cost_price

            # Add to receipt items
            item_stmt = purchase_receipt_items.insert().values(
                receipt_id=receipt_id,
                product_id=product_id,
                batch_number=batch_number,
                expiry_date=expiry_date,
                quantity=quantity,
                cost_price=cost_price,
            )
            self.session.execute(item_stmt)

            # Update PO item received quantity
            po_item_stmt = (
                purchase_order_items.update()
                .where(purchase_order_items.c.purchase_order_id == po_id)
                .where(purchase_order_items.c.product_id == product_id)
                .values(quantity_received=purchase_order_items.c.quantity_received + quantity)
            )
            self.session.execute(po_item_stmt)

            # Add to inventory
            batch = self.inventory_service.receive_stock(
                product_id=product_id,
                store_id=self.get_purchase_order(po_id)["store_id"],
                batch_number=batch_number,
                quantity=quantity,
                expiry_date=expiry_date,
                cost_price=cost_price,
            )

        # Update PO status if fully received
        po = self.get_purchase_order(po_id)
        total_ordered = sum(item["quantity_ordered"] for item in self.get_po_items(po_id))
        total_received = sum(item["quantity_received"] for item in self.get_po_items(po_id))

        if total_received >= total_ordered:
            po_update_stmt = purchase_orders.update().where(purchase_orders.c.id == po_id).values(
                status="received",
                actual_delivery_date=date.today(),
            )
            self.session.execute(po_update_stmt)

        self.session.commit()
        return {
            "receipt_id": receipt_id,
            "total_received_value": float(total_received_value),
        }

    def get_purchase_order(self, po_id: int) -> Optional[dict]:
        """Get purchase order by ID."""
        stmt = select(purchase_orders).where(purchase_orders.c.id == po_id)
        result = self.session.execute(stmt).fetchone()
        return dict(result._mapping) if result else None

    def get_po_items(self, po_id: int) -> List[dict]:
        """Get all items in a purchase order."""
        stmt = select(purchase_order_items).where(purchase_order_items.c.purchase_order_id == po_id)
        results = self.session.execute(stmt).fetchall()
        return [dict(row._mapping) for row in results]

    def get_purchase_orders_by_status(self, store_id: int, status: str = None) -> List[dict]:
        """Get purchase orders by status with supplier names."""
        from sqlalchemy import join

        # Join purchase_orders with suppliers to get supplier names
        stmt = select(
            purchase_orders,
            suppliers.c.name.label('supplier_name')
        ).select_from(
            join(purchase_orders, suppliers, purchase_orders.c.supplier_id == suppliers.c.id)
        ).where(purchase_orders.c.store_id == store_id)

        if status:
            stmt = stmt.where(purchase_orders.c.status == status)

        stmt = stmt.order_by(purchase_orders.c.created_at.desc())

        results = self.session.execute(stmt).fetchall()
        return [dict(row._mapping) for row in results]

    def _generate_po_number(self, store_id: int) -> str:
        """Generate unique PO number."""
        from datetime import datetime

        stmt = select(func.count(purchase_orders.c.id)).where(purchase_orders.c.store_id == store_id)
        count = self.session.execute(stmt).scalar() or 0
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"PO-{store_id}-{timestamp}-{count + 1:04d}"


# --- Session Factory ---------------------------------------------------------
def get_session(db_path: Optional[str] = None) -> Session:
    """Get a database session."""
    engine = get_engine(db_path)
    Session = sessionmaker(bind=engine)
    return Session()


__all__ = [
    "StoreService",
    "UserService",
    "ProductService",
    "InventoryService",
    "SalesService",
    "StockTransferService",
    "SupplierService",
    "PurchaseOrderService",
    "get_session",
]
