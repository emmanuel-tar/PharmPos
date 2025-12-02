"""
PharmaPOS NG - Inventory Management & Stock Control

This module handles inventory tracking, stock levels, batch management,
and FEFO (First Expiry, First Out) logic.
"""

from __future__ import annotations

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List

from desktop_app.models import (
    InventoryService,
    StockTransferService,
    ProductService,
    get_session,
)


# --- Batch Manager -----------------------------------------------------------
class BatchManager:
    """Manages product batches and FEFO logic."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.session = get_session(db_path)
        self.inventory_service = InventoryService(self.session)
        self.product_service = ProductService(self.session)

    def receive_batch(
        self,
        product_id: int,
        store_id: int,
        batch_number: str,
        quantity: int,
        expiry_date: date,
        cost_price: Decimal,
    ) -> tuple[bool, str, Optional[dict]]:
        """Receive new batch into inventory."""
        # Validate product exists
        product = self.product_service.get_product(product_id)
        if not product:
            return False, "Product not found", None

        try:
            batch = self.inventory_service.receive_stock(
                product_id=product_id,
                store_id=store_id,
                batch_number=batch_number,
                quantity=quantity,
                expiry_date=expiry_date,
                cost_price=cost_price,
            )
            return True, "Batch received successfully", batch
        except Exception as e:
            return False, f"Error receiving batch: {str(e)}", None

    def get_fefo_batch(self, product_id: int, store_id: int) -> Optional[dict]:
        """Get the next batch to sell/use (FEFO principle)."""
        inventory = self.inventory_service.get_store_inventory(store_id)
        
        # Filter for this product and find earliest expiry
        product_batches = [
            batch for batch in inventory
            if batch["product_id"] == product_id and batch["quantity"] > 0
        ]
        
        return product_batches[0] if product_batches else None

    def check_expiry(self, batch_id: int) -> bool:
        """Check if batch has expired."""
        batch = self.inventory_service.get_batch(batch_id)
        if not batch:
            return True
        return batch["expiry_date"] <= datetime.now().date()

    def get_stock_status(self, store_id: int) -> dict:
        """Get overall stock status for store."""
        inventory = self.inventory_service.get_store_inventory(store_id)
        
        total_items = sum(batch["quantity"] for batch in inventory)
        total_value = sum(
            batch["quantity"] * (batch["cost_price"] or 0)
            for batch in inventory
        )
        
        expiring_soon = self.inventory_service.get_expiring_batches(store_id, days=30)
        
        return {
            "total_items": total_items,
            "total_value": float(total_value),
            "batch_count": len(inventory),
            "expiring_soon_count": len(expiring_soon),
        }

    def write_off_batch(
        self,
        batch_id: int,
        reason: str,
        user_id: int,
    ) -> tuple[bool, str]:
        """Write off a batch from inventory."""
        batch = self.inventory_service.get_batch(batch_id)
        if not batch:
            return False, "Batch not found"

        try:
            self.inventory_service.update_batch_quantity(
                batch_id=batch_id,
                quantity_change=-batch["quantity"],
                change_type="adjustment",
                user_id=user_id,
                notes=f"Write-off: {reason}",
            )
            return True, "Batch written off successfully"
        except Exception as e:
            return False, str(e)

    def close(self) -> None:
        """Close database session."""
        self.session.close()


# --- Stock Transfer Manager --------------------------------------------------
class StockTransferManager:
    """Manages inter-store stock transfers."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.session = get_session(db_path)
        self.transfer_service = StockTransferService(self.session)
        self.inventory_service = InventoryService(self.session)

    def initiate_transfer(
        self,
        product_id: int,
        batch_number: str,
        quantity: int,
        from_store_id: int,
        to_store_id: int,
    ) -> tuple[bool, str, Optional[dict]]:
        """Initiate a stock transfer."""
        if from_store_id == to_store_id:
            return False, "Source and destination stores must be different", None

        try:
            transfer = self.transfer_service.initiate_transfer(
                product_id=product_id,
                batch_number=batch_number,
                quantity=quantity,
                from_store_id=from_store_id,
                to_store_id=to_store_id,
            )
            return True, "Transfer initiated", transfer
        except Exception as e:
            return False, str(e), None

    def get_pending_transfers_for_store(self, store_id: int) -> List[dict]:
        """Get all pending transfers for store (as destination)."""
        return self.transfer_service.get_pending_transfers(store_id)

    def receive_transfer(
        self, transfer_id: int, received_quantity: int
    ) -> tuple[bool, str]:
        """Receive a pending transfer."""
        try:
            success = self.transfer_service.receive_transfer(
                transfer_id, received_quantity
            )
            if success:
                return True, "Transfer received successfully"
            else:
                return False, "Transfer not found"
        except Exception as e:
            return False, str(e)

    def close(self) -> None:
        """Close database session."""
        self.session.close()


# --- Inventory Alerts --------------------------------------------------------
class InventoryAlerts:
    """Generates inventory alerts and notifications."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.session = get_session(db_path)
        self.inventory_service = InventoryService(self.session)

    def get_expiring_items(self, store_id: int, days: int = 30) -> List[dict]:
        """Get items expiring within N days."""
        return self.inventory_service.get_expiring_batches(store_id, days)

    def get_expired_items(self, store_id: int) -> List[dict]:
        """Get expired items in store."""
        batches = self.inventory_service.get_store_inventory(store_id)
        today = datetime.now().date()
        return [batch for batch in batches if batch["expiry_date"] < today]

    def get_low_stock_items(
        self, store_id: int, min_quantity: int = 10
    ) -> List[dict]:
        """Get items with low stock levels."""
        inventory = self.inventory_service.get_store_inventory(store_id)
        return [batch for batch in inventory if batch["quantity"] < min_quantity]

    def generate_alerts(self, store_id: int) -> dict:
        """Generate comprehensive alert report."""
        expiring = self.get_expiring_items(store_id, 30)
        expired = self.get_expired_items(store_id)
        low_stock = self.get_low_stock_items(store_id)

        alerts = []

        if expired:
            alerts.append({
                "type": "critical",
                "message": f"{len(expired)} expired items in stock",
                "items": len(expired),
            })

        if expiring:
            alerts.append({
                "type": "warning",
                "message": f"{len(expiring)} items expiring within 30 days",
                "items": len(expiring),
            })

        if low_stock:
            alerts.append({
                "type": "info",
                "message": f"{len(low_stock)} items with low stock",
                "items": len(low_stock),
            })

        return {
            "total_alerts": len(alerts),
            "alerts": alerts,
            "generated_at": datetime.now().isoformat(),
        }

    def close(self) -> None:
        """Close database session."""
        self.session.close()


__all__ = [
    "BatchManager",
    "StockTransferManager",
    "InventoryAlerts",
]
