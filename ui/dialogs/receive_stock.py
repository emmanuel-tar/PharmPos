"""
PharmaPOS ERP - Receive Stock Dialog

Allows users to add new batches into inventory.
Includes NAFDAC info and expiry dates for compliance.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QSpinBox, QDoubleSpinBox, QDateEdit, QPushButton, QHBoxLayout, QLabel
)
from PyQt5.QtCore import QDate, Qt
from ..styles.theme import Theme

class ReceiveStockDialog(QDialog):
    """Form to receive new stock batches."""
    def __init__(self, product_id, product_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Receive Stock: {product_name}")
        self.setMinimumWidth(400)
        self.product_id = product_id
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(12)

        self.batch_input = QLineEdit()
        self.batch_input.setPlaceholderText("e.g. BATCH-2024-001")
        form.addRow("Batch Number:", self.batch_input)

        self.qty_input = QSpinBox()
        self.qty_input.setRange(1, 10000)
        self.qty_input.setValue(100)
        form.addRow("Quantity Received:", self.qty_input)

        self.expiry_input = QDateEdit()
        self.expiry_input.setCalendarPopup(True)
        self.expiry_input.setDate(QDate.currentDate().addYears(2))
        form.addRow("Expiry Date:", self.expiry_input)

        self.cost_input = QDoubleSpinBox()
        self.cost_input.setRange(0, 1000000)
        self.cost_input.setPrefix("₦")
        form.addRow("Cost Price (Unit):", self.cost_input)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton("Save Batch")
        self.save_btn.clicked.connect(self.accept)
        self.save_btn.setStyleSheet(f"""
            background-color: {Theme.PRIMARY};
            color: white;
            border-radius: 4px;
            padding: 8px 20px;
            font-weight: 600;
        """)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def get_data(self):
        return {
            "batch_number": self.batch_input.text(),
            "quantity": self.qty_input.value(),
            "expiry_date": self.expiry_input.date().toPyDate(),
            "cost_price": self.cost_input.value()
        }
