"""
PharmaPOS NG - Reporting & Analytics

This module generates comprehensive reports for sales, inventory, and business analytics.
"""

from __future__ import annotations

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import select, func, and_

from desktop_app.database import (
    get_engine,
    sales,
    sale_items,
    products,
    product_batches,
    inventory_audit,
)
from desktop_app.models import (
    SalesService,
    InventoryService,
    ProductService,
    get_session,
)


# --- Sales Reports -----------------------------------------------------------
class SalesReporter:
    """Generates sales reports and analytics."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.session = get_session(db_path)
        self.sales_service = SalesService(self.session)

    def get_daily_sales(self, store_id: int, report_date: date) -> dict:
        """Get sales summary for a specific day."""
        from datetime import timedelta

        start = datetime.combine(report_date, datetime.min.time())
        end = datetime.combine(report_date + timedelta(days=1), datetime.min.time())

        engine = get_engine(self.db_path)
        with engine.connect() as conn:
            stmt = select(
                func.count(sales.c.id).label("transaction_count"),
                func.sum(sales.c.total_amount).label("total_revenue"),
                func.sum(sales.c.change_amount).label("total_change"),
            ).where(
                and_(
                    sales.c.store_id == store_id,
                    sales.c.created_at >= start,
                    sales.c.created_at < end,
                )
            )

            result = conn.execute(stmt).fetchone()

        if not result:
            return {
                "date": report_date.isoformat(),
                "transaction_count": 0,
                "total_revenue": 0.0,
                "average_transaction": 0.0,
            }

        transaction_count = result[0] or 0
        total_revenue = float(result[1] or 0)
        average = total_revenue / transaction_count if transaction_count > 0 else 0

        return {
            "date": report_date.isoformat(),
            "transaction_count": transaction_count,
            "total_revenue": total_revenue,
            "average_transaction": average,
        }

    def get_period_sales(
        self, store_id: int, start_date: date, end_date: date
    ) -> dict:
        """Get sales summary for a date range."""
        sales_list = self.sales_service.get_sales_by_date(store_id, start_date, end_date)

        if not sales_list:
            return {
                "period": f"{start_date} to {end_date}",
                "transaction_count": 0,
                "total_revenue": 0.0,
                "by_payment_method": {},
            }

        total_revenue = sum(Decimal(str(s["total_amount"])) for s in sales_list)
        
        # Group by payment method
        by_method = {}
        for sale in sales_list:
            method = sale["payment_method"]
            if method not in by_method:
                by_method[method] = {"count": 0, "amount": 0.0}
            by_method[method]["count"] += 1
            by_method[method]["amount"] += float(sale["total_amount"])

        return {
            "period": f"{start_date} to {end_date}",
            "transaction_count": len(sales_list),
            "total_revenue": float(total_revenue),
            "by_payment_method": by_method,
        }

    def get_top_selling_products(
        self, store_id: int, start_date: date, end_date: date, limit: int = 10
    ) -> List[dict]:
        """Get top selling products in period."""
        engine = get_engine(self.db_path)
        
        with engine.connect() as conn:
            stmt = (
                select(
                    products.c.name,
                    products.c.sku,
                    func.sum(sale_items.c.quantity).label("total_qty"),
                    func.sum(
                        sale_items.c.quantity * sale_items.c.unit_price
                    ).label("total_value"),
                )
                .select_from(sale_items)
                .join(product_batches)
                .join(products)
                .join(sales)
                .where(
                    and_(
                        sales.c.store_id == store_id,
                        sales.c.created_at >= datetime.combine(start_date, datetime.min.time()),
                        sales.c.created_at < datetime.combine(end_date + timedelta(days=1), datetime.min.time()),
                    )
                )
                .group_by(products.c.id, products.c.name, products.c.sku)
                .order_by(func.sum(sale_items.c.quantity).desc())
                .limit(limit)
            )

            results = conn.execute(stmt).fetchall()

        return [
            {
                "product_name": row[0],
                "sku": row[1],
                "quantity_sold": row[2],
                "revenue": float(row[3] or 0),
            }
            for row in results
        ]

    def close(self) -> None:
        """Close database session."""
        self.session.close()


# --- Inventory Reports -------------------------------------------------------
class InventoryReporter:
    """Generates inventory reports and analytics."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.session = get_session(db_path)
        self.inventory_service = InventoryService(self.session)
        self.product_service = ProductService(self.session)

    def get_stock_valuation(self, store_id: int) -> dict:
        """Get total inventory value and quantity."""
        inventory = self.inventory_service.get_store_inventory(store_id)

        total_quantity = sum(batch["quantity"] for batch in inventory)
        total_value = sum(
            batch["quantity"] * (batch["cost_price"] or 0)
            for batch in inventory
        )

        return {
            "store_id": store_id,
            "total_items_in_stock": total_quantity,
            "total_inventory_value": float(total_value),
            "batch_count": len(inventory),
            "reported_at": datetime.now().isoformat(),
        }

    def get_inventory_by_category(self, store_id: int) -> dict:
        """Get inventory grouped by product category."""
        inventory = self.inventory_service.get_store_inventory(store_id)

        # Group by product (simplified - in real system would use product categories)
        by_product = {}
        for batch in inventory:
            product_id = batch["product_id"]
            if product_id not in by_product:
                product = self.product_service.get_product(product_id)
                product_name = product["name"] if product else f"Product {product_id}"
                by_product[product_id] = {
                    "name": product_name,
                    "total_quantity": 0,
                    "total_value": 0.0,
                }
            by_product[product_id]["total_quantity"] += batch["quantity"]
            by_product[product_id]["total_value"] += float(
                batch["quantity"] * (batch["cost_price"] or 0)
            )

        return {
            "store_id": store_id,
            "categories": list(by_product.values()),
            "reported_at": datetime.now().isoformat(),
        }

    def get_batch_aging_report(self, store_id: int) -> dict:
        """Get report on batch ages."""
        inventory = self.inventory_service.get_store_inventory(store_id)
        today = datetime.now().date()

        aging = {
            "0_to_30_days": [],
            "31_to_60_days": [],
            "61_to_90_days": [],
            "over_90_days": [],
        }

        for batch in inventory:
            age = (today - batch["received_date"].date()).days

            if age <= 30:
                key = "0_to_30_days"
            elif age <= 60:
                key = "31_to_60_days"
            elif age <= 90:
                key = "61_to_90_days"
            else:
                key = "over_90_days"

            aging[key].append({
                "batch_id": batch["id"],
                "batch_number": batch["batch_number"],
                "quantity": batch["quantity"],
                "age_days": age,
                "expiry_date": batch["expiry_date"].isoformat(),
            })

        return {
            "store_id": store_id,
            "batch_aging": aging,
            "reported_at": datetime.now().isoformat(),
        }

    def close(self) -> None:
        """Close database session."""
        self.session.close()


# --- Audit Reports -----------------------------------------------------------
class AuditReporter:
    """Generates audit trail reports."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.session = get_session(db_path)

    def get_batch_audit_trail(self, batch_id: int) -> List[dict]:
        """Get complete audit trail for a batch."""
        engine = get_engine(self.db_path)
        
        with engine.connect() as conn:
            stmt = (
                select(inventory_audit)
                .where(inventory_audit.c.product_batch_id == batch_id)
                .order_by(inventory_audit.c.created_at.desc())
            )
            results = conn.execute(stmt).fetchall()

        return [
            {
                "id": row[0],
                "previous_qty": row[2],
                "new_qty": row[3],
                "change_type": row[4],
                "reference_id": row[5],
                "notes": row[6],
                "user_id": row[7],
                "timestamp": row[8].isoformat(),
            }
            for row in results
        ]

    def get_period_audit(self, start_date: date, end_date: date) -> List[dict]:
        """Get audit entries for a date range."""
        engine = get_engine(self.db_path)
        
        with engine.connect() as conn:
            stmt = (
                select(inventory_audit)
                .where(
                    and_(
                        inventory_audit.c.created_at >= datetime.combine(start_date, datetime.min.time()),
                        inventory_audit.c.created_at < datetime.combine(end_date + timedelta(days=1), datetime.min.time()),
                    )
                )
                .order_by(inventory_audit.c.created_at.desc())
            )
            results = conn.execute(stmt).fetchall()

        return [
            {
                "batch_id": row[1],
                "previous_qty": row[2],
                "new_qty": row[3],
                "change_type": row[4],
                "timestamp": row[8].isoformat(),
            }
            for row in results
        ]

    def close(self) -> None:
        """Close database session."""
        self.session.close()


__all__ = [
    "SalesReporter",
    "InventoryReporter",
    "AuditReporter",
]
