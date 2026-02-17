"""
PharmaPOS NG - Analytics Service

Provides real-time analytics, statistics, and performance metrics for the dashboard.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from .base_service import BaseService


class AnalyticsService(BaseService):
    """Provides analytics and metrics for the dashboard."""

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize analytics service.
        
        Args:
            session: SQLAlchemy database session
        """
        super().__init__(session)

    def get_today_sales_summary(self, store_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get today's sales summary.
        
        Args:
            store_id: Optional store filter
            
        Returns:
            Dictionary with sales metrics
        """
        from desktop_app.analytics import DashboardAnalytics
        
        analytics = DashboardAnalytics(self.session)
        return analytics.get_today_sales_summary(store_id)

    def get_sales_trend(self, days: int = 7, store_id: Optional[int] = None) -> List[Dict]:
        """
        Get sales trend for the last N days.
        
        Args:
            days: Number of days to include
            store_id: Optional store filter
            
        Returns:
            List of daily sales data
        """
        from desktop_app.analytics import DashboardAnalytics
        
        analytics = DashboardAnalytics(self.session)
        return analytics.get_sales_trend(days, store_id)

    def get_top_selling_products(
        self, limit: int = 10, store_id: Optional[int] = None, days: int = 30
    ) -> List[Dict]:
        """
        Get top selling products.
        
        Args:
            limit: Number of products to return
            store_id: Optional store filter
            days: Number of days to analyze
            
        Returns:
            List of top products with sales data
        """
        from desktop_app.analytics import DashboardAnalytics
        
        analytics = DashboardAnalytics(self.session)
        return analytics.get_top_selling_products(limit, store_id, days)

    def get_employee_sales_ranking(
        self, limit: int = 10, store_id: Optional[int] = None, days: int = 30
    ) -> List[Dict]:
        """
        Get employee sales ranking.
        
        Args:
            limit: Number of employees to return
            store_id: Optional store filter
            days: Number of days to analyze
            
        Returns:
            List of employees ranked by sales performance
        """
        from desktop_app.analytics import DashboardAnalytics
        
        analytics = DashboardAnalytics(self.session)
        return analytics.get_employee_sales_ranking(limit, store_id, days)

    def get_low_stock_alert(
        self, store_id: Optional[int] = None, threshold: int = 10
    ) -> List[Dict]:
        """
        Get products with low stock.
        
        Args:
            store_id: Optional store filter
            threshold: Stock level threshold
            
        Returns:
            List of low stock products
        """
        from desktop_app.analytics import DashboardAnalytics
        
        analytics = DashboardAnalytics(self.session)
        return analytics.get_low_stock_alert(store_id, threshold)

    def get_expiring_products(
        self, store_id: Optional[int] = None, days: int = 30
    ) -> List[Dict]:
        """
        Get products expiring soon.
        
        Args:
            store_id: Optional store filter
            days: Days until expiry threshold
            
        Returns:
            List of expiring products
        """
        from desktop_app.analytics import DashboardAnalytics
        
        analytics = DashboardAnalytics(self.session)
        return analytics.get_expiring_products(store_id, days)

    def get_inventory_value(self, store_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get total inventory value.
        
        Args:
            store_id: Optional store filter
            
        Returns:
            Dictionary with inventory metrics
        """
        from desktop_app.analytics import DashboardAnalytics
        
        analytics = DashboardAnalytics(self.session)
        return analytics.get_inventory_value(store_id)

    def get_profit_analysis(
        self, store_id: Optional[int] = None, days: int = 30
    ) -> Dict[str, Any]:
        """
        Get profit analysis metrics.
        
        Args:
            store_id: Optional store filter
            days: Analysis period
            
        Returns:
            Dictionary with profit metrics and margins
        """
        from desktop_app.analytics import DashboardAnalytics
        
        analytics = DashboardAnalytics(self.session)
        return analytics.get_profit_analysis(store_id, days)

    def get_dashboard_summary(self, store_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get complete dashboard summary with all metrics.
        
        Args:
            store_id: Optional store filter
            
        Returns:
            Dictionary with all dashboard metrics
        """
        from desktop_app.analytics import DashboardAnalytics
        
        analytics = DashboardAnalytics(self.session)
        return analytics.get_dashboard_summary(store_id)


__all__ = ["AnalyticsService"]
