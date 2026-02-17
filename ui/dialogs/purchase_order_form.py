"""
PharmaPOS ERP - Purchase Order Form Dialog
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QTableWidget, QHeaderView,
    QTableWidgetItem, QDateEdit, QFormLayout, QTextEdit, QMessageBox, QWidget
)
from PyQt5.QtCore import Qt, QDate
from decimal import Decimal
from ..styles.theme import Theme

class PurchaseOrderFormDialog(QDialog):
    def __init__(self, supplier_service, product_service, po_data=None, parent=None):
        super().__init__(parent)
        self.supplier_service = supplier_service
        self.product_service = product_service
        self.po_data = po_data # None for Create mode
        self.items = [] # [{product_id, name, sku, qty, cost}]
        
        self.setWindowTitle("Purchase Order")
        self.resize(800, 600)
        self.setup_ui()
        self.load_suppliers()
        if self.po_data:
            self.populate_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title_text = "Edit Purchase Order" if self.po_data else "New Purchase Order"
        title = QLabel(title_text)
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {Theme.TEXT_MAIN};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Top Form
        top_form = QHBoxLayout()
        
        # Left side: Supplier & Date
        left_side = QFormLayout()
        self.supplier_combo = QComboBox()
        left_side.addRow("Supplier:", self.supplier_combo)
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        left_side.addRow("Expected Date:", self.date_input)
        
        top_form.addLayout(left_side, 1)
        
        # Right side: PO info
        right_side = QFormLayout()
        self.po_number_label = QLabel("AUTO-GENERATED")
        self.po_number_label.setStyleSheet("font-weight: bold; color: gray;")
        right_side.addRow("PO Number:", self.po_number_label)
        
        self.status_label = QLabel("DRAFT")
        self.status_label.setStyleSheet(f"color: {Theme.INFO}; font-weight: bold;")
        right_side.addRow("Status:", self.status_label)
        
        top_form.addLayout(right_side, 1)
        layout.addLayout(top_form)

        # Items Table
        items_group = QVBoxLayout()
        items_header = QHBoxLayout()
        items_header.addWidget(QLabel("Order Items"))
        items_header.addStretch()
        
        self.add_item_btn = QPushButton("+ ADD ITEM")
        self.add_item_btn.clicked.connect(self.handle_add_item)
        self.add_item_btn.setStyleSheet(f"background-color: {Theme.PRIMARY_LIGHT}; color: {Theme.PRIMARY}; border-radius: 4px; padding: 6px 12px; font-weight: bold;")
        items_header.addWidget(self.add_item_btn)
        items_group.addLayout(items_header)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(["Product", "SKU", "Est. Cost", "Qty", "Total"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.verticalHeader().setVisible(False)
        items_group.addWidget(self.items_table)
        
        layout.addLayout(items_group)

        # Footer
        footer = QHBoxLayout()
        
        # Notes
        notes_layout = QVBoxLayout()
        notes_layout.addWidget(QLabel("Notes / Instructions"))
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        notes_layout.addWidget(self.notes_input)
        footer.addLayout(notes_layout, 2)
        
        # Summary
        summary_layout = QFormLayout()
        self.total_label = QLabel("₦0.00")
        self.total_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {Theme.PRIMARY};")
        summary_layout.addRow("Total Expected:", self.total_label)
        footer.addLayout(summary_layout, 1)
        
        layout.addLayout(footer)

        # Actions
        actions = QHBoxLayout()
        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn = QPushButton("CREATE ORDER")
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                font-weight: bold;
                padding: 12px 24px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {Theme.PRIMARY_HOVER};
            }}
        """)
        self.save_btn.clicked.connect(self.handle_save)
        
        actions.addStretch()
        actions.addWidget(self.cancel_btn)
        actions.addWidget(self.save_btn)
        layout.addLayout(actions)

    def load_suppliers(self):
        self.supplier_combo.clear()
        suppliers = self.supplier_service.get_all_suppliers()
        for s in suppliers:
            self.supplier_combo.addItem(s['name'], s['id'])

    def populate_data(self):
        # TODO: Handle editing existing PO
        pass

    def handle_add_item(self):
        # TODO: Open Product Selector
        # For now, simulate adding a product
        products = self.product_service.get_all_products()
        if not products:
            QMessageBox.warning(self, "Error", "No products found. Please add products first.")
            return
            
        p = products[0] # Pick first one for mock
        item = {
            "product_id": p['id'],
            "name": p['name'],
            "sku": p['sku'],
            "cost": float(p.get('cost_price', 0)),
            "qty": 10
        }
        self.items.append(item)
        self.refresh_items_table()

    def refresh_items_table(self):
        self.items_table.setRowCount(len(self.items))
        total = Decimal("0")
        for i, item in enumerate(self.items):
            self.items_table.setItem(i, 0, QTableWidgetItem(item['name']))
            self.items_table.setItem(i, 1, QTableWidgetItem(item['sku']))
            self.items_table.setItem(i, 2, QTableWidgetItem(f"₦{item['cost']:,.2f}"))
            self.items_table.setItem(i, 3, QTableWidgetItem(str(item['qty'])))
            
            line_total = Decimal(str(item['cost'])) * Decimal(str(item['qty']))
            total += line_total
            self.items_table.setItem(i, 4, QTableWidgetItem(f"₦{float(line_total):,.2f}"))
            
        self.total_label.setText(f"₦{float(total):,.2f}")

    def handle_save(self):
        if self.supplier_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Validation Error", "Please select a supplier.")
            return
        if not self.items:
            QMessageBox.warning(self, "Validation Error", "Please add at least one item.")
            return
        self.accept()

    def get_data(self):
        return {
            "supplier_id": self.supplier_combo.currentData(),
            "expected_delivery_date": self.date_input.date().toPyDate(),
            "notes": self.notes_input.toPlainText().strip(),
            "items": [
                {
                    "product_id": it["product_id"],
                    "quantity_ordered": it["qty"],
                    "expected_cost_price": it["cost"],
                    "notes": ""
                } for it in self.items
            ]
        }
