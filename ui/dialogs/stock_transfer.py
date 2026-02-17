"""
PharmaPOS ERP - Stock Transfer Dialog

Allows users to move stock between different stores/branches.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QSpinBox, QComboBox, QPushButton, QHBoxLayout, QLabel
)
from PyQt5.QtCore import Qt
from ..styles.theme import Theme

class StockTransferDialog(QDialog):
    """Form to initiate a stock transfer."""
    def __init__(self, product_id, product_name, current_store_id, stores, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Stock Transfer: {product_name}")
        self.setMinimumWidth(400)
        self.product_id = product_id
        self.current_store_id = current_store_id
        self.stores = stores # List of store dicts
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(12)

        self.batch_input = QLineEdit()
        self.batch_input.setPlaceholderText("Enter Batch Number to transfer")
        form.addRow("Batch Number:", self.batch_input)

        self.to_store_combo = QComboBox()
        for store in self.stores:
            if store['id'] != self.current_store_id:
                self.to_store_combo.addItem(store['name'], store['id'])
        form.addRow("Destination Store:", self.to_store_combo)

        self.qty_input = QSpinBox()
        self.qty_input.setRange(1, 10000)
        form.addRow("Quantity to Transfer:", self.qty_input)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        self.send_btn = QPushButton("Initiate Transfer")
        self.send_btn.clicked.connect(self.accept)
        self.send_btn.setStyleSheet(f"""
            background-color: {Theme.PRIMARY};
            color: white;
            border-radius: 4px;
            padding: 8px 20px;
            font-weight: 600;
        """)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.send_btn)
        layout.addLayout(btn_layout)

    def get_data(self):
        return {
            "batch_number": self.batch_input.text(),
            "to_store_id": self.to_store_combo.currentData(),
            "quantity": self.qty_input.value()
        }
