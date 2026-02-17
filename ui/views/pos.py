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
        
        cart_header_row = QHBoxLayout()
        cart_header = QLabel("Current Cart")
        cart_header.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 16px; font-weight: 600;")
        cart_header_row.addWidget(cart_header)
        cart_header_row.addStretch()
        
        self.customer_btn = QPushButton("SELECT CUSTOMER")
        self.customer_btn.setStyleSheet(f"color: {Theme.PRIMARY}; font-weight: bold; font-size: 12px; border: 1px solid {Theme.PRIMARY}; padding: 4px 8px; border-radius: 4px;")
        cart_header_row.addWidget(self.customer_btn)
        cart_layout.addLayout(cart_header_row)
        
        # Action Bar (Hold, Recall, Clear)
        action_bar = QHBoxLayout()
        
        self.hold_btn = QPushButton("HOLD")
        self.hold_btn.setStyleSheet(f"background-color: {Theme.INFO}; color: white; border-radius: 4px; padding: 6px; font-size: 10px; font-weight: bold;")
        
        self.recall_btn = QPushButton("RECALL")
        self.recall_btn.setStyleSheet(f"background-color: {Theme.PRIMARY}; color: white; border-radius: 4px; padding: 6px; font-size: 10px; font-weight: bold;")
        
        self.clear_btn = QPushButton("CLEAR")
        self.clear_btn.setStyleSheet(f"background-color: {Theme.DANGER}; color: white; border-radius: 4px; padding: 6px; font-size: 10px; font-weight: bold;")
        self.clear_btn.clicked.connect(self.clear_cart)
        
        action_bar.addWidget(self.hold_btn)
        action_bar.addWidget(self.recall_btn)
        action_bar.addWidget(self.clear_btn)
        cart_layout.addLayout(action_bar)
        
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
        search_term = self.search_input.text().strip()
        if not self.product_service or not search_term:
            self.catalog_table.setRowCount(0)
            return

        try:
            products = self.product_service.get_all_products()
            # Basic client-side filter for now, or use service search if available
            filtered = [
                p for p in products 
                if search_term.lower() in p['name'].lower() 
                or search_term.lower() in p['sku'].lower()
            ]
            self.update_catalog(filtered)
        except Exception as e:
            print(f"Search error: {e}")

    def update_catalog(self, products):
        """Populate the catalog table with search results."""
        self.catalog_table.setRowCount(len(products))
        for i, p in enumerate(products):
            self.catalog_table.setItem(i, 0, QTableWidgetItem(p['name']))
            self.catalog_table.setItem(i, 1, QTableWidgetItem(p['sku']))
            
            # Stock: Get aggregate stock for this product across all batches in this store
            stock = 0
            if self.inventory_service:
                batches = self.inventory_service.get_store_inventory(self.store_id)
                stock = sum(b['quantity'] for b in batches if b['product_id'] == p['id'])
            
            self.catalog_table.setItem(i, 2, QTableWidgetItem(str(stock)))
            self.catalog_table.setItem(i, 3, QTableWidgetItem(f"₦{float(p.get('selling_price', 0)):,.2f}"))
            
            # Store product data for metadata access
            self.catalog_table.item(i, 0).setData(Qt.UserRole, p)

    def add_selected_to_cart(self):
        """Add double-clicked product to cart using FEFO."""
        selected_rows = self.catalog_table.selectionModel().selectedRows()
        if not selected_rows or not self.inventory_service:
            return
            
        product_data = self.catalog_table.item(selected_rows[0].row(), 0).data(Qt.UserRole)
        if not product_data:
            return
            
        product_id = product_data['id']
        product_name = product_data['name']
        
        # Default to FEFO
        batch = self.inventory_service.get_fefo_batch(product_id, self.store_id)
        if batch:
            self.add_batch_to_cart(batch, product_name)
        else:
            QMessageBox.warning(self, "No Stock", f"No available batches for {product_name} in this store.")

    def open_batch_picker(self):
        """Manually select a batch for the selected product."""
        selected_rows = self.catalog_table.selectionModel().selectedRows()
        if not selected_rows or not self.inventory_service:
            return

        product_data = self.catalog_table.item(selected_rows[0].row(), 0).data(Qt.UserRole)
        if not product_data:
            return
            
        product_id = product_data['id']
        product_name = product_data['name']
        
        # Get all batches for this product
        batches = self.inventory_service.get_store_inventory(self.store_id)
        product_batches = [b for b in batches if b['product_id'] == product_id and b['quantity'] > 0]
        
        if not product_batches:
            QMessageBox.warning(self, "No Stock", "No active batches found for this product.")
            return

        dialog = BatchSelectionDialog(product_name, product_batches, self)
        if dialog.exec_():
            batch = dialog.get_selected_batch()
            if batch:
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
