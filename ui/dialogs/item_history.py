"""
PharmaPOS ERP - Item History Dialog
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QHeaderView, QTableWidgetItem,
    QFrame
)
from PyQt5.QtCore import Qt
from ..styles.theme import Theme

class ItemHistoryDialog(QDialog):
    def __init__(self, product_id, product_name, inventory_service, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.inventory_service = inventory_service
        self.setWindowTitle(f"Movement History: {product_name}")
        self.resize(800, 500)
        self.setup_ui()
        self.load_history()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel(f"Traceability Log: {self.windowTitle().split(': ')[1]}")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {Theme.TEXT_MAIN};")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Date", "Batch #", "Type", "Prev Qty", "Change", "New Qty"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet(f"background-color: {Theme.SURFACE_CARD}; border-radius: 4px;")
        layout.addWidget(self.table)

    def load_history(self):
        history = self.inventory_service.get_product_history(self.product_id)
        self.table.setRowCount(len(history))
        for i, entry in enumerate(history):
            self.table.setItem(i, 0, QTableWidgetItem(str(entry['created_at'])[:16]))
            self.table.setItem(i, 1, QTableWidgetItem(entry.get('batch_number', 'N/A')))
            
            type_item = QTableWidgetItem(entry['change_type'].upper())
            # Color coding based on type
            if entry['change_type'] in ['sale', 'transfer_out', 'expired', 'writeoff']:
                type_item.setForeground(Qt.red)
            else:
                type_item.setForeground(Qt.darkGreen)
            
            self.table.setItem(i, 2, type_item)
            self.table.setItem(i, 3, QTableWidgetItem(str(entry['previous_quantity'])))
            
            change = entry['new_quantity'] - entry['previous_quantity']
            change_item = QTableWidgetItem(f"{'+' if change > 0 else ''}{change}")
            self.table.setItem(i, 4, change_item)
            
            self.table.setItem(i, 5, QTableWidgetItem(str(entry['new_quantity'])))
