"""
PharmaPOS NG - Analytics and Dashboard Metrics

Provides real-time analytics, statistics, and performance metrics for the dashboard.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import Session

from desktop_app.logger import get_logger

logger = get_logger(__name__)


class DashboardAnalytics:
    """Provides analytics and metrics for the dashboard."""
    
    def __init__(self, session: Session):
        """Initialize analytics service.
        
        Args:
            session: Database session
        """
        self.session = session
        logger.debug("DashboardAnalytics initialized")
    
    def get_today_sales_summary(self, store_id: Optional[int] = None) -> Dict[str, Any]:
        """Get today's sales summary.
        
        Args:
            store_id: Optional store filter
            
        Returns:
            Dictionary with sales metrics
        """
        try:
            from desktop_app.database import sales
            
            today = date.today()
            
            # Build query
            stmt = select(
                func.count(sales.c.id).label('transaction_count'),
                func.sum(sales.c.total_amount).label('total_sales'),
                func.avg(sales.c.total_amount).label('average_sale'),
            ).where(
                func.date(sales.c.created_at) == today
            )
            
            if store_id:
                stmt = stmt.where(sales.c.store_id == store_id)
            
            result = self.session.execute(stmt).fetchone()
            
            return {
                'transaction_count': result.transaction_count or 0,
                'total_sales': float(result.total_sales or 0),
                'average_sale': float(result.average_sale or 0),
                'total_profit': 0.0,  # Will be populated by separate query if needed
                'date': today.isoformat(),
            }
            
            # Calculate profit (requires joining with batches for cost)
            profit_stmt = select(
                func.sum((sale_items.c.unit_price - product_batches.c.cost_price) * sale_items.c.quantity).label('total_profit')
            ).select_from(
                sale_items.join(product_batches, sale_items.c.product_batch_id == product_batches.c.id)
                .join(sales, sales.c.id == sale_items.c.sale_id)
            ).where(
                func.date(sales.c.created_at) == today
            )
            
            if store_id:
                profit_stmt = profit_stmt.where(sales.c.store_id == store_id)
                
            profit_result = self.session.execute(profit_stmt).scalar()
            today_stats = {
                'transaction_count': result.transaction_count or 0,
                'total_sales': float(result.total_sales or 0),
                'average_sale': float(result.average_sale or 0),
                'total_profit': float(profit_result or 0),
                'date': today.isoformat(),
            }
            
            return today_stats
            
        except Exception as e:
            logger.error(f"Error getting today's sales summary: {e}", exc_info=True)
            return {
                'transaction_count': 0,
                'total_sales': 0.0,
                'average_sale': 0.0,
                'date': date.today().isoformat(),
            }
    
    def get_sales_trend(self, days: int = 7, store_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get sales trend for the last N days.
        
        Args:
            days: Number of days to include
            store_id: Optional store filter
            
        Returns:
            List of daily sales data
        """
        try:
            from desktop_app.database import sales
            
            start_date = date.today() - timedelta(days=days-1)
            
            stmt = select(
                func.date(sales.c.created_at).label('date'),
                func.count(sales.c.id).label('count'),
                func.sum(sales.c.total_amount).label('total'),
            ).where(
                func.date(sales.c.created_at) >= start_date
            ).group_by(
                func.date(sales.c.created_at)
            ).order_by(
                func.date(sales.c.created_at)
            )
            
            if store_id:
                stmt = stmt.where(sales.c.store_id == store_id)
            
            results = self.session.execute(stmt).fetchall()
            
            return [
                {
                    'date': str(row.date) if row.date else '',
                    'count': row.count or 0,
                    'total': float(row.total or 0),
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting sales trend: {e}", exc_info=True)
            return []
    
    def get_top_selling_products(self, limit: int = 10, store_id: Optional[int] = None, days: int = 30) -> List[Dict[str, Any]]:
        """Get top selling products.
        
        Args:
            limit: Number of products to return
            store_id: Optional store filter
            days: Number of days to analyze
            
        Returns:
            List of top products with sales data
        """
        try:
            from desktop_app.database import sale_items, product_batches, products
            
            start_date = date.today() - timedelta(days=days)
            
            stmt = select(
                products.c.id,
                products.c.name,
                products.c.sku,
                func.sum(sale_items.c.quantity).label('total_quantity'),
                func.sum(sale_items.c.quantity * sale_items.c.unit_price).label('total_revenue'),
                func.count(sale_items.c.id).label('transaction_count'),
            ).select_from(
                sale_items.join(
                    product_batches,
                    sale_items.c.product_batch_id == product_batches.c.id
                ).join(
                    products,
                    product_batches.c.product_id == products.c.id
                )
            ).where(
                func.date(sale_items.c.created_at) >= start_date
            ).group_by(
                products.c.id,
                products.c.name,
                products.c.sku
            ).order_by(
                desc('total_quantity')
            ).limit(limit)
            
            if store_id:
                stmt = stmt.where(product_batches.c.store_id == store_id)
            
            results = self.session.execute(stmt).fetchall()
            
            return [
                {
                    'product_id': row.id,
                    'product_name': row.name,
                    'sku': row.sku,
                    'quantity_sold': row.total_quantity or 0,
                    'revenue': float(row.total_revenue or 0),
                    'transactions': row.transaction_count or 0,
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting top selling products: {e}", exc_info=True)
            return []
    
    def get_employee_sales_ranking(self, limit: int = 10, store_id: Optional[int] = None, days: int = 30) -> List[Dict[str, Any]]:
        """Get employee sales ranking.
        
        Args:
            limit: Number of employees to return
            store_id: Optional store filter
            days: Number of days to analyze
            
        Returns:
            List of employees ranked by sales performance
        """
        try:
            from desktop_app.database import sales, users
            
            start_date = date.today() - timedelta(days=days)
            
            stmt = select(
                users.c.id,
                users.c.username,
                users.c.role,
                func.count(sales.c.id).label('transaction_count'),
                func.sum(sales.c.total_amount).label('total_sales'),
                func.avg(sales.c.total_amount).label('average_sale'),
            ).select_from(
                sales.join(users, sales.c.user_id == users.c.id)
            ).where(
                func.date(sales.c.created_at) >= start_date
            ).group_by(
                users.c.id,
                users.c.username,
                users.c.role
            ).order_by(
                desc('total_sales')
            ).limit(limit)
            
            if store_id:
                stmt = stmt.where(sales.c.store_id == store_id)
            
            results = self.session.execute(stmt).fetchall()
            
            return [
                {
                    'user_id': row.id,
                    'username': row.username,
                    'role': row.role,
                    'transaction_count': row.transaction_count or 0,
                    'total_sales': float(row.total_sales or 0),
                    'average_sale': float(row.average_sale or 0),
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting employee sales ranking: {e}", exc_info=True)
            return []
    
    def get_low_stock_alert(self, store_id: Optional[int] = None, threshold: int = 10) -> List[Dict[str, Any]]:
        """Get products with low stock.
        
        Args:
            store_id: Optional store filter
            threshold: Stock level threshold
            
        Returns:
            List of low stock products
        """
        try:
            from desktop_app.database import product_batches, products
            
            stmt = select(
                products.c.id,
                products.c.name,
                products.c.sku,
                func.sum(product_batches.c.quantity).label('total_stock'),
                products.c.min_stock,
                products.c.reorder_level,
            ).select_from(
                product_batches.join(
                    products,
                    product_batches.c.product_id == products.c.id
                )
            ).where(
                product_batches.c.quantity > 0
            ).group_by(
                products.c.id,
                products.c.name,
                products.c.sku,
                products.c.min_stock,
                products.c.reorder_level
            ).having(
                func.sum(product_batches.c.quantity) <= threshold
            ).order_by(
                'total_stock'
            )
            
            if store_id:
                stmt = stmt.where(product_batches.c.store_id == store_id)
            
            results = self.session.execute(stmt).fetchall()
            
            return [
                {
                    'product_id': row.id,
                    'product_name': row.name,
                    'sku': row.sku,
                    'current_stock': row.total_stock or 0,
                    'min_stock': row.min_stock or 0,
                    'reorder_level': row.reorder_level or 0,
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting low stock alert: {e}", exc_info=True)
            return []
    
    def get_expiring_products(self, store_id: Optional[int] = None, days: int = 30) -> List[Dict[str, Any]]:
        """Get products expiring soon.
        
        Args:
            store_id: Optional store filter
            days: Days until expiry threshold
            
        Returns:
            List of expiring products
        """
        try:
            from desktop_app.database import product_batches, products
            
            expiry_date = date.today() + timedelta(days=days)
            
            stmt = select(
                products.c.id,
                products.c.name,
                products.c.sku,
                product_batches.c.batch_number,
                product_batches.c.quantity,
                product_batches.c.expiry_date,
            ).select_from(
                product_batches.join(
                    products,
                    product_batches.c.product_id == products.c.id
                )
            ).where(
                and_(
                    product_batches.c.expiry_date <= expiry_date,
                    product_batches.c.expiry_date >= date.today(),
                    product_batches.c.quantity > 0
                )
            ).order_by(
                product_batches.c.expiry_date
            )
            
            if store_id:
                stmt = stmt.where(product_batches.c.store_id == store_id)
            
            results = self.session.execute(stmt).fetchall()
            
            return [
                {
                    'product_id': row.id,
                    'product_name': row.name,
                    'sku': row.sku,
                    'batch_number': row.batch_number,
                    'quantity': row.quantity or 0,
                    'expiry_date': row.expiry_date.isoformat() if row.expiry_date else '',
                    'days_until_expiry': (row.expiry_date - date.today()).days if row.expiry_date else 0,
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting expiring products: {e}", exc_info=True)
            return []
    
    def get_inventory_value(self, store_id: Optional[int] = None) -> Dict[str, Any]:
        """Get total inventory value.
        
        Args:
            store_id: Optional store filter
            
        Returns:
            Dictionary with inventory metrics
        """
        try:
            from desktop_app.database import product_batches
            
            stmt = select(
                func.sum(product_batches.c.quantity * product_batches.c.cost_price).label('total_value'),
                func.sum(product_batches.c.quantity).label('total_units'),
                func.count(func.distinct(product_batches.c.product_id)).label('unique_products'),
            ).where(
                product_batches.c.quantity > 0
            )
            
            if store_id:
                stmt = stmt.where(product_batches.c.store_id == store_id)
            
            result = self.session.execute(stmt).fetchone()
            
            return {
                'total_value': float(result.total_value or 0),
                'total_units': result.total_units or 0,
                'unique_products': result.unique_products or 0,
            }
            
        except Exception as e:
            logger.error(f"Error getting inventory value: {e}", exc_info=True)
            return {
                'total_value': 0.0,
                'total_units': 0,
                'unique_products': 0,
            }
            
    def get_profit_analysis(self, store_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """Get profit analysis metrics.
        
        Args:
            store_id: Optional store filter
            days: Analysis period
            
        Returns:
            Dictionary with profit metrics and margins
        """
        try:
            from desktop_app.database import sale_items, product_batches, sales
            
            start_date = date.today() - timedelta(days=days)
            
            # Calculate total revenue and total cost
            stmt = select(
                func.sum(sale_items.c.quantity * sale_items.c.unit_price).label('revenue'),
                func.sum(sale_items.c.quantity * product_batches.c.cost_price).label('cost')
            ).select_from(
                sale_items.join(product_batches, sale_items.c.product_batch_id == product_batches.c.id)
                .join(sales, sales.c.id == sale_items.c.sale_id)
            ).where(
                func.date(sales.c.created_at) >= start_date
            )
            
            if store_id:
                stmt = stmt.where(sales.c.store_id == store_id)
                
            result = self.session.execute(stmt).fetchone()
            
            revenue = float(result.revenue or 0)
            cost = float(result.cost or 0)
            profit = revenue - cost
            margin = (profit / revenue * 100) if revenue > 0 else 0
            
            return {
                'total_revenue': revenue,
                'total_cost': cost,
                'gross_profit': profit,
                'profit_margin_percent': round(margin, 2),
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error calculating profit analysis: {e}")
            return {
                'total_revenue': 0.0,
                'total_cost': 0.0,
                'gross_profit': 0.0,
                'profit_margin_percent': 0.0,
                'period_days': days
            }
    
    def get_dashboard_summary(self, store_id: Optional[int] = None) -> Dict[str, Any]:
        """Get complete dashboard summary with all metrics.
        
        Args:
            store_id: Optional store filter
            
        Returns:
            Dictionary with all dashboard metrics
        """
        try:
            return {
                'today_sales': self.get_today_sales_summary(store_id),
                'profit_analysis': self.get_profit_analysis(store_id, 30),
                'sales_trend': self.get_sales_trend(7, store_id),
                'top_products': self.get_top_selling_products(5, store_id, 30),
                'employee_ranking': self.get_employee_sales_ranking(5, store_id, 30),
                'low_stock': self.get_low_stock_alert(store_id, 10),
                'expiring_soon': self.get_expiring_products(store_id, 30),
                'inventory_value': self.get_inventory_value(store_id),
                'generated_at': datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard summary: {e}", exc_info=True)
            return {}


__all__ = ['DashboardAnalytics']
