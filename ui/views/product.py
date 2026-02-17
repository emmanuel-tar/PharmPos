"""
PharmaPOS ERP - Product Catalog View

Comprehensive product management interface.
Manage pricing tiers, NAFDAC info, and SKU master data.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QHeaderView, QPushButton, QSpacerItem, QSizePolicy,
    QFrame, QLineEdit
)
from PyQt5.QtCore import Qt

from ..components.widgets import ERPCard
from ..styles.theme import Theme

class ProductView(QWidget):
    """Modern product catalog management interface."""
    def __init__(self, product_service=None, parent=None):
        super().__init__(parent)
        self.product_service = product_service
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # 1. Headline & Actions
        header_layout = QHBoxLayout()
        headline = QLabel("Product Catalog")
        headline.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 20px; font-weight: 700;")
        header_layout.addWidget(headline)
        
        header_layout.addStretch()
        
        self.add_product_btn = QPushButton("+ NEW PRODUCT")
        self.add_product_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {Theme.PRIMARY_HOVER};
            }}
        """)
        header_layout.addWidget(self.add_product_btn)
        
        self.import_btn = QPushButton("IMPORT / EXPORT")
        self.import_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.SURFACE_CARD};
                color: {Theme.TEXT_MAIN};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {Theme.SURFACE_MAIN};
            }}
        """)
        header_layout.addWidget(self.import_btn)
        
        layout.addLayout(header_layout)

        # 2. Search & Filter Bar
        filter_card = ERPCard()
        filter_card.setFixedHeight(70)
        filter_layout = QHBoxLayout(filter_card)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search products by name, SKU, or Barcode...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                background-color: {Theme.SURFACE_MAIN};
            }}
        """)
        filter_layout.addWidget(self.search_input)
        
        layout.addWidget(filter_card)

        # 3. Product Table Card
        table_card = ERPCard()
        table_layout = QVBoxLayout(table_card)
        
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(6)
        self.product_table.setHorizontalHeaderLabels(["Name", "SKU", "NAFDAC #", "Retail Price", "Wholesale", "Status"])
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.product_table.setStyleSheet(f"border: none; background: transparent;")
        table_layout.addWidget(self.product_table)
        
        layout.addWidget(table_card)
        layout.addStretch()
