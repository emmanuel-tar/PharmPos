"""
PharmaPOS ERP - Batch Selection Dialog

Allows users to manually select a specific batch for a product.
Defaults to FEFO (Earliest Expiry).
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QPushButton, QHeaderView, QFrame
)
from PyQt5.QtCore import Qt
from ..styles.theme import Theme

class BatchSelectionDialog(QDialog):
    """Dialog for picking a specific product batch."""
    def __init__(self, product_name, batches, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Select Batch: {product_name}")
        self.setMinimumWidth(500)
        self.selected_batch = None
        self.batches = batches
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = QLabel("Available Batches (FEFO Prioritized)")
        header.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 14px; font-weight: 700;")
        layout.addWidget(header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Batch #", "Expiry", "Stock", "Select"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.load_batches()
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(f"padding: 8px 16px; color: {Theme.TEXT_MUTED};")
        
        self.confirm_btn = QPushButton("Confirm Selection")
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self.accept)
        self.confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 600;
            }}
            QPushButton:disabled {{
                background-color: {Theme.BORDER};
            }}
        """)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.confirm_btn)
        layout.addLayout(btn_layout)

        self.table.itemSelectionChanged.connect(self.on_selection_changed)

    def load_batches(self):
        self.table.setRowCount(len(self.batches))
        for i, batch in enumerate(self.batches):
            self.table.setItem(i, 0, QTableWidgetItem(batch.get('batch_number', 'N/A')))
            self.table.setItem(i, 1, QTableWidgetItem(str(batch.get('expiry_date', 'N/A'))))
            self.table.setItem(i, 2, QTableWidgetItem(str(batch.get('quantity', 0))))
            
            # Highlight FEFO (first row)
            if i == 0:
                for col in range(3):
                    self.table.item(i, col).setForeground(Theme.SUCCESS)
                    self.table.item(i, col).setToolTip("Recommended: Earliest Expiry")

    def on_selection_changed(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            index = selected_rows[0].row()
            self.selected_batch = self.batches[index]
            self.confirm_btn.setEnabled(True)

    def get_selected_batch(self):
        return self.selected_batch
