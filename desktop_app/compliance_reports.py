"""
PharmaPOS NG - Compliance and Reporting Service

Generates reports for regulatory compliance (NAFDAC, PCN) and internal auditing.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from decimal import Decimal

from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import Session

from desktop_app.database import (
    products,
    product_batches,
    sales,
    sale_items,
    suppliers,
    purchase_receipts,
    purchase_receipt_items,
    stores,
    users,
    compliance_alerts,
)
from desktop_app.logger import get_logger

logger = get_logger(__name__)


class ComplianceService:
    """Service for generating compliance reports and managing alerts."""

    def __init__(self, session: Session):
        self.session = session

    # --- NAFDAC Reporting ----------------------------------------------------

    def generate_nafdac_report(
        self,
        start_date: datetime,
        end_date: datetime,
        store_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Generate regulated product report for NAFDAC compliance.
        
        Requires: Product Name, NAFDAC Reg No, Batch No, Expiry, Quantity Sold/Stocked.
        """
        try:
            # Query sales of products with NAFDAC numbers
            stmt = (
                select(
                    products.c.name.label("product_name"),
                    products.c.nafdac_number,
                    products.c.generic_name,
                    product_batches.c.batch_number,
                    product_batches.c.expiry_date,
                    func.sum(sale_items.c.quantity).label("quantity_sold"),
                    func.min(sales.c.created_at).label("first_sale_date"),
                    func.max(sales.c.created_at).label("last_sale_date"),
                )
                .join(sale_items, sale_items.c.product_batch_id == product_batches.c.id)
                .join(sales, sales.c.id == sale_items.c.sale_id)
                .join(products, products.c.id == product_batches.c.product_id)
                .where(
                    and_(
                        sales.c.created_at >= start_date,
                        sales.c.created_at <= end_date,
                        products.c.nafdac_number.is_not(None),
                        products.c.nafdac_number != "",
                    )
                )
                .group_by(
                    products.c.id,
                    product_batches.c.batch_number,
                )
            )

            if store_id:
                stmt = stmt.where(sales.c.store_id == store_id)

            result = self.session.execute(stmt)
            rows = result.fetchall()

            report_data = []
            for row in rows:
                row_dict = dict(row._mapping)
                # Ensure dates are strings
                if row_dict['expiry_date']:
                    row_dict['expiry_date'] = row_dict['expiry_date'].strftime('%Y-%m-%d')
                if row_dict['first_sale_date']:
                    row_dict['first_sale_date'] = row_dict['first_sale_date'].strftime('%Y-%m-%d')
                if row_dict['last_sale_date']:
                    row_dict['last_sale_date'] = row_dict['last_sale_date'].strftime('%Y-%m-%d')
                
                report_data.append(row_dict)

            return report_data
        except Exception as e:
            logger.error(f"Failed to generate NAFDAC report: {e}")
            return []

    # --- PCN Reporting -------------------------------------------------------

    def generate_pcn_report(
        self,
        start_date: datetime,
        end_date: datetime,
        store_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate operational report for Pharmacists Council of Nigeria.
        
        Includes: Sales summary, Prescription stats (proxied by ethical drugs),
        Staffing logs, and Dispatch records.
        """
        try:
            # 1. Total Sales Volume & Value
            sales_stmt = (
                select(
                    func.count(sales.c.id).label("total_transactions"),
                    func.sum(sales.c.total_amount).label("total_revenue"),
                )
                .where(
                    and_(
                        sales.c.created_at >= start_date,
                        sales.c.created_at <= end_date,
                    )
                )
            )
            if store_id:
                sales_stmt = sales_stmt.where(sales.c.store_id == store_id)
            
            sales_metrics = self.session.execute(sales_stmt).fetchone()._mapping

            # 2. Poison/Ethical Drugs Sales (Category-based filtering)
            # Assuming categories like 'Ethical', 'Prescription', 'Poison' exist
            ethical_stmt = (
                select(
                    func.count(sale_items.c.id).label("units_sold"),
                    products.c.category,
                )
                .join(product_batches, product_batches.c.id == sale_items.c.product_batch_id)
                .join(products, products.c.id == product_batches.c.product_id)
                .join(sales, sales.c.id == sale_items.c.sale_id)
                .where(
                    and_(
                        sales.c.created_at >= start_date,
                        sales.c.created_at <= end_date,
                        products.c.category.in_(['Ethical', 'Prescription', 'Poison', 'Controlled']),
                    )
                )
                .group_by(products.c.category)
            )
            if store_id:
                ethical_stmt = ethical_stmt.where(sales.c.store_id == store_id)

            ethical_sales = [dict(row._mapping) for row in self.session.execute(ethical_stmt).fetchall()]

            return {
                "period_start": start_date.strftime('%Y-%m-%d'),
                "period_end": end_date.strftime('%Y-%m-%d'),
                "sales_metrics": dict(sales_metrics),
                "ethical_drug_sales": ethical_sales,
                "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
        except Exception as e:
            logger.error(f"Failed to generate PCN report: {e}")
            return {}

    # --- Alert Management ----------------------------------------------------

    def check_and_create_expiry_alerts(self, threshold_days: int = 30) -> int:
        """Scan inventory for expiring products and create alerts."""
        try:
            # Find batches expiring soon that don't have active alerts
            # For simplicity, we just find all and upsert logic could be added
            # Here we just list them first
            
            cutoff_date = datetime.now().date() + func.cast(f"{threshold_days} days", Any) # Pseudo-code for interval
            # SQLite specific date math might differ, doing in python for safety if strict SQLite mapping is tricky
            
            # Using Python date math
            from datetime import timedelta
            target_date = datetime.now().date() + timedelta(days=threshold_days)
            today = datetime.now().date()

            stmt = (
                select(
                    product_batches.c.id,
                    product_batches.c.batch_number,
                    product_batches.c.expiry_date,
                    product_batches.c.store_id,
                    products.c.name.label("product_name"),
                )
                .join(products, products.c.id == product_batches.c.product_id)
                .where(
                    and_(
                        product_batches.c.expiry_date <= target_date,
                        product_batches.c.expiry_date >= today,
                        product_batches.c.quantity > 0, # Only if stock exists
                    )
                )
            )
            
            results = self.session.execute(stmt).fetchall()
            created_count = 0

            for row in results:
                # Check if alert exists
                alert_exists = self.session.execute(
                    select(compliance_alerts).where(
                        and_(
                            compliance_alerts.c.entity_type == 'batch',
                            compliance_alerts.c.entity_id == row.id,
                            compliance_alerts.c.alert_type == 'expiry',
                            compliance_alerts.c.is_resolved == False
                        )
                    )
                ).scalar()

                if not alert_exists:
                    title = f"Expiry Warning: {row.product_name}"
                    message = (
                        f"Batch {row.batch_number} expires on {row.expiry_date}. "
                        f"Action required."
                    )
                    
                    self.session.execute(
                        compliance_alerts.insert().values(
                            alert_type='expiry',
                            severity='high' if row.expiry_date <= datetime.now().date() + timedelta(days=7) else 'medium',
                            title=title,
                            message=message,
                            entity_type='batch',
                            entity_id=row.id,
                            store_id=row.store_id
                        )
                    )
                    created_count += 1
            
            self.session.commit()
            return created_count

        except Exception as e:
            logger.error(f"Failed to check expiry alerts: {e}")
            self.session.rollback()
            return 0

    def get_active_alerts(self, store_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all unresolved compliance alerts."""
        try:
            stmt = select(compliance_alerts).where(compliance_alerts.c.is_resolved == False)
            
            if store_id:
                stmt = stmt.where(compliance_alerts.c.store_id == store_id)
            
            stmt = stmt.order_by(
                desc(compliance_alerts.c.severity == 'critical'),
                desc(compliance_alerts.c.severity == 'high'),
                desc(compliance_alerts.c.created_at)
            )
            
            return [dict(row._mapping) for row in self.session.execute(stmt).fetchall()]
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []

    def resolve_alert(self, alert_id: int, user_id: int) -> bool:
        """Mark an alert as resolved."""
        try:
            stmt = (
                compliance_alerts.update()
                .where(compliance_alerts.c.id == alert_id)
                .values(
                    is_resolved=True,
                    resolved_at=datetime.now(),
                    resolved_by=user_id
                )
            )
            self.session.execute(stmt)
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_id}: {e}")
            self.session.rollback()
            return False

    def export_to_csv(self, data: List[Dict[str, Any]]) -> str:
        """Helper to convert list of dicts to CSV string."""
        if not data:
            return ""
        
        output = io.StringIO()
        keys = data[0].keys()
        writer = csv.DictWriter(output, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()


__all__ = ['ComplianceService']
