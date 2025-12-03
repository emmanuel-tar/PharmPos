"""
PharmaPOS NG - Data Models and Services Layer

This module provides SQLAlchemy ORM models and business logic services
for managing stores, users, products, sales, and inventory.
"""

from __future__ import annotations

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List

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
            name=name, address=address, is_primary=is_primary
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
    ) -> dict:
        """Create a new product."""
        stmt = products.insert().values(
            name=name,
            sku=sku,
            cost_price=cost_price,
            selling_price=selling_price,
            nafdac_number=nafdac_number,
            generic_name=generic_name,
            barcode=barcode,
            description=description,
        )
        result = self.session.execute(stmt)
        self.session.commit()
        return {
            "id": result.inserted_primary_key[0],
            "name": name,
            "sku": sku,
            "cost_price": float(cost_price),
            "selling_price": float(selling_price),
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
    ) -> dict:
        """Record receipt of new stock batch."""
        stmt = product_batches.insert().values(
            product_id=product_id,
            store_id=store_id,
            batch_number=batch_number,
            quantity=quantity,
            expiry_date=expiry_date,
            cost_price=cost_price,
        )
        result = self.session.execute(stmt)
        self.session.commit()
        return {
            "id": result.inserted_primary_key[0],
            "product_id": product_id,
            "batch_number": batch_number,
            "quantity": quantity,
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

    def allocate_stock_for_sale(self, product_id: int, store_id: int, quantity: int) -> List[dict]:
        """Allocate stock for a sale using FEFO. Returns list of allocations: [{batch_id, quantity}].

        This does not commit a sale; it only prepares an allocation map. The caller
        should apply `update_batch_quantity` to deduct quantities once payment succeeds
        or call `create_sale` which will atomically deduct.
        """
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

    def reserve_stock(self, product_id: int, store_id: int, quantity: int, user_id: int, ttl_seconds: int = 300) -> Optional[int]:
        """Create a reservation for a product quantity. Returns reservation id or None.

        A reservation is a logical hold and does not modify batch quantities. It should be
        checked during allocation and cleared on sale completion or timeout.
        """
        from datetime import datetime, timedelta

        if quantity <= 0:
            return None

        reserved_until = datetime.now() + timedelta(seconds=ttl_seconds)
        stmt = stock_reservations.insert().values(
            product_id=product_id,
            store_id=store_id,
            quantity=quantity,
            user_id=user_id,
            reserved_until=reserved_until,
            status="active",
        )
        result = self.session.execute(stmt)
        self.session.commit()
        return result.inserted_primary_key[0]

    def release_reservation(self, reservation_id: int, user_id: Optional[int] = None) -> bool:
        """Release a reservation (mark as cancelled)."""
        stmt = (
            stock_reservations.update()
            .where(stock_reservations.c.id == reservation_id)
            .values(status="cancelled")
        )
        self.session.execute(stmt)
        self.session.commit()
        return True

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
        """Transfer stock from one store to another. Creates transfer record and adjusts batches.

        Simple implementation: deduct from batches in `from_store_id` (FEFO), and create or
        increase a batch with same batch_number in `to_store_id`.
        Returns transfer record id or None.
        """
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
            # Not enough stock to transfer
            return None

        # Create transfer record
        transfer_stmt = stock_transfers.insert().values(
            product_id=product_id,
            batch_number=batch_number,
            quantity=quantity,
            from_store_id=from_store_id,
            to_store_id=to_store_id,
            status="pending",
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
                )
                self.session.execute(ins)

        # mark transfer as received for now
        upd = stock_transfers.update().where(stock_transfers.c.id == transfer_id).values(status="received", received_date=datetime.now())
        self.session.execute(upd)
        self.session.commit()
        return transfer_id

    def reconcile_inventory(self, store_id: int, physical_counts: List[dict], user_id: int) -> dict:
        """Reconcile physical counts against recorded batches.

        `physical_counts` is a list of {product_id, counted_qty}.
        Returns a simple report with adjustments performed.
        """
        report = {"adjustments": []}
        for item in physical_counts:
            pgid = int(item["product_id"])
            counted = int(item["counted_qty"])
            recorded = int(self.get_product_stock(pgid, store_id) or 0)
            diff = counted - recorded
            if diff == 0:
                continue
            # For now, apply a single adjustment to the earliest batch (or create a phantom batch)
            # If diff > 0 we add stock to a phantom batch (untracked), if diff < 0 we remove from oldest batch(s)
            if diff > 0:
                # create phantom batch
                ins = product_batches.insert().values(product_id=pgid, store_id=store_id, batch_number=f"RECON-{datetime.now().strftime('%Y%m%d%H%M%S')}", expiry_date=datetime.now().date(), quantity=diff)
                res = self.session.execute(ins)
                report["adjustments"].append({"product_id": pgid, "delta": diff, "action": "added_phantom_batch"})
            else:
                # remove from batches FEFO until satisfied
                to_remove = -diff
                stmt = select(product_batches).where(product_batches.c.product_id == pgid, product_batches.c.store_id == store_id, product_batches.c.quantity > 0).order_by(product_batches.c.expiry_date)
                rows = self.session.execute(stmt).fetchall()
                for r in rows:
                    if to_remove <= 0:
                        break
                    b = dict(r._mapping)
                    avail = int(b.get("quantity", 0) or 0)
                    take = min(avail, to_remove)
                    if take > 0:
                        self.update_batch_quantity(batch_id=b["id"], quantity_change=-take, change_type="reconcile", user_id=user_id, notes="Reconciliation removal")
                        report["adjustments"].append({"product_id": pgid, "delta": -take, "batch_id": b["id"]})
                        to_remove -= take

        return report

    def get_expiring_batches(self, store_id: int, days: int = 30) -> List[dict]:
        """Get batches expiring within N days."""
        from datetime import timedelta

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
        """Mark a single batch as expired by zeroing quantity and logging an audit entry.

        This method uses `update_batch_quantity` to create an audit trail and
        will return False if the batch does not exist or has no quantity.
        """
        batch = self.get_batch(batch_id)
        if not batch:
            return False

        qty = batch.get("quantity", 0) or 0
        if qty <= 0:
            # Nothing to expire
            return False

        return self.update_batch_quantity(
            batch_id=batch_id,
            quantity_change=-qty,
            change_type="expired",
            user_id=user_id,
            notes=notes,
        )

    def expire_batches_older_than(self, store_id: int, days: int, user_id: int) -> int:
        """Expire all batches in a store older than `days` (expiry within days in past).

        Returns the number of batches expired.
        """
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
        """Expire all batches that will expire within the next `days` days.

        Useful for proactively marking near-expiry stock as expired or moving to quarantine.
        Returns the number of batches expired.
        """
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

    def update_batch_quantity(
        self,
        batch_id: int,
        quantity_change: int,
        change_type: str,
        user_id: int,
        reference_id: Optional[int] = None,
        notes: str = "",
    ) -> bool:
        """Update batch quantity and log the change in audit trail."""
        # Get current batch
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
        )
        self.session.execute(audit_stmt)
        self.session.commit()
        return True


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
    "get_session",
]
