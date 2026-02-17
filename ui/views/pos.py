"""
PharmaPOS ERP - POS View

Point of Sale interface designed for speed and clarity.
Supports both retail scanning and pharmaceutical batch selection.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTableWidget, QHeaderView, QPushButton, QSpacerItem, QSizePolicy,
    QFrame, QMessageBox, QTableWidgetItem, QInputDialog, QCompleter,
    QScrollArea, QGridLayout
)
from PyQt5.QtCore import Qt, QStringListModel

from ..components.widgets import ERPCard, ProductCard
from ..styles.theme import Theme
from ..dialogs.batch_selection import BatchSelectionDialog
from ..dialogs.suspended_sales import SuspendedSalesDialog
from ..dialogs.payment_dialog import PaymentDialog
from ..dialogs.customer_selector import CustomerSelectorDialog

class POSView(QWidget):
    """Versatile POS interface."""
    def __init__(self, sales_service=None, product_service=None, inventory_service=None, category_service=None, customer_service=None, parent=None):
        super().__init__(parent)
        self.sales_service = sales_service
        self.product_service = product_service
        self.inventory_service = inventory_service
        self.category_service = category_service
        self.customer_service = customer_service
        self.cart = [] # List of (batch_data, quantity)
        self.store_id = 1 # Placeholder, should come from session
        self.current_customer = None
        self.current_category = None
        self.setup_ui()
        self.init_search_completer()
        self.load_categories()
        # Initial catalog load
        self.handle_search()

    def clear_cart(self):
        if not self.cart: return
        res = QMessageBox.question(self, "Clear Cart", "Are you sure you want to empty the cart?", 
                                 QMessageBox.Yes | QMessageBox.No)
        if res == QMessageBox.Yes:
            self.cart = []
            self.update_cart_display()

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
        
        # Assisted Search Completer
        self.completer = QCompleter(self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.activated.connect(self.handle_completer_selection)
        self.search_input.setCompleter(self.completer)
        
        search_layout.addWidget(self.search_input)
        left_side.addWidget(search_card)

        # Categories Card
        self.cat_scroll = QFrame()
        self.cat_scroll.setFixedHeight(60)
        self.cat_layout = QHBoxLayout(self.cat_scroll)
        self.cat_layout.setContentsMargins(0, 0, 0, 0)
        left_side.addWidget(self.cat_scroll)

        # Product Grid Area
        # Product Grid Area
        catalog_card = ERPCard()
        catalog_layout = QVBoxLayout(catalog_card)
        catalog_card.set_layout(catalog_layout)
        
        # Scroll area for grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        
        self.scroll_area.setWidget(self.grid_container)
        catalog_layout.addWidget(self.scroll_area)
        
        left_side.addWidget(catalog_card, stretch=1)
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
        self.customer_btn.clicked.connect(self.handle_customer_select)
        cart_header_row.addWidget(self.customer_btn)
        cart_layout.addLayout(cart_header_row)
        
        # Action Bar (Hold, Recall, Clear)
        action_bar = QHBoxLayout()
        
        self.hold_btn = QPushButton("HOLD")
        self.hold_btn.setStyleSheet(f"background-color: {Theme.INFO}; color: white; border-radius: 4px; padding: 6px; font-size: 10px; font-weight: bold;")
        self.hold_btn.clicked.connect(self.handle_hold_sale)
        
        self.recall_btn = QPushButton("RECALL")
        self.recall_btn.setStyleSheet(f"background-color: {Theme.PRIMARY}; color: white; border-radius: 4px; padding: 6px; font-size: 10px; font-weight: bold;")
        self.recall_btn.clicked.connect(self.handle_recall_sale)
        
        self.clear_btn = QPushButton("CLEAR")
        self.clear_btn.setStyleSheet(f"background-color: {Theme.DANGER}; color: white; border-radius: 4px; padding: 6px; font-size: 10px; font-weight: bold;")
        self.clear_btn.clicked.connect(self.clear_cart)
        
        action_bar.addWidget(self.hold_btn)
        action_bar.addWidget(self.recall_btn)
        action_bar.addWidget(self.clear_btn)
        cart_layout.addLayout(action_bar)
        
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(4)
        self.cart_table.setHorizontalHeaderLabels(["Item", "Price", "Qty", "Total"])
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
        self.checkout_btn.clicked.connect(self.handle_checkout)
        cart_layout.addWidget(self.checkout_btn)

        right_side.addWidget(cart_card)
        layout.addLayout(right_side, stretch=2)

    def load_categories(self):
        """Load categories and create buttons."""
        if not self.category_service: return
        
        # Clear existing
        for i in reversed(range(self.cat_layout.count())): 
            self.cat_layout.itemAt(i).widget().setParent(None)

        # Add "ALL" button
        all_btn = QPushButton("ALL ITEMS")
        all_btn.setStyleSheet(self.get_cat_btn_style(True))
        all_btn.clicked.connect(lambda: self.filter_by_category(None))
        self.cat_layout.addWidget(all_btn)
        self.cat_btns = {None: all_btn}

        try:
            categories = self.category_service.get_all_categories()
            for cat in categories:
                btn = QPushButton(cat['name'].upper())
                btn.setStyleSheet(self.get_cat_btn_style(False))
                btn.clicked.connect(lambda ch, c=cat['name']: self.filter_by_category(c))
                self.cat_layout.addWidget(btn)
                self.cat_btns[cat['name']] = btn
        except Exception as e:
            print(f"Error loading categories: {e}")
        
        self.cat_layout.addStretch()

    def get_cat_btn_style(self, active=False):
        bg = Theme.PRIMARY if active else Theme.SURFACE_CARD
        fg = "white" if active else Theme.TEXT_MAIN
        border = Theme.PRIMARY if active else Theme.BORDER
        return f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 15px;
                padding: 4px 16px;
                font-weight: 600;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {Theme.PRIMARY};
                color: white;
            }}
        """

    def filter_by_category(self, category_name):
        self.current_category = category_name
        # Update styles
        for name, btn in self.cat_btns.items():
            btn.setStyleSheet(self.get_cat_btn_style(name == category_name))
        self.handle_search()

    def init_search_completer(self):
        """Pre-load products for the search completer."""
        if not self.product_service: return
        try:
            products = self.product_service.get_all_products()
            keywords = []
            for p in products:
                keywords.append(p['name'])
                if p.get('sku'): keywords.append(p['sku'])
                if p.get('barcode'): keywords.append(p['barcode'])
            
            # Remove duplicates and empty strings
            keywords = list(set(filter(None, keywords)))
            
            model = QStringListModel()
            model.setStringList(keywords)
            self.completer.setModel(model)
        except Exception as e:
            print(f"Error initializing completer: {e}")

    def handle_completer_selection(self, text):
        """Handle item selection from the assisted search dropdown."""
        if not self.product_service: return
        
        try:
            # Try to find exactly by name, sku or barcode
            products = self.product_service.get_all_products()
            match = next((p for p in products if p['name'] == text or p['sku'] == text or p.get('barcode') == text), None)
            
            if match:
                self.add_product_to_cart(match)
                self.search_input.clear()
        except Exception as e:
            print(f"Selection error: {e}")

    def handle_search(self):
        """Search products and display in catalog or add to cart if exact match."""
        if not self.product_service:
            return

        search_term = self.search_input.text().strip()
        
        try:
            products = self.product_service.get_all_products(category=self.current_category)
            
            # 1. Check for Exact Match (Barcode/SKU) for immediate addition
            if search_term:
                exact_match = next((p for p in products if p['sku'].lower() == search_term.lower() or (p.get('barcode') and p['barcode'].lower() == search_term.lower())), None)
                
                if exact_match:
                    self.add_product_to_cart(exact_match)
                    self.search_input.clear()
                    # If we don't have a category filter, we might want to clear the table
                    if not self.current_category:
                        self.update_catalog([])
                        return
                    # If we DO have a category, keep showing the category items
                    search_term = "" # continue to show all in category
            
            # 2. Update the catalog table with results
            if search_term:
                filtered = [
                    p for p in products 
                    if search_term.lower() in p['name'].lower() 
                    or search_term.lower() in p['sku'].lower()
                    or (p.get('barcode') and search_term.lower() in p['barcode'].lower())
                ]
            else:
                filtered = products
            
            self.update_catalog(filtered)
        except Exception as e:
            print(f"Search error: {e}")

    def add_product_to_cart(self, product_data):
        """Add a specific product to the cart using FEFO."""
        if not self.inventory_service: return
        
        product_id = product_data['id']
        product_name = product_data['name']
        
        batch = self.inventory_service.get_fefo_batch(product_id, self.store_id)
        if batch:
            self.add_batch_to_cart(batch, product_name)
        else:
            QMessageBox.warning(self, "No Stock", f"No available batches for {product_name} in this store.")

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
            'price': float(batch_data.get('retail_price') or batch_data.get('selling_price') or 0),
            'quantity': 1
        })
        self.update_cart_display()

    def update_catalog(self, products):
        """Populate the grid with product cards."""
        # Clear existing
        try:
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.setParent(None)
        except Exception as e:
            print(f"Error clearing catalog: {e}")

        # Populate grid
        cols = 4 # Flexible responsive cols would be better but fixed for now
        for i, product in enumerate(products):
            try:
                card = ProductCard(product)
                card.clicked.connect(self.add_product_to_cart)
                self.grid_layout.addWidget(card, i // cols, i % cols)
            except Exception as e:
                print(f"Error adding product card: {e}")
        
        if not products:
            empty_lbl = QLabel("No products found.")
            empty_lbl.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(empty_lbl, 0, 0)

    def update_cart_display(self):
        self.cart_table.setRowCount(len(self.cart))
        total = 0
        for i, item in enumerate(self.cart):
            row_total = item['price'] * item['quantity']
            total += row_total
            
            # Item Name
            self.cart_table.setItem(i, 0, QTableWidgetItem(item['product_name']))
            
            # Price
            self.cart_table.setItem(i, 1, QTableWidgetItem(f"₦{item['price']:,.2f}"))
            
            # Qty with modifiers
            qty_widget = QWidget()
            qty_layout = QHBoxLayout(qty_widget)
            qty_layout.setContentsMargins(2, 2, 2, 2)
            qty_layout.setSpacing(4)
            
            minus_btn = QPushButton("-")
            minus_btn.setFixedSize(20, 20)
            minus_btn.clicked.connect(lambda _, idx=i: self.change_qty(idx, -1))
            
            qty_label = QLabel(str(item['quantity']))
            qty_label.setAlignment(Qt.AlignCenter)
            
            plus_btn = QPushButton("+")
            plus_btn.setFixedSize(20, 20)
            plus_btn.clicked.connect(lambda _, idx=i: self.change_qty(idx, 1))
            
            qty_layout.addWidget(minus_btn)
            qty_layout.addWidget(qty_label)
            qty_layout.addWidget(plus_btn)
            self.cart_table.setCellWidget(i, 2, qty_widget)
            
            # Total with Delete button
            total_widget = QWidget()
            total_layout = QHBoxLayout(total_widget)
            total_layout.setContentsMargins(4, 2, 4, 2)
            
            total_label = QLabel(f"₦{row_total:,.2f}")
            total_layout.addWidget(total_label)
            total_layout.addStretch()
            
            del_btn = QPushButton("×")
            del_btn.setFixedSize(20, 20)
            del_btn.setStyleSheet(f"background-color: {Theme.DANGER}; color: white; border-radius: 10px; font-weight: bold;")
            del_btn.clicked.connect(lambda _, idx=i: self.remove_from_cart(idx))
            total_layout.addWidget(del_btn)
            
            self.cart_table.setCellWidget(i, 3, total_widget)

        subtotal = total
        vat = total * 0.075
        grand_total = subtotal + vat
        
        self.subtotal_label.setText(f"₦{subtotal:,.2f}")
        self.vat_label.setText(f"₦{vat:,.2f}")
        self.total_label.setText(f"₦{grand_total:,.2f}")

    def change_qty(self, index, delta):
        if 0 <= index < len(self.cart):
            self.cart[index]['quantity'] += delta
            if self.cart[index]['quantity'] < 1:
                self.remove_from_cart(index)
            else:
                self.update_cart_display()

    def remove_from_cart(self, index):
        if 0 <= index < len(self.cart):
            self.cart.pop(index)
            self.update_cart_display()

    def handle_hold_sale(self):
        """Suspend the current cart."""
        if not self.cart:
            return
            
        ref, ok = QInputDialog.getText(self, "Hold Sale", "Enter reference name (optional):")
        if not ok:
            return
            
        success, msg, suspended_id = self.sales_service.suspend_sale(
            user_id=1, # Placeholder
            store_id=self.store_id,
            cart=self.cart,
            reference=ref
        )
        
        if success:
            QMessageBox.information(self, "Sale Held", f"Sale saved with reference: {ref or suspended_id}")
            self.cart = []
            self.update_cart_display()
        else:
            QMessageBox.critical(self, "Error", msg)

    def handle_recall_sale(self):
        """Recall a suspended sale."""
        if self.cart:
            res = QMessageBox.question(self, "Clear Cart?", "Recalling a sale will clear your current cart. Proceed?", 
                                     QMessageBox.Yes | QMessageBox.No)
            if res == QMessageBox.No:
                return

        dialog = SuspendedSalesDialog(self.sales_service, self.store_id, self)
        if dialog.exec_():
            suspended_id = dialog.get_selected_id()
            if not suspended_id: return
            
            items = self.sales_service.get_suspended_sale_items(suspended_id)
            if items:
                self.cart = []
                for item in items:
                    self.cart.append({
                        'product_name': item['product_name'],
                        'batch_id': item['batch_id'],
                        'batch_number': item['batch_number'],
                        'price': item['price'],
                        'quantity': item['quantity']
                    })
                
                # Cleanup: Delete from suspended sales after recall
                self.sales_service.delete_suspended_sale(suspended_id)
                self.update_cart_display()
                QMessageBox.information(self, "Sale Recalled", "Transaction restored to cart.")

    def handle_customer_select(self):
        """Open customer selector and assign to sale."""
        if not self.customer_service:
            QMessageBox.warning(self, "Service Error", "Customer service not available.")
            return
            
        dialog = CustomerSelectorDialog(self.customer_service, self)
        if dialog.exec_():
            self.current_customer = dialog.get_selected()
            if self.current_customer:
                self.customer_btn.setText(f"CUST: {self.current_customer['name']}")
                self.customer_btn.setStyleSheet(f"color: {Theme.SUCCESS}; font-weight: bold; font-size: 12px; border: 1px solid {Theme.SUCCESS}; padding: 4px 8px; border-radius: 4px;")

    def handle_checkout(self):
        """Open the payment dialog and finalize sale."""
        if not self.cart:
            QMessageBox.warning(self, "Empty Cart", "Please add items to the cart before checkout.")
            return
            
        dialog = PaymentDialog(
            cart=self.cart, 
            sales_service=self.sales_service, 
            user_id=1, # Placeholder
            store_id=self.store_id,
            parent=self
        )
        
        if dialog.exec_():
            # Sale completed!
            self.cart = []
            self.current_customer = None
            self.customer_btn.setText("SELECT CUSTOMER")
            self.customer_btn.setStyleSheet(f"color: {Theme.PRIMARY}; font-weight: bold; font-size: 12px; border: 1px solid {Theme.PRIMARY}; padding: 4px 8px; border-radius: 4px;")
            self.update_cart_display()
            self.search_input.clear()
            self.catalog_table.setRowCount(0)
            QMessageBox.information(self, "Success", "Transaction finalized and bill closed.")

