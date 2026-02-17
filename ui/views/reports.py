"""
PharmaPOS ERP - Reports View

Business intelligence and compliance reporting.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QHeaderView, QPushButton, QSpacerItem, QSizePolicy,
    QFrame, QGridLayout
)
from PyQt5.QtCore import Qt

from ..components.widgets import ERPCard
from ..styles.theme import Theme

class ReportsView(QWidget):
    """Modern reporting and analytics interface."""
    def __init__(self, report_service=None, parent=None):
        super().__init__(parent)
        self.report_service = report_service
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # 1. Headline
        headline = QLabel("Reports & Analytics")
        headline.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 20px; font-weight: 700;")
        layout.addWidget(headline)

        # 2. Report Selection Grid
        report_grid = QGridLayout()
        report_grid.setSpacing(16)
        
        def create_report_button(title, description, icon="📊"):
            card = ERPCard()
            card.setFixedHeight(120)
            card_layout = QVBoxLayout(card)
            
            t_label = QLabel(f"{icon} {title}")
            t_label.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 14px; font-weight: 700;")
            
            d_label = QLabel(description)
            d_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px;")
            d_label.setWordWrap(True)
            
            card_layout.addWidget(t_label)
            card_layout.addWidget(d_label)
            card_layout.addStretch()
            
            btn = QPushButton("Generate")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"background: {Theme.PRIMARY_LIGHT}; color: {Theme.PRIMARY}; border: none; padding: 4px; border-radius: 4px; font-weight: 600;")
            card_layout.addWidget(btn)
            return card

        report_grid.addWidget(create_report_button("Sales Summary", "Daily, weekly, and monthly sales performance."), 0, 0)
        report_grid.addWidget(create_report_button("Inventory Aging", "Insights into stock age and FEFO compliance."), 0, 1)
        report_grid.addWidget(create_report_button("Profit & Loss", "Calculated margins based on cost and selling prices."), 1, 0)
        report_grid.addWidget(create_report_button("Audit Trail", "Detailed history of all stock and price adjustments."), 1, 1)
        
        layout.addLayout(report_grid)
        layout.addStretch()
