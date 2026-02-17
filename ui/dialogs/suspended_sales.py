"""
PharmaPOS ERP - Suspended Sales Dialog
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QHeaderView, QTableWidgetItem, QMessageBox
)
from PyQt5.QtCore import Qt
from ..styles.theme import Theme

class SuspendedSalesDialog(QDialog):
    def __init__(self, sales_service, store_id, parent=None):
        super().__init__(parent)
        self.sales_service = sales_service
        self.store_id = store_id
        self.selected_sale_id = None
        
        self.setWindowTitle("Recall Suspended Sale")
        self.resize(700, 500)
        self.setup_ui()
        self.refresh_table()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("Suspended Transactions (On-Hold)")
        header.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Theme.TEXT_MAIN};")
        layout.addWidget(header)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Reference", "Total Amount", "Date", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.handle_recall)
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel_btn = QPushButton("CLOSE")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)
        
        self.recall_btn = QPushButton("RECALL SALE")
        self.recall_btn.clicked.connect(self.handle_recall)
        self.recall_btn.setStyleSheet(f"background-color: {Theme.PRIMARY}; color: white; padding: 8px 20px; border-radius: 6px; font-weight: bold;")
        btns.addWidget(self.recall_btn)
        layout.addLayout(btns)

    def refresh_table(self):
        if not self.sales_service: return
        sales = self.sales_service.get_suspended_sales(self.store_id)
        
        self.table.setRowCount(len(sales))
        for i, s in enumerate(sales):
            self.table.setItem(i, 0, QTableWidgetItem(s['reference'] or "No Reference"))
            self.table.setItem(i, 1, QTableWidgetItem(f"₦{float(s['total_amount']):,.2f}"))
            self.table.setItem(i, 2, QTableWidgetItem(str(s['created_at'])[:16]))
            
            # Store sale ID in the first item
            self.table.item(i, 0).setData(Qt.UserRole, s['id'])

    def handle_recall(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a sale to recall.")
            return
            
        self.selected_sale_id = self.table.item(row, 0).data(Qt.UserRole)
        self.accept()

    def get_selected_id(self):
        return self.selected_sale_id
