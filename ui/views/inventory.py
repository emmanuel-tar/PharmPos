"""
PharmaPOS ERP - Inventory View

Professional inventory management interface.
Focus on FEFO tracking, batch management, and stock alerts.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QHeaderView, QPushButton, QSpacerItem, QSizePolicy,
    QFrame, QLineEdit
)
from PyQt5.QtCore import Qt

from ..components.widgets import ERPCard, MetricCard
from ..styles.theme import Theme
from ..dialogs.receive_stock import ReceiveStockDialog
from ..dialogs.stock_transfer import StockTransferDialog

class InventoryView(QWidget):
    """Modern inventory management interface."""
    def __init__(self, inventory_service=None, transfer_service=None, parent=None):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.transfer_service = transfer_service
        self.store_id = 1 # Placeholder
        self.setup_ui()
        self.refresh_status()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # 1. Headline & Actions
        header_layout = QHBoxLayout()
        headline = QLabel("Inventory Management")
        headline.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 20px; font-weight: 700;")
        header_layout.addWidget(headline)
        
        header_layout.addStretch()
        
        self.receive_btn = QPushButton("+ RECEIVE STOCK")
        self.receive_btn.clicked.connect(self.handle_receive_stock)
        self.receive_btn.setStyleSheet(f"""
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
        header_layout.addWidget(self.receive_btn)
        
        self.transfer_btn = QPushButton("STOCK TRANSFER")
        self.transfer_btn.clicked.connect(self.handle_stock_transfer)
        self.transfer_btn.setStyleSheet(f"""
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
        header_layout.addWidget(self.transfer_btn)
        
        layout.addLayout(header_layout)

        # 2. Key Metrics Row
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(16)
        
        self.total_value_card = MetricCard("Inventory Value", "₦0.00", "Across all batches", Theme.INFO)
        self.expiring_card = MetricCard("Critical Expiries", "0", "Within 30 days", Theme.DANGER)
        self.low_stock_card = MetricCard("Low Stock Items", "0", "Below reorder level", Theme.WARNING)
        
        metrics_layout.addWidget(self.total_value_card)
        metrics_layout.addWidget(self.expiring_card)
        metrics_layout.addWidget(self.low_stock_card)
        
        layout.addLayout(metrics_layout)

        # 3. Search & Filters
        filter_card = ERPCard()
        filter_card.setFixedHeight(70)
        filter_layout = filter_card.set_layout(QHBoxLayout())
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter by Product, SKU, or Batch number...")
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
        
        # Branch selector placeholder
        branch_selector = QLineEdit("Main Branch")
        branch_selector.setReadOnly(True)
        branch_selector.setFixedWidth(150)
        filter_layout.addWidget(branch_selector)
        
        layout.addWidget(filter_card)

        # 4. Inventory Table Card
        table_card = ERPCard()
        table_layout = table_card.set_layout(QVBoxLayout())
        
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(6)
        self.inventory_table.setHorizontalHeaderLabels(["Product", "Batch #", "Expiry Date", "Stock", "Cost", "Value"])
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inventory_table.setStyleSheet(f"border: none; background: transparent;")
        table_layout.addWidget(self.inventory_table)
        
        layout.addWidget(table_card)
        layout.addStretch()

    def refresh_status(self):
        """Update metric cards from service."""
        if not self.inventory_service:
            return

        status = self.inventory_service.get_stock_status(self.store_id)
        expiring = self.inventory_service.get_expiring_items(self.store_id)
        
        self.total_value_card.update_value(f"₦0.00") # TODO: Add value calculation to service
        self.expiring_card.update_value(str(len(expiring)))
        self.low_stock_card.update_value(str(status.get('low_stock_count', 0)))

    def handle_receive_stock(self):
        """Open dialog and receive new stock batch."""
        # For demo, assume we are receiving for product_id 1
        dialog = ReceiveStockDialog(1, "Sample Product", self)
        if dialog.exec_():
            data = dialog.get_data()
            self.inventory_service.receive_batch(
                product_id=1,
                store_id=self.store_id,
                batch_number=data['batch_number'],
                quantity=data['quantity'],
                expiry_date=data['expiry_date'],
                cost_price=data['cost_price']
            )
            self.refresh_status()
            print(f"Received batch: {data['batch_number']}")

    def handle_stock_transfer(self):
        """Open transfer dialog and initiate transfer."""
        if not self.transfer_service:
            return
            
        # Placeholder stores list
        stores = [{"id": 1, "name": "Main Branch"}, {"id": 2, "name": "Warehouse"}]
        
        dialog = StockTransferDialog(1, "Sample Product", self.store_id, stores, self)
        if dialog.exec_():
            data = dialog.get_data()
            self.transfer_service.initiate_transfer(
                product_id=1,
                batch_number=data['batch_number'],
                quantity=data['quantity'],
                from_store_id=self.store_id,
                to_store_id=data['to_store_id']
            )
            self.refresh_status()
            print(f"Initiated transfer of {data['quantity']} units to Store {data['to_store_id']}")
