"""
PharmaPOS ERP - Receive Purchase Order Dialog
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QHeaderView, QTableWidgetItem, 
    QDateEdit, QSpinBox, QDoubleSpinBox, QMessageBox, QWidget
)
from PyQt5.QtCore import Qt, QDate
from decimal import Decimal
from ..styles.theme import Theme

class ReceivePurchaseOrderDialog(QDialog):
    def __init__(self, procurement_service, po_id, po_number, items, parent=None):
        super().__init__(parent)
        self.procurement_service = procurement_service
        self.po_id = po_id
        self.po_number = po_number
        self.items = items # [{product_id, name, sku, quantity_ordered, expected_cost_price}]
        self.receipts = [] # To be filled by user
        
        self.setWindowTitle(f"Receive Goods: {self.po_number}")
        self.resize(1000, 600)
        self.setup_ui()
        self.initialize_receipts()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel(f"Goods Receiving for PO: {self.po_number}")
        header.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {Theme.TEXT_MAIN};")
        layout.addWidget(header)

        instruction = QLabel("Enter received quantities, batch details and confirm cost prices.")
        instruction.setStyleSheet(f"color: {Theme.TEXT_MUTED};")
        layout.addWidget(instruction)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Product", "Ordered", "Received Qty", "Batch Number", "Expiry Date", "Actual Cost", "Subtotal"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # Actions
        btns = QHBoxLayout()
        btns.addStretch()
        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.clicked.connect(self.reject)
        btns.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("CONFIRM RECEPTION")
        self.save_btn.clicked.connect(self.handle_save)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.SUCCESS};
                color: white;
                padding: 10px 24px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Theme.SUCCESS_HOVER if hasattr(Theme, 'SUCCESS_HOVER') else Theme.SUCCESS};
            }}
        """)
        btns.addWidget(self.save_btn)
        layout.addLayout(btns)

    def initialize_receipts(self):
        self.table.setRowCount(len(self.items))
        for i, item in enumerate(self.items):
            # Product Name
            self.table.setItem(i, 0, QTableWidgetItem(item['name']))
            
            # Ordered Qty
            self.table.setItem(i, 1, QTableWidgetItem(str(item['quantity_ordered'])))
            
            # Received Qty Input
            qty_spin = QSpinBox()
            qty_spin.setRange(0, 100000)
            qty_spin.setValue(item['quantity_ordered'])
            self.table.setCellWidget(i, 2, qty_spin)
            
            # Batch Number Input
            batch_input = QLineEdit()
            batch_input.setPlaceholderText("Batch #")
            self.table.setCellWidget(i, 3, batch_input)
            
            # Expiry Date Input
            expiry_input = QDateEdit()
            expiry_input.setCalendarPopup(True)
            expiry_input.setDate(QDate.currentDate().addYears(2))
            self.table.setCellWidget(i, 4, expiry_input)
            
            # Actual Cost Input
            cost_spin = QDoubleSpinBox()
            cost_spin.setRange(0, 10000000)
            cost_spin.setPrefix("₦")
            cost_spin.setValue(float(item.get('expected_cost_price', 0)))
            self.table.setCellWidget(i, 5, cost_spin)
            
            # Subtotal (will update on qty/cost change)
            self.update_row_total(i)
            
            # Connect signals
            qty_spin.valueChanged.connect(lambda _, idx=i: self.update_row_total(idx))
            cost_spin.valueChanged.connect(lambda _, idx=i: self.update_row_total(idx))

    def update_row_total(self, row):
        qty = self.table.cellWidget(row, 2).value()
        cost = self.table.cellWidget(row, 5).value()
        total = qty * cost
        self.table.setItem(row, 6, QTableWidgetItem(f"₦{total:,.2f}"))

    def handle_save(self):
        receipts = []
        for i in range(self.table.rowCount()):
            qty = self.table.cellWidget(i, 2).value()
            batch = self.table.cellWidget(i, 3).text().strip()
            expiry = self.table.cellWidget(i, 4).date().toPyDate()
            cost = self.table.cellWidget(i, 5).value()
            
            if qty > 0:
                if not batch:
                    QMessageBox.warning(self, "Missing Info", f"Please enter batch number for {self.items[i]['name']}")
                    return
                
                receipts.append({
                    "product_id": self.items[i]['product_id'],
                    "batch_number": batch,
                    "expiry_date": expiry,
                    "received_quantity": qty,
                    "actual_cost_price": cost
                })
        
        if not receipts:
            QMessageBox.warning(self, "No Items", "Please receive at least one item.")
            return
            
        self.receipts = receipts
        self.accept()

    def get_data(self):
        return self.receipts
