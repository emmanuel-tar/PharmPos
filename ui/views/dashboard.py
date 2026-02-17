"""
PharmaPOS ERP - Dashboard View

The primary analytics and overview screen.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QGridLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt

from ..components.widgets import MetricCard, ERPCard
from ..styles.theme import Theme

class DashboardView(QWidget):
    """Redesigned ERP Dashboard."""
    def __init__(self, analytics_service=None, parent=None):
        super().__init__(parent)
        self.analytics_service = analytics_service
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # 1. Headline
        headline = QLabel("Welcome back, Admin")
        headline.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 20px; font-weight: 700;")
        layout.addWidget(headline)

        # 2. KPI Metrics Row
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(16)
        
        self.sales_card = MetricCard("Today's Sales", "₦0.00", "↑ 12% from yesterday", Theme.SUCCESS)
        self.orders_card = MetricCard("Total Orders", "0", "Daily target: 50")
        self.inventory_card = MetricCard("Stock Value", "₦0.00", "Across 2 branches", Theme.INFO)
        self.expiry_card = MetricCard("Expiring Soon", "0", "Requires attention", Theme.DANGER)
        
        metrics_layout.addWidget(self.sales_card)
        metrics_layout.addWidget(self.orders_card)
        metrics_layout.addWidget(self.inventory_card)
        metrics_layout.addWidget(self.expiry_card)
        
        layout.addLayout(metrics_layout)

        # 3. Main Content Grid (Charts & Tables)
        content_grid = QGridLayout()
        content_grid.setSpacing(24)

        # Sales Trend placeholder card
        trend_card = ERPCard()
        trend_layout = trend_card.set_layout(QVBoxLayout())
        trend_layout.addWidget(QLabel("Sales Trend Chart Placeholder"))
        trend_card.setMinimumHeight(350)
        content_grid.addWidget(trend_card, 0, 0, 1, 2) # Span 2 columns

        # Stock Alerts placeholder card
        alerts_card = ERPCard()
        alerts_layout = alerts_card.set_layout(QVBoxLayout())
        alerts_layout.addWidget(QLabel("Inventory Alerts Placeholder"))
        content_grid.addWidget(alerts_card, 1, 0)

        # Top Products placeholder card
        top_products_card = ERPCard()
        product_layout = top_products_card.set_layout(QVBoxLayout())
        product_layout.addWidget(QLabel("Top Selling Products Placeholder"))
        content_grid.addWidget(top_products_card, 1, 1)

        layout.addLayout(content_grid)
        layout.addStretch()

    def refresh_data(self):
        """Update metrics from analytics service."""
        # TODO: Integration with analytics_service
        pass
