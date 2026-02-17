"""
PharmaPOS ERP - Customers View

Manage customer profiles, credit history, and purchase loyalty.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QHeaderView, QPushButton, QSpacerItem, QSizePolicy,
    QFrame, QLineEdit
)
from PyQt5.QtCore import Qt

from ..components.widgets import ERPCard, MetricCard
from ..styles.theme import Theme

class CustomersView(QWidget):
    """Modern customer management interface."""
    def __init__(self, customer_service=None, parent=None):
        super().__init__(parent)
        self.customer_service = customer_service
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # 1. Headline & Actions
        header_layout = QHBoxLayout()
        headline = QLabel("Customer Management")
        headline.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 20px; font-weight: 700;")
        header_layout.addWidget(headline)
        
        header_layout.addStretch()
        
        self.add_customer_btn = QPushButton("+ REGISTER CUSTOMER")
        self.add_customer_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
            }}
        """)
        header_layout.addWidget(self.add_customer_btn)
        
        layout.addLayout(header_layout)

        # 2. Search Bar Card
        filter_card = ERPCard()
        filter_card.setFixedHeight(70)
        filter_layout = QHBoxLayout(filter_card)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, phone number, or customer ID...")
        self.search_input.setStyleSheet(f"border: 1px solid {Theme.BORDER}; border-radius: 6px; padding: 8px 12px;")
        filter_layout.addWidget(self.search_input)
        
        layout.addWidget(filter_card)

        # 3. Customer Table
        table_card = ERPCard()
        table_layout = QVBoxLayout(table_card)
        
        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(5)
        self.customer_table.setHorizontalHeaderLabels(["Name", "Phone", "Debt/Credit", "Last Visit", "Status"])
        self.customer_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.customer_table.setStyleSheet(f"border: none; background: transparent;")
        table_layout.addWidget(self.customer_table)
        
        layout.addWidget(table_card)
        layout.addStretch()
