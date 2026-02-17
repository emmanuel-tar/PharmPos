"""
PharmaPOS NG - Report Service

This module generates comprehensive reports for sales, inventory, and business analytics.
"""

from __future__ import annotations

from datetime import date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from .base_service import BaseService


class ReportService(BaseService):
    """Service for generating business reports."""

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize report service.
        
        Args:
            session: SQLAlchemy database session
        """
        super().__init__(session)
        # Note: existing reporters use db_path, but we want to move towards using session.
        # For now, we'll maintain compatibility if needed, but primary focus is session-based.

    def get_daily_sales_report(self, store_id: int, report_date: date) -> dict:
        """Get daily sales summary."""
        from desktop_app.reports import SalesReporter
        
        reporter = SalesReporter()
        reporter.session = self.session
        try:
            return reporter.get_daily_sales(store_id, report_date)
        finally:
            # We don't want reporter.close() to close our session if it's shared.
            # But the existing reporter.close() ONLY closes self.session.
            pass

    def get_period_sales_report(self, store_id: int, start_date: date, end_date: date) -> dict:
        """Get sales summary for a date range."""
        from desktop_app.reports import SalesReporter
        
        reporter = SalesReporter()
        reporter.session = self.session
        return reporter.get_period_sales(store_id, start_date, end_date)

    def get_top_selling_products(self, store_id: int, start_date: date, end_date: date, limit: int = 10) -> List[dict]:
        """Get top selling products in period."""
        from desktop_app.reports import SalesReporter
        
        reporter = SalesReporter()
        reporter.session = self.session
        return reporter.get_top_selling_products(store_id, start_date, end_date, limit)

    def get_stock_valuation_report(self, store_id: int) -> dict:
        """Get total inventory valuation."""
        from desktop_app.reports import InventoryReporter
        
        reporter = InventoryReporter()
        reporter.session = self.session
        return reporter.get_stock_valuation(store_id)

    def get_inventory_category_report(self, store_id: int) -> dict:
        """Get inventory grouped by category."""
        from desktop_app.reports import InventoryReporter
        
        reporter = InventoryReporter()
        reporter.session = self.session
        return reporter.get_inventory_by_category(store_id)

    def get_batch_aging_report(self, store_id: int) -> dict:
        """Get report on batch ages."""
        from desktop_app.reports import InventoryReporter
        
        reporter = InventoryReporter()
        reporter.session = self.session
        return reporter.get_batch_aging_report(store_id)

    def get_batch_audit_trail(self, batch_id: int) -> List[dict]:
        """Get complete audit trail for a batch."""
        from desktop_app.reports import AuditReporter
        
        reporter = AuditReporter()
        reporter.session = self.session
        return reporter.get_batch_audit_trail(batch_id)

    def get_period_audit_report(self, start_date: date, end_date: date) -> List[dict]:
        """Get audit entries for a date range."""
        from desktop_app.reports import AuditReporter
        
        reporter = AuditReporter()
        reporter.session = self.session
        return reporter.get_period_audit(start_date, end_date)


__all__ = ["ReportService"]
