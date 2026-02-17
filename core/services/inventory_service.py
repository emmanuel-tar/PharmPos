"""
PharmaPOS NG - Inventory Service

This module handles inventory tracking, stock levels, batch management,
and FEFO (First Expiry, First Out) logic.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from .base_service import BaseService


# --- Inventory Service -------------------------------------------------------
class InventoryService(BaseService):
    """Manages product batches, stock levels, and FEFO logic."""

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize inventory service.
        
        Args:
            session: SQLAlchemy database session
        """
        super().__init__(session)

    def receive_batch(
        self,
        product_id: int,
        store_id: int,
        batch_number: str,
        quantity: int,
        expiry_date: date,
        cost_price: Decimal,
    ) -> Optional[dict]:
        """
        Receive new batch into inventory.
        """
        from desktop_app.models import InventoryService as ModelInventoryService
        
        inventory_service = ModelInventoryService(self.session)
        try:
            batch = inventory_service.receive_stock(
                product_id=product_id,
                store_id=store_id,
                batch_number=batch_number,
                quantity=quantity,
                expiry_date=expiry_date,
                cost_price=cost_price,
            )
            return batch
        except Exception:
            return None

    def get_fefo_batch(self, product_id: int, store_id: int) -> Optional[dict]:
        """
        Get the next batch to sell/use (FEFO principle).
        """
        from desktop_app.models import InventoryService as ModelInventoryService
        
        inventory_service = ModelInventoryService(self.session)
        batches = inventory_service.get_available_batches(product_id, store_id)
        return batches[0] if batches else None

    def check_expiry(self, batch_id: int) -> bool:
        """
        Check if batch has expired.
        """
        from desktop_app.models import InventoryService as ModelInventoryService
        
        inventory_service = ModelInventoryService(self.session)
        batch = inventory_service.get_batch(batch_id)
        if not batch or not batch.get("expiry_date"):
            return False
        return batch["expiry_date"] < date.today()

    def get_stock_status(self, store_id: int) -> Dict[str, int]:
        """
        Get overall stock status for store.
        """
        from desktop_app.models import InventoryService as ModelInventoryService
        
        inventory_service = ModelInventoryService(self.session)
        batches = inventory_service.get_store_inventory(store_id)
        
        total_items = len(batches)
        total_quantity = sum(b.get("quantity", 0) for b in batches)
        low_stock = sum(1 for b in batches if b.get("quantity", 0) < 10)
        
        return {
            "total_items": total_items,
            "total_quantity": total_quantity,
            "low_stock_count": low_stock,
        }

    def write_off_batch(
        self,
        batch_id: int,
        reason: str,
        user_id: int,
    ) -> bool:
        """
        Write off a batch from inventory.
        """
        from desktop_app.models import InventoryService as ModelInventoryService
        
        inventory_service = ModelInventoryService(self.session)
        try:
            inventory_service.writeoff_batch(
                batch_id=batch_id,
                quantity=None, # Write off full batch
                user_id=user_id,
                reason=reason,
            )
            return True
        except Exception:
            return False

    def get_expiring_items(self, store_id: int, days: int = 30) -> List[dict]:
        """
        Get items expiring within N days.
        """
        from desktop_app.models import InventoryService as ModelInventoryService
        
        inventory_service = ModelInventoryService(self.session)
        return inventory_service.get_expiring_batches(store_id, days)

    def get_expired_items(self, store_id: int) -> List[dict]:
        """
        Get expired items in store.
        """
        from desktop_app.models import InventoryService as ModelInventoryService
        
        inventory_service = ModelInventoryService(self.session)
        return inventory_service.get_expired_batches(store_id)

    def get_low_stock_items(
        self, store_id: int, min_quantity: int = 10
    ) -> List[dict]:
        """
        Get items with low stock levels.
        """
        from desktop_app.models import InventoryService as ModelInventoryService
        
        inventory_service = ModelInventoryService(self.session)
        batches = inventory_service.get_store_inventory(store_id)
        
        low_stock = [
            b for b in batches
            if b.get("quantity", 0) < min_quantity
        ]
        return low_stock

    def get_batch_history(self, batch_id: int) -> List[dict]:
        """Get audit history for a specific batch."""
        from desktop_app.models import InventoryService as ModelInventoryService
        
        inventory_service = ModelInventoryService(self.session)
        return inventory_service.get_batch_history(batch_id)

    def get_product_history(self, product_id: int, store_id: Optional[int] = None) -> List[dict]:
        """Get movement history for a product."""
        from desktop_app.models import InventoryService as ModelInventoryService
        
        inventory_service = ModelInventoryService(self.session)
        return inventory_service.get_product_history(product_id, store_id)

    def get_batches_by_store(self, store_id: int) -> List[dict]:
        """Get all active batches for a store with product details."""
        from desktop_app.models import InventoryService as ModelInventoryService
        
        inventory_service = ModelInventoryService(self.session)
        return inventory_service.get_store_inventory(store_id)


# --- Stock Transfer Service --------------------------------------------------
class StockTransferService(BaseService):
    """Manages inter-store stock transfers."""

    def __init__(self, session: Optional[Session] = None):
        super().__init__(session)

    def initiate_transfer(
        self,
        product_id: int,
        batch_number: str,
        quantity: int,
        from_store_id: int,
        to_store_id: int,
    ) -> Optional[dict]:
        """
        Initiate a stock transfer.
        """
        from desktop_app.models import StockTransferService as ModelStockTransferService
        
        transfer_service = ModelStockTransferService(self.session)
        try:
            transfer = transfer_service.initiate_transfer(
                product_id=product_id,
                batch_number=batch_number,
                quantity=quantity,
                from_store_id=from_store_id,
                to_store_id=to_store_id,
            )
            return transfer
        except Exception:
            return None

    def get_pending_transfers_for_store(self, store_id: int) -> List[dict]:
        """
        Get all pending transfers for store (as destination).
        """
        from desktop_app.models import StockTransferService as ModelStockTransferService
        
        transfer_service = ModelStockTransferService(self.session)
        return transfer_service.get_pending_transfers(store_id)

    def receive_transfer(
        self, transfer_id: int, received_quantity: int
    ) -> bool:
        """
        Receive a pending transfer.
        """
        from desktop_app.models import StockTransferService as ModelStockTransferService
        
        transfer_service = ModelStockTransferService(self.session)
        try:
            transfer_service.receive_transfer(transfer_id, received_quantity)
            return True
        except Exception:
            return False


__all__ = [
    "InventoryService",
    "StockTransferService",
]
