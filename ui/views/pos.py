"""
PharmaPOS ERP - POS View

Point of Sale interface designed for speed and clarity.
Supports both retail scanning and pharmaceutical batch selection.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTableWidget, QHeaderView, QPushButton, QSpacerItem, QSizePolicy,
    QFrame
)
from PyQt5.QtCore import Qt

from ..components.widgets import ERPCard
from ..styles.theme import Theme
from ..dialogs.batch_selection import BatchSelectionDialog

class POSView(QWidget):
    """Versatile POS interface."""
    def __init__(self, sales_service=None, product_service=None, inventory_service=None, category_service=None, parent=None):
        super().__init__(parent)
        self.sales_service = sales_service
        self.product_service = product_service
        self.inventory_service = inventory_service
        self.category_service = category_service
        self.cart = [] # List of (batch_data, quantity)
        self.store_id = 1 # Placeholder, should come from session
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # --- LEFT SIDE: Product Selection ---
        left_side = QVBoxLayout()
        left_side.setSpacing(16)

        # Search Bar Card
        search_card = ERPCard()
        search_card.setFixedHeight(80)
        search_layout = QHBoxLayout(search_card)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Scan barcode or search products (Press Enter)...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                background-color: {Theme.SURFACE_MAIN};
            }}
            QLineEdit:focus {{
                border-color: {Theme.PRIMARY};
                background-color: {Theme.SURFACE_CARD};
            }}
        """)
        self.search_input.returnPressed.connect(self.handle_search)
        search_layout.addWidget(self.search_input)
        left_side.addWidget(search_card)

        # Product Grid/Table Card
        catalog_card = ERPCard()
        catalog_layout = QVBoxLayout(catalog_card)
        
        catalog_header = QLabel("Product Catalog")
        catalog_header.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 16px; font-weight: 600;")
        catalog_layout.addWidget(catalog_header)
        
        self.catalog_table = QTableWidget()
        self.catalog_table.setColumnCount(4)
        self.catalog_table.setHorizontalHeaderLabels(["Product", "SKU", "Stock", "Price"])
        self.catalog_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.catalog_table.setStyleSheet(f"border: none; background: transparent;")
        self.catalog_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.catalog_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.catalog_table.doubleClicked.connect(self.add_selected_to_cart)
        catalog_layout.addWidget(self.catalog_table)
        
        left_side.addWidget(catalog_card)
        layout.addLayout(left_side, stretch=3)

        # --- RIGHT SIDE: Cart & Checkout ---
        right_side = QVBoxLayout()
        right_side.setSpacing(16)

        # Cart Card
        cart_card = ERPCard()
        cart_layout = QVBoxLayout(cart_card)
        
        cart_header = QLabel("Current Cart")
        cart_header.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 16px; font-weight: 600;")
        cart_layout.addWidget(cart_header)
        
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(4)
        self.cart_table.setHorizontalHeaderLabels(["Item", "Batch", "Qty", "Total"])
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cart_table.setStyleSheet(f"border: none; background: transparent;")
        cart_layout.addWidget(self.cart_table)
        
        # Totals Area
        totals_frame = QFrame()
        totals_frame.setStyleSheet(f"border-top: 1px solid {Theme.BORDER}; margin-top: 10px; padding-top: 10px;")
        totals_layout = QVBoxLayout(totals_frame)
        
        self.subtotal_label = QLabel("₦0.00")
        self.vat_label = QLabel("₦0.00")
        self.total_label = QLabel("₦0.00")

        def add_total_row(label, val_widget, bold=False):
            row = QHBoxLayout()
            lbl = QLabel(label)
            style = f"color: {Theme.TEXT_MAIN}; font-size: {'16px' if bold else '13px'}; font-weight: {'700' if bold else '500'};"
            lbl.setStyleSheet(style)
            val_widget.setStyleSheet(style)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val_widget)
            totals_layout.addLayout(row)

        add_total_row("Subtotal", self.subtotal_label)
        add_total_row("VAT (7.5%)", self.vat_label)
        totals_layout.addSpacing(8)
        add_total_row("TOTAL", self.total_label, bold=True)
        
        cart_layout.addWidget(totals_frame)
        
        # Checkout Button
        self.checkout_btn = QPushButton("PROCEED TO CHECKOUT")
        self.checkout_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.SUCCESS};
                color: white;
                border-radius: 8px;
                padding: 16px;
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
        """)
        cart_layout.addWidget(self.checkout_btn)

        right_side.addWidget(cart_card)
        layout.addLayout(right_side, stretch=2)

    def handle_search(self):
        """Search products and display in catalog."""
        search_term = self.search_input.text()
        if not self.product_service or not search_term:
            return

        # Assuming product_service.search_products returns a list of dicts
        # This is a placeholder for real service integration
        print(f"Searching for: {search_term}")
        # products = self.product_service.search_products(search_term)
        # self.update_catalog(products)

    def add_selected_to_cart(self):
        """Add double-clicked product to cart using FEFO."""
        selected_rows = self.catalog_table.selectionModel().selectedRows()
        if not selected_rows or not self.inventory_service:
            return
            
        product_id = 1 # Placeholder
        product_name = self.catalog_table.item(selected_rows[0].row(), 0).text()
        
        # Default to FEFO
        batch = self.inventory_service.get_fefo_batch(product_id, self.store_id)
        if batch:
            self.add_batch_to_cart(batch, product_name)
        else:
            print("No batches available!")

    def open_batch_picker(self):
        """Manually select a batch for the selected product."""
        selected_rows = self.catalog_table.selectionModel().selectedRows()
        if not selected_rows or not self.inventory_service:
            return

        product_id = 1 # Placeholder
        product_name = self.catalog_table.item(selected_rows[0].row(), 0).text()
        
        # Get all batches for this product
        # Placeholder for real service call
        batches = [
            {'id': 101, 'batch_number': 'B-001', 'expiry_date': '2025-12-31', 'quantity': 50, 'selling_price': 1500},
            {'id': 102, 'batch_number': 'B-002', 'expiry_date': '2026-06-30', 'quantity': 100, 'selling_price': 1500},
        ]
        
        dialog = BatchSelectionDialog(product_name, batches, self)
        if dialog.exec_():
            batch = dialog.get_selected_batch()
            self.add_batch_to_cart(batch, product_name)

    def contextMenuEvent(self, event):
        """Right-click menu for manual batch selection."""
        if self.catalog_table.underMouse():
            from PyQt5.QtWidgets import QMenu
            menu = QMenu(self)
            manual_action = menu.addAction("Select Specific Batch...")
            manual_action.triggered.connect(self.open_batch_picker)
            menu.exec_(event.globalPos())

    def add_batch_to_cart(self, batch_data, product_name):
        """Add a specific batch to the cart."""
        # Check if already in cart
        for item in self.cart:
            if item['batch_id'] == batch_data.get('id'):
                item['quantity'] += 1
                self.update_cart_display()
                return

        self.cart.append({
            'product_name': product_name,
            'batch_id': batch_data.get('id'),
            'batch_number': batch_data.get('batch_number'),
            'price': batch_data.get('selling_price', 0),
            'quantity': 1
        })
        self.update_cart_display()

    def update_cart_display(self):
        self.cart_table.setRowCount(len(self.cart))
        total = 0
        for i, item in enumerate(self.cart):
            row_total = item['price'] * item['quantity']
            total += row_total
            self.cart_table.setItem(i, 0, QTableWidgetItem(item['product_name']))
            self.cart_table.setItem(i, 1, QTableWidgetItem(item['batch_number']))
            self.cart_table.setItem(i, 2, QTableWidgetItem(str(item['quantity'])))
            self.cart_table.setItem(i, 3, QTableWidgetItem(f"₦{row_total:,.2f}"))

        subtotal = total / 1.075 # Reverse VAT for display
        vat = total - subtotal
        
        self.subtotal_label.setText(f"₦{subtotal:,.2f}")
        self.vat_label.setText(f"₦{vat:,.2f}")
        self.total_label.setText(f"₦{total:,.2f}")
