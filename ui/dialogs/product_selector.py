"""
PharmaPOS ERP - Product Selector Dialog
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QHeaderView, QTableWidgetItem, QMessageBox
)
from PyQt5.QtCore import Qt
from ..styles.theme import Theme

class ProductSelectorDialog(QDialog):
    def __init__(self, product_service, parent=None):
        super().__init__(parent)
        self.product_service = product_service
        self.selected_product = None
        
        self.setWindowTitle("Select Product")
        self.resize(600, 500)
        self.setup_ui()
        self.refresh_table()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("Search and Select a Product")
        header.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Theme.TEXT_MAIN};")
        layout.addWidget(header)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Name or SKU...")
        self.search_input.textChanged.connect(self.refresh_table)
        self.search_input.setStyleSheet(f"padding: 10px; border: 1px solid {Theme.BORDER}; border-radius: 6px;")
        layout.addWidget(self.search_input)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "SKU", "Base Cost"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.handle_select)
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel_btn = QPushButton("CANCEL")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)
        
        self.select_btn = QPushButton("SELECT")
        self.select_btn.clicked.connect(self.handle_select)
        self.select_btn.setStyleSheet(f"background-color: {Theme.PRIMARY}; color: white; padding: 8px 20px; border-radius: 6px; font-weight: bold;")
        btns.addWidget(self.select_btn)
        layout.addLayout(btns)

    def refresh_table(self):
        if not self.product_service: return
        query = self.search_input.text().lower()
        products = self.product_service.get_all_products()
        
        if query:
            products = [p for p in products if query in p['name'].lower() or query in p['sku'].lower()]
            
        self.table.setRowCount(len(products))
        for i, p in enumerate(products):
            self.table.setItem(i, 0, QTableWidgetItem(p['name']))
            self.table.setItem(i, 1, QTableWidgetItem(p['sku']))
            self.table.setItem(i, 2, QTableWidgetItem(f"₦{float(p.get('cost_price', 0)):,.2f}"))
            # Store product data in the first item
            self.table.item(i, 0).setData(Qt.UserRole, p)

    def handle_select(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a product from the list.")
            return
            
        self.selected_product = self.table.item(row, 0).data(Qt.UserRole)
        self.accept()

    def get_selected(self):
        return self.selected_product
