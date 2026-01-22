"""
Purchase Order UI Components

This module contains UI components for purchase order management,
extracted from the monolithic ui.py file during Phase 1 refactoring.
Uses modern UI components and constants for improved maintainability.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QFrame, QGroupBox, QFormLayout,
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit,
    QTextEdit, QScrollArea, QSplitter, QProgressBar, QDialog,
    QDialogButtonBox, QTableWidgetItem, QListWidget, QListWidgetItem,
    QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont

from .ui_constants import Colors, Fonts, Dimensions, Styles, Messages
from .ui_components import (
    StyledButton, FormField, Card, LoadingIndicator, ConfirmationDialog,
    StyledTable, SearchWidget, StatusBar, show_message, show_error,
    show_success, ask_confirmation, get_input, WorkerThread
)
from .models import StoreService, SupplierService, PurchaseOrderService, ProductService, get_session


class CreatePurchaseOrderDialog(QDialog):
    """Dialog for creating new purchase orders."""

    def __init__(self, parent=None, session=None):
        super().__init__(parent)
        self.session = session or get_session()
        self.supplier_service = SupplierService(self.session)
        self.product_service = ProductService(self.session)
        self.purchase_order_service = PurchaseOrderService(self.session)

        self.setWindowTitle("Create Purchase Order")
        self.setModal(True)
        self.setMinimumSize(1200, 900)
        self.resize(1200, 900)

        self.setup_ui()
        self.load_stores()
        self.load_suppliers()
        self.load_products()

    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Store/Warehouse selection
        store_layout = QHBoxLayout()
        store_layout.addWidget(QLabel("Store/Warehouse:"))
        self.store_combo = QComboBox()
        self.store_combo.setFixedHeight(Dimensions.INPUT_HEIGHT)
        store_layout.addWidget(self.store_combo)
        layout.addLayout(store_layout)

        # Supplier selection
        supplier_layout = QHBoxLayout()
        supplier_layout.addWidget(QLabel("Supplier:"))
        self.supplier_combo = QComboBox()
        self.supplier_combo.setFixedHeight(Dimensions.INPUT_HEIGHT)
        supplier_layout.addWidget(self.supplier_combo)
        layout.addLayout(supplier_layout)

        # Expected delivery date
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Expected Delivery Date:"))
        self.delivery_date = QDateEdit()
        self.delivery_date.setDate(QDate.currentDate().addDays(7))
        self.delivery_date.setFixedHeight(Dimensions.INPUT_HEIGHT)
        date_layout.addWidget(self.delivery_date)
        layout.addLayout(date_layout)

        # Products section
        products_label = QLabel("Products:")
        products_label.setFont(Fonts.SUBTITLE)
        layout.addWidget(products_label)

        # Product selection and add button
        add_product_layout = QHBoxLayout()
        add_product_layout.addWidget(QLabel("Product:"))
        self.product_combo = QComboBox()
        self.product_combo.setFixedHeight(Dimensions.INPUT_HEIGHT)
        add_product_layout.addWidget(self.product_combo)

        add_product_layout.addWidget(QLabel("Quantity:"))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 10000)
        self.quantity_spin.setValue(100)
        self.quantity_spin.setFixedHeight(Dimensions.INPUT_HEIGHT)
        add_product_layout.addWidget(self.quantity_spin)

        add_product_layout.addWidget(QLabel("Cost Price:"))
        self.cost_price_spin = QDoubleSpinBox()
        self.cost_price_spin.setRange(0, 1000000)
        self.cost_price_spin.setValue(0.00)
        self.cost_price_spin.setFixedHeight(Dimensions.INPUT_HEIGHT)
        add_product_layout.addWidget(self.cost_price_spin)

        self.add_product_btn = StyledButton("Add Product", "success")
        self.add_product_btn.clicked.connect(self.add_product_to_order)
        add_product_layout.addWidget(self.add_product_btn)

        layout.addLayout(add_product_layout)

        # Products table
        self.products_table = StyledTable([
            "Product", "Quantity", "Cost Price", "Total", "Actions"
        ])
        self.products_table.setColumnWidth(0, 200)
        self.products_table.setColumnWidth(4, 100)
        layout.addWidget(self.products_table)

        # Notes
        notes_layout = QVBoxLayout()
        notes_layout.addWidget(QLabel("Notes:"))
        self.notes_text = QTextEdit()
        self.notes_text.setFixedHeight(60)
        notes_layout.addWidget(self.notes_text)
        layout.addLayout(notes_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_draft_btn = StyledButton("Save as Draft", "warning")
        self.save_draft_btn.clicked.connect(self.save_as_draft)
        button_layout.addWidget(self.save_draft_btn)

        self.submit_btn = StyledButton("Submit for Approval", "success")
        self.submit_btn.clicked.connect(self.submit_order)
        button_layout.addWidget(self.submit_btn)

        self.cancel_btn = StyledButton("Cancel", "danger")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Data storage
        self.order_items = []

    def load_suppliers(self):
        """Load suppliers into combo box."""
        try:
            suppliers = self.supplier_service.get_all_suppliers()
            self.supplier_combo.clear()
            for supplier in suppliers:
                self.supplier_combo.addItem(supplier["name"], supplier["id"])
        except Exception as e:
            show_error(self, f"Error loading suppliers: {str(e)}")

    def load_stores(self):
        """Load stores into combo box."""
        try:
            store_service = StoreService(self.session)
            stores = store_service.get_all_stores()
            self.store_combo.clear()
            for store in stores:
                self.store_combo.addItem(store["name"], store["id"])
        except Exception as e:
            show_error(self, f"Error loading stores: {str(e)}")

    def load_products(self):
        """Load products into combo box."""
        try:
            products = self.product_service.get_all_products()
            self.product_combo.clear()
            for product in products:
                self.product_combo.addItem(product["name"], product["id"])
        except Exception as e:
            show_error(self, f"Error loading products: {str(e)}")

    def add_product_to_order(self):
        """Add selected product to the order."""
        product_name = self.product_combo.currentText()
        product_id = self.product_combo.currentData()
        quantity = self.quantity_spin.value()
        cost_price = self.cost_price_spin.value()

        if not product_name or quantity <= 0:
            show_error(self, "Please select a product and enter a valid quantity.")
            return

        # Check if product already exists
        for item in self.order_items:
            if item["product_id"] == product_id:
                show_error(self, "Product already added to order.")
                return

        total = quantity * cost_price
        self.order_items.append({
            "product_id": product_id,
            "quantity_ordered": quantity,
            "expected_cost_price": cost_price,
            "notes": ""
        })

        # Add to table
        remove_btn = StyledButton("Remove", "danger")
        remove_btn.setFixedWidth(80)
        remove_btn.clicked.connect(lambda: self.remove_product(product_id))

        self.products_table.add_row([
            product_name,
            str(quantity),
            f"₦{cost_price:.2f}",
            f"₦{total:.2f}",
            remove_btn
        ])

    def remove_product(self, product_id):
        """Remove product from order."""
        self.order_items = [item for item in self.order_items if item["product_id"] != product_id]
        self.refresh_products_table()

    def refresh_products_table(self):
        """Refresh the products table."""
        self.products_table.clear_table()
        for item in self.order_items:
            product = self.product_service.get_product(item["product_id"])
            if product:
                total = item["quantity_ordered"] * item["expected_cost_price"]
                remove_btn = StyledButton("Remove", "danger")
                remove_btn.setFixedWidth(80)
                remove_btn.clicked.connect(lambda: self.remove_product(item["product_id"]))

                self.products_table.add_row([
                    product["name"],
                    str(item["quantity_ordered"]),
                    f"₦{item['expected_cost_price']:.2f}",
                    f"₦{total:.2f}",
                    ""  # Placeholder for button
                ])

    def validate_order(self):
        """Validate order data."""
        if self.store_combo.currentData() is None:
            show_error(self, "Please select a store/warehouse.")
            return False

        if self.supplier_combo.currentData() is None:
            show_error(self, "Please select a supplier.")
            return False

        if not self.order_items:
            show_error(self, "Please add at least one product to the order.")
            return False

        return True

    def save_as_draft(self):
        """Save order as draft."""
        if not self.validate_order():
            return

        try:
            supplier_id = self.supplier_combo.currentData()
            store_id = self.store_combo.currentData()
            user_id = 1   # Default user for now
            expected_date = self.delivery_date.date().toPyDate()
            notes = self.notes_text.toPlainText()

            result = self.purchase_order_service.create_purchase_order(
                supplier_id=supplier_id,
                store_id=store_id,
                user_id=user_id,
                items=self.order_items,
                expected_delivery_date=expected_date,
                notes=notes
            )

            show_success(self, f"Purchase order {result['po_number']} saved as draft.")
            self.accept()

        except Exception as e:
            show_error(self, f"Error saving purchase order: {str(e)}")

    def submit_order(self):
        """Submit order for approval."""
        if not self.validate_order():
            return

        try:
            supplier_id = self.supplier_combo.currentData()
            store_id = self.store_combo.currentData()
            user_id = 1   # Default user for now
            expected_date = self.delivery_date.date().toPyDate()
            notes = self.notes_text.toPlainText()

            result = self.purchase_order_service.create_purchase_order(
                supplier_id=supplier_id,
                store_id=store_id,
                user_id=user_id,
                items=self.order_items,
                expected_delivery_date=expected_date,
                notes=notes
            )

            # Submit for approval
            po_id = result['id']
            self.purchase_order_service.submit_purchase_order(po_id, user_id)

            show_success(self, f"Purchase order {result['po_number']} submitted for approval.")
            self.accept()

        except Exception as e:
            show_error(self, f"Error submitting purchase order: {str(e)}")


class PurchaseOrderUI:
    """UI components for purchase order management."""

    def __init__(self, main_window):
        self.main_window = main_window
        self.session = main_window.session if hasattr(main_window, 'session') else get_session()
        self.product_service = ProductService(self.session)

    def create_purchasing_tab(self) -> QWidget:
        """Create purchasing management tab with modern UI."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(Dimensions.MARGIN_MEDIUM, Dimensions.MARGIN_MEDIUM,
                                Dimensions.MARGIN_MEDIUM, Dimensions.MARGIN_MEDIUM)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Title
        title = QLabel("🛒 PURCHASING MANAGEMENT")
        title.setFont(Fonts.TITLE)
        title.setStyleSheet(f"color: {Colors.PRIMARY}; margin-bottom: {Dimensions.SPACING_LARGE}px;")
        layout.addWidget(title)

        # Control buttons card
        buttons_card = Card("⚡ Quick Actions")
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        create_po_btn = StyledButton("📝 Create Purchase Order", "success")
        create_po_btn.clicked.connect(self._create_new_purchase_order)
        buttons_layout.addWidget(create_po_btn)

        receive_goods_btn = StyledButton("📦 Receive Goods", "primary")
        receive_goods_btn.clicked.connect(self.main_window.receive_stock)
        buttons_layout.addWidget(receive_goods_btn)

        view_suppliers_btn = StyledButton("🏢 Suppliers", "info")
        view_suppliers_btn.clicked.connect(self._view_suppliers)
        buttons_layout.addWidget(view_suppliers_btn)

        buttons_card.add_widget(QWidget())
        buttons_card.layout.addLayout(buttons_layout)
        layout.addWidget(buttons_card)

        # Purchase Orders table card
        po_card = Card("📋 Recent Purchase Orders")
        self.purchase_orders_table = StyledTable([
            "PO #", "Supplier", "Date", "Status", "Total", "Actions"
        ])
        self.purchase_orders_table.setColumnWidth(1, 200)
        self.purchase_orders_table.setColumnWidth(5, 150)

        # Sample data - replace with actual data loading
        sample_pos = [
            ["PO-2024-001", "MediPharm Ltd", "2024-01-15", "Pending", "₦125,000"],
            ["PO-2024-002", "HealthCorp", "2024-01-20", "Approved", "₦89,500"],
            ["PO-2024-003", "PharmaPlus", "2024-01-25", "Delivered", "₦156,200"],
        ]

        for po in sample_pos:
            view_btn = StyledButton("👁 View", "primary")
            view_btn.setFixedWidth(80)
            self.purchase_orders_table.add_row(po + [""])

        po_card.add_widget(self.purchase_orders_table)
        layout.addWidget(po_card)

        # Low stock alerts card
        alerts_card = Card("⚠ Items Needing Replenishment")
        self.low_stock_table = StyledTable([
            "Product", "Current Stock", "Min Required", "Suggested Order"
        ])
        self.low_stock_table.setColumnWidth(0, 250)

        # Sample low stock data
        low_stock_items = [
            ["Paracetamol 500mg", "15", "50", "100"],
            ["Amoxicillin 250mg", "8", "25", "50"],
            ["Ibuprofen 200mg", "12", "30", "75"],
        ]

        for item in low_stock_items:
            self.low_stock_table.add_row(item)

        alerts_card.add_widget(self.low_stock_table)
        layout.addWidget(alerts_card)

        widget.setLayout(layout)
        return widget

    def create_purchase_order_tab(self) -> QWidget:
        """Create purchase order management tab with modern UI."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(Dimensions.MARGIN_MEDIUM, Dimensions.MARGIN_MEDIUM,
                                Dimensions.MARGIN_MEDIUM, Dimensions.MARGIN_MEDIUM)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Title
        title = QLabel("📝 PURCHASE ORDER MANAGEMENT")
        title.setFont(Fonts.TITLE)
        title.setStyleSheet(f"color: {Colors.PRIMARY}; margin-bottom: {Dimensions.SPACING_LARGE}px;")
        layout.addWidget(title)

        # Control buttons card
        buttons_card = Card("⚡ Actions")
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        create_po_btn = StyledButton("📝 Create Purchase Order", "success")
        create_po_btn.clicked.connect(self._create_new_purchase_order)
        buttons_layout.addWidget(create_po_btn)

        view_po_btn = StyledButton("👁 View Purchase Orders", "primary")
        view_po_btn.clicked.connect(self._view_purchase_orders)
        buttons_layout.addWidget(view_po_btn)

        buttons_card.add_widget(QWidget())
        buttons_card.layout.addLayout(buttons_layout)
        layout.addWidget(buttons_card)

        # Purchase Orders table card
        po_card = Card("📋 Recent Purchase Orders")
        self.purchase_orders_table = StyledTable([
            "PO #", "Supplier", "Date", "Status", "Total", "Actions"
        ])
        self.purchase_orders_table.setColumnWidth(1, 200)
        self.purchase_orders_table.setColumnWidth(5, 150)

        # Load real purchase order data
        self.load_purchase_orders()

        po_card.add_widget(self.purchase_orders_table)
        layout.addWidget(po_card)

        widget.setLayout(layout)
        return widget

    def create_purchase_invoice_tab(self) -> QWidget:
        """Create purchase invoice management tab with modern UI."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(Dimensions.MARGIN_MEDIUM, Dimensions.MARGIN_MEDIUM,
                                Dimensions.MARGIN_MEDIUM, Dimensions.MARGIN_MEDIUM)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Title
        title = QLabel("📄 PURCHASE INVOICE MANAGEMENT")
        title.setFont(Fonts.TITLE)
        title.setStyleSheet(f"color: {Colors.PRIMARY}; margin-bottom: {Dimensions.SPACING_LARGE}px;")
        layout.addWidget(title)

        # Control buttons card
        buttons_card = Card("⚡ Actions")
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        create_invoice_btn = StyledButton("📄 Create Purchase Invoice", "danger")
        create_invoice_btn.clicked.connect(self._create_new_purchase_invoice)
        buttons_layout.addWidget(create_invoice_btn)

        view_invoices_btn = StyledButton("📋 View Invoices", "primary")
        view_invoices_btn.clicked.connect(self._view_purchase_invoices)
        buttons_layout.addWidget(view_invoices_btn)

        buttons_card.add_widget(QWidget())
        buttons_card.layout.addLayout(buttons_layout)
        layout.addWidget(buttons_card)

        # Purchase Invoices table card
        invoices_card = Card("📋 Recent Purchase Invoices")
        self.purchase_invoices_table = StyledTable([
            "Invoice #", "Supplier", "PO #", "Date", "Status", "Total", "Actions"
        ])
        self.purchase_invoices_table.setColumnWidth(1, 150)
        self.purchase_invoices_table.setColumnWidth(6, 150)

        # Sample data
        sample_invoices = [
            ["INV-2024-001", "MediPharm Ltd", "PO-2024-001", "2024-01-16", "Paid", "₦125,000"],
            ["INV-2024-002", "HealthCorp", "PO-2024-002", "2024-01-21", "Pending", "₦89,500"],
            ["INV-2024-003", "PharmaPlus", "PO-2024-003", "2024-01-26", "Paid", "₦156,200"],
        ]

        for invoice in sample_invoices:
            view_btn = StyledButton("👁 View", "primary")
            view_btn.setFixedWidth(80)
            self.purchase_invoices_table.add_row(invoice + [""])

        invoices_card.add_widget(self.purchase_invoices_table)
        layout.addWidget(invoices_card)

        widget.setLayout(layout)
        return widget

    def create_suppliers_tab(self) -> QWidget:
        """Create suppliers management tab with modern UI."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(Dimensions.MARGIN_MEDIUM, Dimensions.MARGIN_MEDIUM,
                                Dimensions.MARGIN_MEDIUM, Dimensions.MARGIN_MEDIUM)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Title
        title = QLabel("🏢 SUPPLIERS MANAGEMENT")
        title.setFont(Fonts.TITLE)
        title.setStyleSheet(f"color: {Colors.PRIMARY}; margin-bottom: {Dimensions.SPACING_LARGE}px;")
        layout.addWidget(title)

        # Control buttons card
        buttons_card = Card("⚡ Actions")
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        add_supplier_btn = StyledButton("🏢 Add Supplier", "success")
        add_supplier_btn.clicked.connect(self._add_new_supplier)
        buttons_layout.addWidget(add_supplier_btn)

        manage_suppliers_btn = StyledButton("📋 Manage Suppliers", "primary")
        manage_suppliers_btn.clicked.connect(self._manage_suppliers)
        buttons_layout.addWidget(manage_suppliers_btn)

        buttons_card.add_widget(QWidget())
        buttons_card.layout.addLayout(buttons_layout)
        layout.addWidget(buttons_card)

        # Suppliers table card
        suppliers_card = Card("📋 Supplier Directory")
        self.suppliers_table = StyledTable([
            "ID", "Name", "Contact Person", "Phone", "Email", "Status", "Actions"
        ])
        self.suppliers_table.setColumnWidth(1, 200)
        self.suppliers_table.setColumnWidth(2, 150)
        self.suppliers_table.setColumnWidth(6, 150)

        # Sample data
        sample_suppliers = [
            ["1", "MediPharm Ltd", "John Smith", "+234-123-4567", "john@medipharm.com", "Active"],
            ["2", "HealthCorp", "Sarah Johnson", "+234-234-5678", "sarah@healthcorp.com", "Active"],
            ["3", "PharmaPlus", "Mike Davis", "+234-345-6789", "mike@pharmaplus.com", "Active"],
        ]

        for supplier in sample_suppliers:
            edit_btn = StyledButton("✏ Edit", "warning")
            edit_btn.setFixedWidth(80)
            self.suppliers_table.add_row(supplier + [""])

        suppliers_card.add_widget(self.suppliers_table)
        layout.addWidget(suppliers_card)

        widget.setLayout(layout)
        return widget

    def create_warehouse_tab(self) -> QWidget:
        """Create warehouse management tab with modern UI."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(Dimensions.MARGIN_MEDIUM, Dimensions.MARGIN_MEDIUM,
                                Dimensions.MARGIN_MEDIUM, Dimensions.MARGIN_MEDIUM)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Title
        title = QLabel("🏭 WAREHOUSE MANAGEMENT")
        title.setFont(Fonts.TITLE)
        title.setStyleSheet(f"color: {Colors.PRIMARY}; margin-bottom: {Dimensions.SPACING_LARGE}px;")
        layout.addWidget(title)

        # Control buttons card
        buttons_card = Card("⚡ Actions")
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        add_location_btn = StyledButton("🏭 Add Warehouse Location", "success")
        add_location_btn.clicked.connect(self._add_warehouse_location)
        buttons_layout.addWidget(add_location_btn)

        manage_stock_btn = StyledButton("📦 Manage Stock Locations", "primary")
        manage_stock_btn.clicked.connect(self._manage_stock_locations)
        buttons_layout.addWidget(manage_stock_btn)

        buttons_card.add_widget(QWidget())
        buttons_card.layout.addLayout(buttons_layout)
        layout.addWidget(buttons_card)

        # Warehouse locations table card
        warehouse_card = Card("📋 Warehouse Locations & Stock Distribution")
        self.warehouse_table = StyledTable([
            "Location", "Product", "Batch", "Quantity", "Expiry Date", "Status"
        ])
        self.warehouse_table.setColumnWidth(0, 150)
        self.warehouse_table.setColumnWidth(1, 200)
        self.warehouse_table.setColumnWidth(5, 100)

        # Sample data
        sample_warehouse = [
            ["Main Warehouse", "Paracetamol 500mg", "BATCH-001", "500", "2025-12-31", "Good"],
            ["Main Warehouse", "Amoxicillin 250mg", "BATCH-002", "300", "2025-10-15", "Good"],
            ["Backup Storage", "Ibuprofen 200mg", "BATCH-003", "200", "2025-08-20", "Low"],
        ]

        for item in sample_warehouse:
            self.warehouse_table.add_row(item)

        warehouse_card.add_widget(self.warehouse_table)
        layout.addWidget(warehouse_card)

        widget.setLayout(layout)
        return widget

    # Action methods
    def _create_new_purchase_order(self):
        """Create a new purchase order."""
        dialog = CreatePurchaseOrderDialog(self.main_window, self.session)
        dialog.exec_()

    def _view_purchase_orders(self):
        """View all purchase orders."""
        show_message(self.main_window, "View Purchase Orders", "Purchase orders list would open here.")

    def _create_new_purchase_invoice(self):
        """Create a new purchase invoice."""
        show_message(self.main_window, "Create Purchase Invoice", "Purchase invoice creation dialog would open here.")

    def _view_purchase_invoices(self):
        """View all purchase invoices."""
        show_message(self.main_window, "View Purchase Invoices", "Purchase invoices list would open here.")

    def _view_suppliers(self):
        """View suppliers."""
        show_message(self.main_window, "View Suppliers", "Suppliers management would open here.")

    def _add_new_supplier(self):
        """Add a new supplier."""
        show_message(self.main_window, "Add Supplier", "Add supplier dialog would open here.")

    def _manage_suppliers(self):
        """Manage suppliers."""
        show_message(self.main_window, "Manage Suppliers", "Suppliers management dialog would open here.")

    def _add_warehouse_location(self):
        """Add a new warehouse location."""
        show_message(self.main_window, "Add Warehouse Location", "Add warehouse location dialog would open here.")

    def _manage_stock_locations(self):
        """Manage stock locations."""
        show_message(self.main_window, "Manage Stock Locations", "Stock locations management would open here.")

    def load_purchase_orders(self):
        """Load purchase orders from database and populate table."""
        try:
            po_service = PurchaseOrderService(self.session)
            supplier_service = SupplierService(self.session)
            store_service = StoreService(self.session)

            # Get primary store for filtering purchase orders
            primary_store = store_service.get_primary_store()
            if not primary_store:
                show_error(self.main_window, "No primary store configured.")
                return

            # Get all purchase orders for the primary store
            purchase_orders = po_service.get_purchase_orders_by_status(primary_store["id"])

            self.purchase_orders_table.clear_table()

            for po in purchase_orders:
                # Get supplier name
                supplier = supplier_service.get_supplier(po["supplier_id"])
                supplier_name = supplier["name"] if supplier else "Unknown"

                # Format date
                date_str = po["created_at"].strftime("%Y-%m-%d") if po["created_at"] else ""

                # Format total
                total_str = f"₦{po['total_expected_amount']:.2f}" if po["total_expected_amount"] else "₦0.00"

                # Status with color coding
                status = po["status"].title()

                # Create action buttons
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                actions_layout.setSpacing(5)

                view_btn = StyledButton("👁 View", "primary")
                view_btn.setFixedWidth(70)
                view_btn.clicked.connect(lambda checked, po_id=po["id"]: self._view_purchase_order_details(po_id))
                actions_layout.addWidget(view_btn)

                # Add approve/reject buttons based on status
                if po["status"] == "submitted":
                    approve_btn = StyledButton("✓ Approve", "success")
                    approve_btn.setFixedWidth(80)
                    approve_btn.clicked.connect(lambda checked, po_id=po["id"]: self._approve_purchase_order(po_id))
                    actions_layout.addWidget(approve_btn)

                    reject_btn = StyledButton("✗ Reject", "danger")
                    reject_btn.setFixedWidth(70)
                    reject_btn.clicked.connect(lambda checked, po_id=po["id"]: self._reject_purchase_order(po_id))
                    actions_layout.addWidget(reject_btn)

                actions_layout.addStretch()

                self.purchase_orders_table.add_row([
                    po["po_number"],
                    supplier_name,
                    date_str,
                    status,
                    total_str,
                    actions_widget
                ])

        except Exception as e:
            show_error(self.main_window, f"Error loading purchase orders: {str(e)}")

    def _view_purchase_order_details(self, po_id):
        """View detailed information about a purchase order."""
        try:
            po_service = PurchaseOrderService(self.session)
            supplier_service = SupplierService(self.session)
            store_service = StoreService(self.session)

            po = po_service.get_purchase_order(po_id)
            if not po:
                show_error(self.main_window, "Purchase order not found.")
                return

            supplier = supplier_service.get_supplier(po["supplier_id"])
            store = store_service.get_store(po["store_id"])

            # Create detailed view dialog
            dialog = QDialog(self.main_window)
            dialog.setWindowTitle(f"Purchase Order Details - {po['po_number']}")
            dialog.setGeometry(200, 200, 800, 600)

            layout = QVBoxLayout(dialog)

            # Header info
            header_layout = QVBoxLayout()
            header_layout.addWidget(QLabel(f"<b>PO Number:</b> {po['po_number']}"))
            header_layout.addWidget(QLabel(f"<b>Supplier:</b> {supplier['name'] if supplier else 'Unknown'}"))
            header_layout.addWidget(QLabel(f"<b>Store:</b> {store['name'] if store else 'Unknown'}"))
            header_layout.addWidget(QLabel(f"<b>Status:</b> {po['status'].title()}"))
            header_layout.addWidget(QLabel(f"<b>Expected Delivery:</b> {po['expected_delivery_date']}"))
            header_layout.addWidget(QLabel(f"<b>Total Amount:</b> ₦{po['total_expected_amount']:.2f}"))
            if po["notes"]:
                header_layout.addWidget(QLabel(f"<b>Notes:</b> {po['notes']}"))

            layout.addLayout(header_layout)

            # Items table
            items_label = QLabel("<b>Order Items:</b>")
            layout.addWidget(items_label)

            items_table = StyledTable([
                "Product", "Quantity Ordered", "Cost Price", "Total", "Quantity Received"
            ])
            items_table.setColumnWidth(0, 200)

            po_items = po_service.get_po_items(po_id)
            for item in po_items:
                product = self.product_service.get_product(item["product_id"])
                product_name = product["name"] if product else f"Product ID: {item['product_id']}"

                total = item["quantity_ordered"] * (item["expected_cost_price"] or 0)

                items_table.add_row([
                    product_name,
                    str(item["quantity_ordered"]),
                    f"₦{item['expected_cost_price']:.2f}" if item["expected_cost_price"] else "₦0.00",
                    f"₦{total:.2f}",
                    str(item["quantity_received"]) if item["quantity_received"] else "0"
                ])

            layout.addWidget(items_table)

            # Close button
            close_btn = StyledButton("Close", "primary")
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn)

            dialog.exec_()

        except Exception as e:
            show_error(self.main_window, f"Error viewing purchase order details: {str(e)}")

    def _approve_purchase_order(self, po_id):
        """Approve a purchase order."""
        try:
            reply = ask_confirmation(self.main_window, "Approve Purchase Order",
                                   "Are you sure you want to approve this purchase order?")
            if reply:
                po_service = PurchaseOrderService(self.session)
                po_service.approve_purchase_order(po_id, 1)  # Default approver ID
                show_success(self.main_window, "Purchase order approved successfully.")
                self.load_purchase_orders()  # Refresh table
        except Exception as e:
            show_error(self.main_window, f"Error approving purchase order: {str(e)}")

    def _reject_purchase_order(self, po_id):
        """Reject a purchase order."""
        try:
            reason, ok = get_input(self.main_window, "Reject Purchase Order",
                                 "Please provide a reason for rejection:")
            if ok and reason.strip():
                po_service = PurchaseOrderService(self.session)
                po_service.reject_purchase_order(po_id, 1, reason.strip())  # Default approver ID
                show_success(self.main_window, "Purchase order rejected.")
                self.load_purchase_orders()  # Refresh table
        except Exception as e:
            show_error(self.main_window, f"Error rejecting purchase order: {str(e)}")
