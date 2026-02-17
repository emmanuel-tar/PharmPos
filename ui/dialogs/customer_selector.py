"""
PharmaPOS ERP - Customer Selector Dialog
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QHeaderView, QTableWidgetItem, QMessageBox
)
from PyQt5.QtCore import Qt
from ..styles.theme import Theme

class CustomerSelectorDialog(QDialog):
    def __init__(self, customer_service, parent=None):
        super().__init__(parent)
        self.customer_service = customer_service
        self.selected_customer = None
        
        self.setWindowTitle("Select Customer")
        self.resize(600, 500)
        self.setup_ui()
        self.refresh_table()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("Search and Select a Customer")
        header.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Theme.TEXT_MAIN};")
        layout.addWidget(header)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Name or Phone...")
        self.search_input.textChanged.connect(self.refresh_table)
        self.search_input.setStyleSheet(f"padding: 10px; border: 1px solid {Theme.BORDER}; border-radius: 6px;")
        layout.addWidget(self.search_input)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Phone", "Email"])
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
        # Local mock or service call
        customers = []
        try:
            # Assuming a standard customer registry exists in database
            from desktop_app.database import customers as cust_table
            from sqlalchemy import select
            
            query = self.search_input.text().lower()
            # This is a bit direct for UI, usually service layer would handle this
            # session = ...
            # customers = ...
            
            # Placeholder for now
            customers = [
                {'id': 1, 'name': 'Walk-in Customer', 'phone': '0000000000', 'email': 'none@pharmapos.ng'},
                {'id': 2, 'name': 'John Doe', 'phone': '08012345678', 'email': 'john@example.com'},
            ]
            
            if query:
                customers = [c for c in customers if query in c['name'].lower() or query in c['phone']]
                
        except:
            pass
            
        self.table.setRowCount(len(customers))
        for i, c in enumerate(customers):
            self.table.setItem(i, 0, QTableWidgetItem(c['name']))
            self.table.setItem(i, 1, QTableWidgetItem(c['phone']))
            self.table.setItem(i, 2, QTableWidgetItem(c.get('email', 'N/A')))
            # Store data
            self.table.item(i, 0).setData(Qt.UserRole, c)

    def handle_select(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a customer.")
            return
            
        self.selected_customer = self.table.item(row, 0).data(Qt.UserRole)
        self.accept()

    def get_selected(self):
        return self.selected_customer
