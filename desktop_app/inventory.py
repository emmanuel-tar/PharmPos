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
from sqlalchemy import text


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

    def get_expiry_timeline(self, store_id: int, months: int = 12) -> dict:
        """Get expiry timeline for next N months."""
        try:
            result = self.session.execute(text("""
                SELECT 
                    strftime('%Y-%m', pb.expiry_date) as month,
                    COUNT(DISTINCT pb.id) as batch_count,
                    SUM(pb.quantity) as total_quantity,
                    COUNT(DISTINCT pb.product_id) as product_count
                FROM product_batches pb
                WHERE pb.store_id = :store_id
                AND pb.expiry_date BETWEEN date('now') AND date('now', '+' || :months || ' months')
                AND pb.quantity > 0
                GROUP BY month
                ORDER BY month
            """), {"store_id": store_id, "months": months})
            
            timeline = []
            for row in result:
                timeline.append({
                    "month": row[0],
                    "batch_count": row[1],
                    "total_quantity": row[2],
                    "product_count": row[3]
                })
            
            return {
                "months": months,
                "timeline": timeline,
                "total_batches": sum(t["batch_count"] for t in timeline),
                "total_items": sum(t["total_quantity"] for t in timeline)
            }
        except Exception as e:
            print(f"Error getting expiry timeline: {e}")
            return {"months": months, "timeline": [], "total_batches": 0, "total_items": 0}

    def suggest_promotions(self, store_id: int, days_to_expiry: int = 60) -> List[dict]:
        """Suggest products for promotion before expiry."""
        try:
            result = self.session.execute(text("""
                SELECT 
                    p.id as product_id,
                    p.name as product_name,
                    p.sku,
                    pb.batch_number,
                    pb.expiry_date,
                    pb.quantity,
                    pb.cost_price,
                    pb.retail_price,
                    CAST(julianday(pb.expiry_date) - julianday('now') AS INTEGER) as days_until_expiry
                FROM product_batches pb
                JOIN products p ON pb.product_id = p.id
                WHERE pb.store_id = :store_id
                AND pb.expiry_date BETWEEN date('now') AND date('now', '+' || :days || ' days')
                AND pb.quantity > 0
                ORDER BY pb.expiry_date ASC
            """), {"store_id": store_id, "days": days_to_expiry})
            
            suggestions = []
            for row in result:
                days_left = row[8]
                
                # Calculate suggested discount based on days until expiry
                if days_left <= 30:
                    suggested_discount = 30  # 30% off
                elif days_left <= 45:
                    suggested_discount = 20  # 20% off
                else:
                    suggested_discount = 10  # 10% off
                
                retail_price = float(row[7] or 0)
                discounted_price = retail_price * (1 - suggested_discount / 100)
                
                suggestions.append({
                    "product_id": row[0],
                    "product_name": row[1],
                    "sku": row[2],
                    "batch_number": row[3],
                    "expiry_date": row[4],
                    "quantity": row[5],
                    "cost_price": float(row[6] or 0),
                    "retail_price": retail_price,
                    "days_until_expiry": days_left,
                    "suggested_discount": suggested_discount,
                    "suggested_price": round(discounted_price, 2),
                    "urgency": "high" if days_left <= 30 else "medium" if days_left <= 45 else "low"
                })
            
            return suggestions
        except Exception as e:
            print(f"Error suggesting promotions: {e}")
            return []

    def auto_mark_expired(self, store_id: int) -> tuple[int, List[dict]]:
        """Automatically identify expired batches for write-off."""
        try:
            result = self.session.execute(text("""
                SELECT 
                    pb.id as batch_id,
                    p.name as product_name,
                    p.sku,
                    pb.batch_number,
                    pb.expiry_date,
                    pb.quantity,
                    pb.cost_price
                FROM product_batches pb
                JOIN products p ON pb.product_id = p.id
                WHERE pb.store_id = :store_id
                AND pb.expiry_date < date('now')
                AND pb.quantity > 0
                ORDER BY pb.expiry_date ASC
            """), {"store_id": store_id})
            
            expired_batches = []
            total_value = 0
            
            for row in result:
                cost_value = float(row[5] or 0) * float(row[6] or 0)
                total_value += cost_value
                
                expired_batches.append({
                    "batch_id": row[0],
                    "product_name": row[1],
                    "sku": row[2],
                    "batch_number": row[3],
                    "expiry_date": row[4],
                    "quantity": row[5],
                    "cost_price": float(row[6] or 0),
                    "total_value": round(cost_value, 2)
                })
            
            return len(expired_batches), expired_batches
        except Exception as e:
            print(f"Error marking expired batches: {e}")
            return 0, []

    def get_expiry_summary(self, store_id: int) -> dict:
        """Get comprehensive expiry summary."""
        expired_count, expired_items = self.auto_mark_expired(store_id)
        expiring_7 = len(self.get_expiring_items(store_id, 7))
        expiring_30 = len(self.get_expiring_items(store_id, 30))
        expiring_90 = len(self.get_expiring_items(store_id, 90))
        
        total_expired_value = sum(item["total_value"] for item in expired_items)
        
        return {
            "expired": {
                "count": expired_count,
                "total_value": round(total_expired_value, 2)
            },
            "expiring_soon": {
                "7_days": expiring_7,
                "30_days": expiring_30,
                "90_days": expiring_90
            },
            "requires_action": expired_count + expiring_7,
            "generated_at": datetime.now().isoformat()
        }

    def close(self) -> None:
        """Close database session."""
        self.session.close()


# --- Reconciliation Manager --------------------------------------------------
class ReconciliationManager:
    """Manages inventory reconciliation and variance tracking."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.session = get_session(db_path)
        self.inventory_service = InventoryService(self.session)

    def start_reconciliation(
        self, store_id: int, user_id: int, notes: str = ""
    ) -> tuple[bool, str, Optional[int]]:
        """Start a new reconciliation session."""
        try:
            # Create reconciliation record
            result = self.session.execute(text("""
                INSERT INTO inventory_reconciliations 
                (store_id, user_id, reconciliation_date, notes, sync_id, sync_status)
                VALUES (:store_id, :user_id, :recon_date, :notes, :sync_id, :sync_status)
            """), {
                "store_id": store_id,
                "user_id": user_id,
                "recon_date": datetime.now(),
                "notes": notes,
                "sync_id": None,
                "sync_status": 'pending'
            })
            self.session.commit()
            reconciliation_id = result.lastrowid
            
            return True, "Reconciliation started", reconciliation_id
        except Exception as e:
            self.session.rollback()
            return False, f"Error starting reconciliation: {str(e)}", None

    def add_count(
        self,
        reconciliation_id: int,
        batch_id: int,
        counted_quantity: int,
        notes: str = ""
    ) -> tuple[bool, str]:
        """Add a counted quantity for a batch."""
        try:
            # Get current system quantity
            batch = self.inventory_service.get_batch(batch_id)
            if not batch:
                return False, "Batch not found"
            
            system_quantity = batch.get("quantity", 0)
            variance = counted_quantity - system_quantity
            
            # Insert reconciliation item
            self.session.execute(text("""
                INSERT INTO reconciliation_items
                (reconciliation_id, product_batch_id, system_quantity, 
                 counted_quantity, variance_quantity, sync_id, sync_status)
                VALUES (:recon_id, :batch_id, :sys_qty, :count_qty, :variance, :sync_id, :sync_status)
            """), {
                "recon_id": reconciliation_id,
                "batch_id": batch_id,
                "sys_qty": system_quantity,
                "count_qty": counted_quantity,
                "variance": variance,
                "sync_id": None,
                "sync_status": 'pending'
            })
            self.session.commit()
            
            return True, f"Count recorded. Variance: {variance}"
        except Exception as e:
            self.session.rollback()
            return False, f"Error recording count: {str(e)}"

    def get_reconciliation_items(self, reconciliation_id: int) -> List[dict]:
        """Get all items in a reconciliation."""
        try:
            result = self.session.execute(text("""
                SELECT 
                    ri.id,
                    ri.product_batch_id,
                    ri.system_quantity,
                    ri.counted_quantity,
                    ri.variance_quantity,
                    pb.batch_number,
                    p.name as product_name,
                    p.sku
                FROM reconciliation_items ri
                JOIN product_batches pb ON ri.product_batch_id = pb.id
                JOIN products p ON pb.product_id = p.id
                WHERE ri.reconciliation_id = :recon_id
                ORDER BY ABS(ri.variance_quantity) DESC
            """), {"recon_id": reconciliation_id})
            
            items = []
            for row in result:
                items.append({
                    "id": row[0],
                    "product_batch_id": row[1],
                    "system_quantity": row[2],
                    "counted_quantity": row[3],
                    "variance_quantity": row[4],
                    "batch_number": row[5],
                    "product_name": row[6],
                    "sku": row[7]
                })
            
            return items
        except Exception as e:
            print(f"Error getting reconciliation items: {e}")
            return []

    def complete_reconciliation(
        self, reconciliation_id: int, apply_adjustments: bool = True
    ) -> tuple[bool, str, dict]:
        """Complete reconciliation and optionally apply adjustments."""
        try:
            items = self.get_reconciliation_items(reconciliation_id)
            
            if not items:
                return False, "No items in reconciliation", {}
            
            total_variance_qty = sum(item["variance_quantity"] for item in items)
            items_with_variance = [item for item in items if item["variance_quantity"] != 0]
            
            # Apply adjustments if requested
            if apply_adjustments:
                for item in items_with_variance:
                    batch_id = item["product_batch_id"]
                    variance = item["variance_quantity"]
                    
                    # Update batch quantity
                    self.inventory_service.update_batch_quantity(
                        batch_id=batch_id,
                        quantity_change=variance,
                        change_type="reconciliation",
                        user_id=1,  # Should be passed from UI
                        notes=f"Reconciliation #{reconciliation_id}"
                    )
            
            # Update reconciliation record
            self.session.execute(text("""
                UPDATE inventory_reconciliations
                SET total_variance_qty = :variance
                WHERE id = :recon_id
            """), {"variance": total_variance_qty, "recon_id": reconciliation_id})
            self.session.commit()
            
            summary = {
                "total_items": len(items),
                "items_with_variance": len(items_with_variance),
                "total_variance": total_variance_qty,
                "adjustments_applied": apply_adjustments,
            }
            
            return True, "Reconciliation completed", summary
        except Exception as e:
            self.session.rollback()
            return False, f"Error completing reconciliation: {str(e)}", {}

    def get_variance_report(self, reconciliation_id: int) -> dict:
        """Generate variance report for reconciliation."""
        items = self.get_reconciliation_items(reconciliation_id)
        
        positive_variance = [i for i in items if i["variance_quantity"] > 0]
        negative_variance = [i for i in items if i["variance_quantity"] < 0]
        no_variance = [i for i in items if i["variance_quantity"] == 0]
        
        return {
            "reconciliation_id": reconciliation_id,
            "total_items": len(items),
            "items_with_positive_variance": len(positive_variance),
            "items_with_negative_variance": len(negative_variance),
            "items_with_no_variance": len(no_variance),
            "total_variance": sum(i["variance_quantity"] for i in items),
            "largest_positive": max(positive_variance, key=lambda x: x["variance_quantity"]) if positive_variance else None,
            "largest_negative": min(negative_variance, key=lambda x: x["variance_quantity"]) if negative_variance else None,
            "items": items,
        }

    def get_reconciliation_history(self, store_id: int, limit: int = 10) -> List[dict]:
        """Get reconciliation history for a store."""
        try:
            result = self.session.execute(text("""
                SELECT 
                    ir.id,
                    ir.reconciliation_date,
                    ir.total_variance_qty,
                    ir.notes,
                    u.username as reconciled_by,
                    COUNT(ri.id) as item_count
                FROM inventory_reconciliations ir
                LEFT JOIN users u ON ir.user_id = u.id
                LEFT JOIN reconciliation_items ri ON ir.id = ri.reconciliation_id
                WHERE ir.store_id = :store_id
                GROUP BY ir.id
                ORDER BY ir.reconciliation_date DESC
                LIMIT :limit
            """), {"store_id": store_id, "limit": limit})
            
            history = []
            for row in result:
                history.append({
                    "id": row[0],
                    "reconciliation_date": row[1],
                    "total_variance_qty": row[2],
                    "notes": row[3],
                    "reconciled_by": row[4],
                    "item_count": row[5]
                })
            
            return history
        except Exception as e:
            print(f"Error getting reconciliation history: {e}")
            return []

    def close(self) -> None:
        """Close database session."""
        self.session.close()


__all__ = [
    "BatchManager",
    "StockTransferManager",
    "InventoryAlerts",
    "ReconciliationManager",
]

