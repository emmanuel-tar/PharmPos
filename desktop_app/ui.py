"""
PharmaPOS NG - Desktop Application (PyQt5)

Main entry point for the pharmacy billing and inventory desktop application.
"""

import sys
from decimal import Decimal
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QDialog,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QMessageBox,
    QDateEdit,
    QDoubleSpinBox,
    QFileDialog,
    QTextEdit,
    QScrollArea,
    QFrame,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon, QFont

from desktop_app.auth import AuthenticationService, UserSession
from desktop_app.models import (
    StoreService,
    UserService,
    ProductService,
    InventoryService,
    SalesService,
    get_session,
)
from desktop_app.sales import SalesTransaction
from desktop_app.printer import ThermalPrinter, PrinterType, ReceiptGenerator
from desktop_app.inventory import BatchManager, InventoryAlerts
from desktop_app.reports import SalesReporter, InventoryReporter
from desktop_app.product_manager import ProductImportExporter
from desktop_app.config import load_printer_config, save_printer_config


# --- Printer Settings Dialog -----------------------------------------------
class PrinterSettingsDialog(QDialog):
    """Dialog to configure thermal printer settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Printer Settings")
        self.setGeometry(200, 200, 600, 500)
        self.setup_ui()
        self.load_config()

    def setup_ui(self) -> None:
        """Setup printer settings UI."""
        layout = QVBoxLayout()

        # Enable/Disable
        enable_layout = QHBoxLayout()
        enable_layout.addWidget(QLabel("Enable Thermal Printer:"))
        self.enable_checkbox = QLineEdit()
        self.enable_checkbox.setText("No")
        enable_layout.addWidget(self.enable_checkbox)
        layout.addLayout(enable_layout)

        # Printer Type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Printer Type:"))
        self.printer_type_combo = QComboBox()
        self.printer_type_combo.addItems(["FILE", "USB", "SERIAL", "NETWORK"])
        self.printer_type_combo.currentTextChanged.connect(self.on_printer_type_changed)
        type_layout.addWidget(self.printer_type_combo)
        layout.addLayout(type_layout)

        # USB Settings
        layout.addWidget(QLabel("<b>USB Settings</b>"))
        usb_layout = QHBoxLayout()
        usb_layout.addWidget(QLabel("Vendor ID:"))
        self.usb_vendor_input = QLineEdit()
        self.usb_vendor_input.setPlaceholderText("e.g., 0x04b8")
        usb_layout.addWidget(self.usb_vendor_input)
        usb_layout.addWidget(QLabel("Product ID:"))
        self.usb_product_input = QLineEdit()
        self.usb_product_input.setPlaceholderText("e.g., 0x0202")
        usb_layout.addWidget(self.usb_product_input)
        layout.addLayout(usb_layout)

        # Serial Settings
        layout.addWidget(QLabel("<b>Serial Settings</b>"))
        serial_layout = QHBoxLayout()
        serial_layout.addWidget(QLabel("Port:"))
        self.serial_port_input = QLineEdit()
        self.serial_port_input.setPlaceholderText("e.g., /dev/ttyUSB0 or COM3")
        serial_layout.addWidget(self.serial_port_input)
        serial_layout.addWidget(QLabel("Baudrate:"))
        self.serial_baudrate_input = QSpinBox()
        self.serial_baudrate_input.setValue(9600)
        self.serial_baudrate_input.setRange(300, 921600)
        serial_layout.addWidget(self.serial_baudrate_input)
        layout.addLayout(serial_layout)

        # Network Settings
        layout.addWidget(QLabel("<b>Network Settings</b>"))
        network_layout = QHBoxLayout()
        network_layout.addWidget(QLabel("Host:"))
        self.network_host_input = QLineEdit()
        self.network_host_input.setPlaceholderText("e.g., 192.168.1.100")
        network_layout.addWidget(self.network_host_input)
        network_layout.addWidget(QLabel("Port:"))
        self.network_port_input = QSpinBox()
        self.network_port_input.setValue(9100)
        self.network_port_input.setRange(1, 65535)
        network_layout.addWidget(self.network_port_input)
        layout.addLayout(network_layout)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_config)
        test_btn = QPushButton("Test Printer")
        test_btn.clicked.connect(self.test_printer)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(test_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_config(self) -> None:
        """Load printer configuration from config.json."""
        config = load_printer_config()
        self.enable_checkbox.setText("Yes" if config.get("enabled") else "No")
        self.printer_type_combo.setCurrentText(config.get("type", "FILE"))

        usb_cfg = config.get("usb", {})
        self.usb_vendor_input.setText(usb_cfg.get("vendor_id", "0x04b8"))
        self.usb_product_input.setText(usb_cfg.get("product_id", "0x0202"))

        serial_cfg = config.get("serial", {})
        self.serial_port_input.setText(serial_cfg.get("port", "/dev/ttyUSB0"))
        self.serial_baudrate_input.setValue(serial_cfg.get("baudrate", 9600))

        network_cfg = config.get("network", {})
        self.network_host_input.setText(network_cfg.get("host", "192.168.1.100"))
        self.network_port_input.setValue(network_cfg.get("port", 9100))

    def on_printer_type_changed(self) -> None:
        """Show/hide relevant settings based on printer type."""
        printer_type = self.printer_type_combo.currentText()
        # In a more advanced UI, we'd show/hide groups based on type
        # For now, all are visible

    def save_config(self) -> None:
        """Save printer configuration."""
        config = {
            "enabled": self.enable_checkbox.text().lower() == "yes",
            "type": self.printer_type_combo.currentText(),
            "usb": {
                "vendor_id": self.usb_vendor_input.text(),
                "product_id": self.usb_product_input.text(),
            },
            "serial": {
                "port": self.serial_port_input.text(),
                "baudrate": self.serial_baudrate_input.value(),
            },
            "network": {
                "host": self.network_host_input.text(),
                "port": self.network_port_input.value(),
            },
        }
        if save_printer_config(config):
            QMessageBox.information(self, "Success", "Printer settings saved successfully.")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to save printer settings.")

    def test_printer(self) -> None:
        """Test printer connection."""
        try:
            printer_type = self.printer_type_combo.currentText()
            device_info = {}

            if printer_type == "USB":
                device_info = {
                    "idVendor": int(self.usb_vendor_input.text(), 16),
                    "idProduct": int(self.usb_product_input.text(), 16),
                }
            elif printer_type == "SERIAL":
                device_info = {
                    "port": self.serial_port_input.text(),
                    "baudrate": self.serial_baudrate_input.value(),
                }
            elif printer_type == "NETWORK":
                device_info = {
                    "host": self.network_host_input.text(),
                    "port": self.network_port_input.value(),
                }

            QMessageBox.information(self, "Test", f"Printer test for {printer_type}: Not yet implemented. Please click Save to apply settings.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Printer test failed: {e}")


# --- Stock Receiving Dialog -----------------------------------------------
class StockReceivingDialog(QDialog):
    """Dialog to receive stock with comprehensive pricing and stock alert fields."""

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.product_service = ProductService(session)
        self.result_data = None
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup stock receiving UI with pricing tiers and stock alerts."""
        self.setWindowTitle("Receive Stock - Full Details")
        self.setGeometry(100, 100, 700, 850)

        main_layout = QVBoxLayout()

        # Create scroll area for long form
        scroll = QScrollArea()
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)

        # --- Product Section ---
        layout.addWidget(QLabel("<b>Product Information</b>"))
        layout.addWidget(self._create_separator())

        layout.addWidget(QLabel("Product:"))
        self.product_combo = QComboBox()
        self.product_combo.currentIndexChanged.connect(self._on_product_changed)
        self.load_products()
        layout.addWidget(self.product_combo)

        # --- Batch Details Section ---
        layout.addWidget(QLabel("<b>Batch Details</b>"))
        layout.addWidget(self._create_separator())

        layout.addWidget(QLabel("Batch Number:"))
        self.batch_number_input = QLineEdit()
        self.batch_number_input.setPlaceholderText("e.g., BATCH-001, LOT-2025-001")
        layout.addWidget(self.batch_number_input)

        layout.addWidget(QLabel("Quantity (units):"))
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 100000)
        self.quantity_input.setValue(1)
        layout.addWidget(self.quantity_input)

        layout.addWidget(QLabel("Expiry Date:"))
        self.expiry_date_input = QDateEdit()
        self.expiry_date_input.setCalendarPopup(True)
        self.expiry_date_input.setDate(QDate.currentDate())
        self.expiry_date_input.setDateRange(QDate.currentDate(), QDate(2099, 12, 31))
        layout.addWidget(self.expiry_date_input)

        # --- Cost & Pricing Section ---
        layout.addWidget(QLabel("<b>Cost & Pricing</b>"))
        layout.addWidget(self._create_separator())

        layout.addWidget(QLabel("Cost Price (per unit, ₦):"))
        self.cost_price_input = QDoubleSpinBox()
        self.cost_price_input.setRange(0, 999999.99)
        self.cost_price_input.setDecimals(2)
        self.cost_price_input.setValue(0)
        layout.addWidget(self.cost_price_input)

        layout.addWidget(QLabel("Retail Price (per unit, ₦):"))
        self.retail_price_input = QDoubleSpinBox()
        self.retail_price_input.setRange(0, 999999.99)
        self.retail_price_input.setDecimals(2)
        self.retail_price_input.setValue(0)
        layout.addWidget(self.retail_price_input)

        # Bulk pricing layout
        bulk_layout = QHBoxLayout()
        bulk_layout.addWidget(QLabel("Bulk Price (₦):"))
        self.bulk_price_input = QDoubleSpinBox()
        self.bulk_price_input.setRange(0, 999999.99)
        self.bulk_price_input.setDecimals(2)
        bulk_layout.addWidget(self.bulk_price_input)

        bulk_layout.addWidget(QLabel("Min Qty:"))
        self.bulk_quantity_input = QSpinBox()
        self.bulk_quantity_input.setRange(1, 100000)
        self.bulk_quantity_input.setValue(10)
        bulk_layout.addWidget(self.bulk_quantity_input)
        layout.addLayout(bulk_layout)

        # Wholesale pricing layout
        wholesale_layout = QHBoxLayout()
        wholesale_layout.addWidget(QLabel("Wholesale Price (₦):"))
        self.wholesale_price_input = QDoubleSpinBox()
        self.wholesale_price_input.setRange(0, 999999.99)
        self.wholesale_price_input.setDecimals(2)
        wholesale_layout.addWidget(self.wholesale_price_input)

        wholesale_layout.addWidget(QLabel("Min Qty:"))
        self.wholesale_quantity_input = QSpinBox()
        self.wholesale_quantity_input.setRange(1, 100000)
        self.wholesale_quantity_input.setValue(50)
        wholesale_layout.addWidget(self.wholesale_quantity_input)
        layout.addLayout(wholesale_layout)

        # --- Stock Alerts Section ---
        layout.addWidget(QLabel("<b>Stock Alerts</b>"))
        layout.addWidget(self._create_separator())

        alert_layout = QHBoxLayout()
        alert_layout.addWidget(QLabel("Min Stock Alert:"))
        self.min_stock_input = QSpinBox()
        self.min_stock_input.setRange(0, 100000)
        self.min_stock_input.setValue(10)
        alert_layout.addWidget(self.min_stock_input)

        alert_layout.addWidget(QLabel("Max Stock Alert:"))
        self.max_stock_input = QSpinBox()
        self.max_stock_input.setRange(1, 1000000)
        self.max_stock_input.setValue(500)
        alert_layout.addWidget(self.max_stock_input)

        alert_layout.addWidget(QLabel("Reorder Level:"))
        self.reorder_level_input = QSpinBox()
        self.reorder_level_input.setRange(0, 100000)
        self.reorder_level_input.setValue(50)
        alert_layout.addWidget(self.reorder_level_input)
        layout.addLayout(alert_layout)

        # --- Store Section ---
        layout.addWidget(QLabel("<b>Store & Location</b>"))
        layout.addWidget(self._create_separator())

        layout.addWidget(QLabel("Store:"))
        self.store_combo = QComboBox()
        self.load_stores()
        layout.addWidget(self.store_combo)

        layout.addStretch()

        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll)

        # Buttons
        button_layout = QHBoxLayout()
        receive_btn = QPushButton("Receive Stock")
        receive_btn.setMinimumWidth(120)
        receive_btn.clicked.connect(self.accept_receive)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumWidth(120)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(receive_btn)
        button_layout.addWidget(cancel_btn)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _create_separator(self) -> QWidget:
        """Create a simple line separator."""
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #cccccc;")
        return line

    def _on_product_changed(self) -> None:
        """Update pricing fields when product changes (optional pre-fill from product defaults)."""
        # This can be used to pre-fill pricing from product master data
        pass

    def load_products(self) -> None:
        """Load products into combo box."""
        try:
            products = self.product_service.get_all_products()
            self.product_combo.clear()
            for prod in products:
                self.product_combo.addItem(
                    f"{prod['name']} ({prod['sku']})", prod["id"]
                )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load products: {str(e)}")

    def load_stores(self) -> None:
        """Load stores into combo box."""
        try:
            store_service = StoreService(self.session)
            stores = store_service.get_all_stores()
            self.store_combo.clear()
            for store in stores:
                self.store_combo.addItem(store["name"], store["id"])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load stores: {str(e)}")

    def accept_receive(self) -> None:
        """Validate and accept receiving stock."""
        # Validation
        if not self.batch_number_input.text().strip():
            QMessageBox.warning(self, "Validation", "Please enter a batch number")
            return

        if self.quantity_input.value() <= 0:
            QMessageBox.warning(self, "Validation", "Quantity must be greater than 0")
            return

        if self.cost_price_input.value() < 0:
            QMessageBox.warning(self, "Validation", "Cost price cannot be negative")
            return

        if self.retail_price_input.value() <= 0:
            QMessageBox.warning(self, "Validation", "Retail price must be greater than 0")
            return

        if self.bulk_price_input.value() < 0 or self.wholesale_price_input.value() < 0:
            QMessageBox.warning(self, "Validation", "Bulk/Wholesale prices cannot be negative")
            return

        if self.min_stock_input.value() > self.max_stock_input.value():
            QMessageBox.warning(self, "Validation", "Min stock cannot exceed Max stock")
            return

        # Store the result data
        self.result_data = {
            "product_id": self.product_combo.currentData(),
            "batch_number": self.batch_number_input.text().strip(),
            "quantity": self.quantity_input.value(),
            "cost_price": Decimal(str(self.cost_price_input.value())),
            "retail_price": Decimal(str(self.retail_price_input.value())),
            "bulk_price": Decimal(str(self.bulk_price_input.value())) if self.bulk_price_input.value() > 0 else None,
            "bulk_quantity": self.bulk_quantity_input.value() if self.bulk_price_input.value() > 0 else None,
            "wholesale_price": Decimal(str(self.wholesale_price_input.value())) if self.wholesale_price_input.value() > 0 else None,
            "wholesale_quantity": self.wholesale_quantity_input.value() if self.wholesale_price_input.value() > 0 else None,
            "min_stock": self.min_stock_input.value(),
            "max_stock": self.max_stock_input.value(),
            "reorder_level": self.reorder_level_input.value(),
            "expiry_date": self.expiry_date_input.date().toPyDate(),
            "store_id": self.store_combo.currentData(),
        }
        self.accept()


# --- Sales Cart Dialog (FEFO-based) ---------------------------------------
class SalesCartDialog(QDialog):
    """Dialog to manage sales cart with FEFO allocation."""

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.inv_service = InventoryService(session)
        self.product_service = ProductService(session)
        self.store_service = StoreService(session)
        self.cart_items = []  # List of {product_id, quantity, unit_price, batches: [{batch_id, qty}, ...]}
        self.setWindowTitle("Sales Cart (FEFO)")
        self.setGeometry(100, 100, 900, 600)
        self.init_ui()

    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()

        # Product selection section
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Product:"))
        self.product_combo = QComboBox()
        self._load_products()
        select_layout.addWidget(self.product_combo)

        select_layout.addWidget(QLabel("Quantity:"))
        self.qty_input = QSpinBox()
        self.qty_input.setMinimum(1)
        self.qty_input.setValue(1)
        select_layout.addWidget(self.qty_input)

        select_layout.addWidget(QLabel("Unit Price:"))
        self.unit_price_input = QDoubleSpinBox()
        self.unit_price_input.setMinimum(0)
        self.unit_price_input.setValue(0)
        select_layout.addWidget(self.unit_price_input)

        add_btn = QPushButton("Add to Cart")
        add_btn.clicked.connect(self._add_item_to_cart)
        select_layout.addWidget(add_btn)
        layout.addLayout(select_layout)

        # Cart table
        layout.addWidget(QLabel("Cart Items (FEFO Allocation):"))
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels(
            ["Product", "Qty", "Unit Price", "Subtotal", "Batches (FEFO)", "Remove"]
        )
        layout.addWidget(self.cart_table)

        # Total section
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        total_layout.addWidget(QLabel("Cart Total:"))
        self.total_label = QLabel("₦0.00")
        self.total_label.setFont(QFont("Arial", 12, QFont.Bold))
        total_layout.addWidget(self.total_label)
        layout.addLayout(total_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        clear_btn = QPushButton("Clear Cart")
        clear_btn.clicked.connect(self._clear_cart)
        btn_layout.addWidget(clear_btn)

        checkout_btn = QPushButton("Checkout")
        checkout_btn.clicked.connect(self._checkout)
        btn_layout.addWidget(checkout_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _load_products(self):
        """Load products into combo box."""
        try:
            products = self.product_service.list_products()
            for product in products:
                self.product_combo.addItem(
                    f"{product['name']} ({product['sku']})",
                    product["id"],
                )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load products: {str(e)}")

    def _add_item_to_cart(self):
        """Add product to cart using FEFO allocation."""
        try:
            product_id = self.product_combo.currentData()
            qty = self.qty_input.value()
            unit_price = self.unit_price_input.value()

            if qty <= 0:
                QMessageBox.warning(self, "Validation", "Quantity must be > 0")
                return

            if unit_price < 0:
                QMessageBox.warning(self, "Validation", "Unit price cannot be negative")
                return

            # Get primary store
            store = self.store_service.get_primary_store()
            if not store:
                QMessageBox.warning(self, "Error", "No primary store configured")
                return

            # Use FEFO allocation
            allocated_batches = self.inv_service.allocate_stock_for_sale(
                product_id=product_id,
                store_id=store["id"],
                quantity=qty,
            )

            if not allocated_batches:
                QMessageBox.warning(
                    self,
                    "Insufficient Stock",
                    f"Not enough stock for product ID {product_id}",
                )
                return

            # Add to cart
            product = self.product_service.get_product(product_id)
            cart_item = {
                "product_id": product_id,
                "product_name": product["name"],
                "quantity": qty,
                "unit_price": unit_price,
                "batches": allocated_batches,  # [{batch_id, quantity}, ...]
            }
            self.cart_items.append(cart_item)

            # Refresh cart display
            self._refresh_cart_table()
            QMessageBox.information(self, "Success", f"Added {qty} units to cart")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add item: {str(e)}")

    def _refresh_cart_table(self):
        """Refresh cart table display."""
        self.cart_table.setRowCount(len(self.cart_items))
        total = 0

        for i, item in enumerate(self.cart_items):
            subtotal = item["quantity"] * item["unit_price"]
            total += subtotal

            # Product name
            self.cart_table.setItem(i, 0, QTableWidgetItem(item["product_name"]))

            # Quantity
            self.cart_table.setItem(i, 1, QTableWidgetItem(str(item["quantity"])))

            # Unit price
            self.cart_table.setItem(i, 2, QTableWidgetItem(f"₦{item['unit_price']:.2f}"))

            # Subtotal
            self.cart_table.setItem(i, 3, QTableWidgetItem(f"₦{subtotal:.2f}"))

            # Batches (FEFO allocation details)
            batch_info = ", ".join(
                [f"B{b['batch_id']}:{b['quantity']}" for b in item["batches"]]
            )
            self.cart_table.setItem(i, 4, QTableWidgetItem(batch_info))

            # Remove button
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, idx=i: self._remove_item(idx))
            self.cart_table.setCellWidget(i, 5, remove_btn)

        # Update total
        self.total_label.setText(f"₦{total:.2f}")

    def _remove_item(self, index):
        """Remove item from cart."""
        if 0 <= index < len(self.cart_items):
            self.cart_items.pop(index)
            self._refresh_cart_table()

    def _clear_cart(self):
        """Clear all items from cart."""
        self.cart_items.clear()
        self._refresh_cart_table()

    def _checkout(self):
        """Proceed to checkout (validate and store cart data)."""
        if not self.cart_items:
            QMessageBox.warning(self, "Empty Cart", "Add items before checkout")
            return

        # Store checkout data and accept
        self.checkout_data = self.cart_items
        self.accept()


# --- Login Dialog -----------------------------------------------
class LoginDialog(QDialog):
    """User login dialog."""

    def __init__(self, auth_service: AuthenticationService):
        super().__init__()
        self.auth_service = auth_service
        self.user_session = None
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup login UI."""
        self.setWindowTitle("PharmaPOS - Login")
        self.setGeometry(100, 100, 400, 350)

        layout = QVBoxLayout()

        # Title
        title = QLabel("PharmaPOS NG - Pharmacy Management System")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        layout.addSpacing(20)

        # Username (ComboBox)
        layout.addWidget(QLabel("Username:"))
        self.username_combo = QComboBox()
        self.load_usernames()
        layout.addWidget(self.username_combo)

        # Password
        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        layout.addSpacing(20)

        # Login button
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.login)
        layout.addWidget(login_btn)

        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red;")
        layout.addWidget(self.error_label)

        self.setLayout(layout)

    def load_usernames(self) -> None:
        """Load available usernames from database."""
        try:
            from desktop_app.database import users
            session = get_session()
            
            # Query all active users
            result = session.query(users.c.username).filter(
                users.c.is_active == True
            ).order_by(users.c.username).all()
            
            if result:
                usernames = [row[0] for row in result]
                self.username_combo.addItems(usernames)
            else:
                # Fallback if no users in database
                self.username_combo.addItems(["admin", "manager1", "cashier1"])
            session.close()
        except Exception:
            # Fallback to demo users
            self.username_combo.addItems(["admin", "manager1", "cashier1"])

    def login(self) -> None:
        """Attempt login."""
        username = self.username_combo.currentText()
        password = self.password_input.text()

        if not username or not password:
            self.error_label.setText("Please select username and enter password")
            return

        user_session = self.auth_service.login(username, password)
        if user_session:
            self.user_session = user_session
            self.accept()
        else:
            self.error_label.setText("Invalid username or password")


# --- Main Application Window -----------------------------------------------
class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, auth_service: AuthenticationService, user_session: UserSession):
        super().__init__()
        self.auth_service = auth_service
        self.user_session = user_session
        self.db_path = None

        # Initialize services
        session = get_session(self.db_path)
        self.store_service = StoreService(session)
        self.product_service = ProductService(session)
        self.inventory_service = InventoryService(session)

        self.setup_ui()
        self.load_dashboard_data()

    def _create_separator(self) -> QWidget:
        """Create a simple line separator."""
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #cccccc;")
        return line

    def setup_ui(self) -> None:
        """Setup main UI."""
        self.setWindowTitle(f"PharmaPOS - {self.user_session.username} ({self.user_session.role})")
        self.setGeometry(100, 100, 1200, 700)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()

        # Top bar with user info and logout
        top_bar = QHBoxLayout()
        user_label = QLabel(f"User: {self.user_session.username} | Role: {self.user_session.role}")
        top_bar.addWidget(user_label)
        top_bar.addStretch()
        settings_btn = QPushButton("⚙ Printer Settings")
        settings_btn.clicked.connect(self.open_printer_settings)
        top_bar.addWidget(settings_btn)
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.logout)
        top_bar.addWidget(logout_btn)
        layout.addLayout(top_bar)

        # Tab widget
        self.tabs = QTabWidget()

        # Dashboard tab
        self.tabs.addTab(self.create_dashboard_tab(), "Dashboard")

        # Sales tab
        self.tabs.addTab(self.create_sales_tab(), "Sales")

        # Inventory tab
        self.tabs.addTab(self.create_inventory_tab(), "Inventory")

        # Products tab
        self.tabs.addTab(self.create_products_tab(), "Products")

        # Reports tab
        self.tabs.addTab(self.create_reports_tab(), "Reports")

        layout.addWidget(self.tabs)
        central.setLayout(layout)

    def create_dashboard_tab(self) -> QWidget:
        """Create dashboard tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Summary cards
        layout.addWidget(QLabel("Dashboard Summary"))

        self.dashboard_table = QTableWidget()
        self.dashboard_table.setColumnCount(2)
        self.dashboard_table.setHorizontalHeaderLabels(["Metric", "Value"])
        layout.addWidget(self.dashboard_table)

        # Alerts
        layout.addWidget(QLabel("Alerts"))
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(2)
        self.alerts_table.setHorizontalHeaderLabels(["Alert Type", "Message"])
        layout.addWidget(self.alerts_table)

        widget.setLayout(layout)
        return widget

    def create_sales_tab(self) -> QWidget:
        """Create professional POS sales screen with product grid and cart."""
        widget = QWidget()
        main_layout = QHBoxLayout()

        # ===== LEFT SIDE: Product Catalog =====
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Products"))

        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Search by name, article, barcode, code and description")
        self.product_search.textChanged.connect(self.on_product_search)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.product_search)
        left_layout.addLayout(search_layout)

        # Product grid (scrollable)
        product_scroll = QScrollArea()
        product_scroll.setWidgetResizable(True)
        self.product_grid_widget = QWidget()
        self.product_grid_layout = QVBoxLayout(self.product_grid_widget)
        self.product_grid_layout.setSpacing(10)

        # Container for product cards
        self.products_container = QWidget()
        self.products_container_layout = QVBoxLayout(self.products_container)
            
        # Create product cards grid (4 columns)
        self.products_cards_layout = QGridLayout()
        self.products_cards_layout.setSpacing(10)
        self.products_container_layout.addLayout(self.products_cards_layout)
        self.products_container_layout.addStretch()

        product_scroll.setWidget(self.products_container)
        left_layout.addWidget(product_scroll)

        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setMaximumWidth(500)

        main_layout.addWidget(left_widget)

        # ===== RIGHT SIDE: Sales Cart & Summary =====
        right_layout = QVBoxLayout()

        # Customer info
        customer_layout = QHBoxLayout()
        customer_layout.addWidget(QLabel("Customer:"))
        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("Default customer")
        customer_layout.addWidget(self.customer_input)
        right_layout.addLayout(customer_layout)

        # Cart table
        self.sales_cart_table = QTableWidget()
        self.sales_cart_table.setColumnCount(6)
        self.sales_cart_table.setHorizontalHeaderLabels(
            ["Product Name", "Price (₦)", "Quantity", "Discount (%)", "Total (₦)", "Action"]
        )
        self.sales_cart_table.setColumnWidth(0, 250)
        self.sales_cart_table.setColumnWidth(1, 100)
        self.sales_cart_table.setColumnWidth(2, 80)
        self.sales_cart_table.setColumnWidth(3, 100)
        self.sales_cart_table.setColumnWidth(4, 120)
        self.sales_cart_table.setColumnWidth(5, 60)
        self.sales_cart_table.setRowHeight(0, 30)
        right_layout.addWidget(self.sales_cart_table)

        # Summary section
        summary_layout = QVBoxLayout()
        summary_layout.setSpacing(8)
        
        # Subtotal
        subtotal_layout = QHBoxLayout()
        subtotal_lbl = QLabel("Subtotal:")
        subtotal_lbl.setStyleSheet("font-size: 12px; font-weight: bold;")
        subtotal_layout.addWidget(subtotal_lbl)
        subtotal_layout.addStretch()
        self.subtotal_label = QLabel("0.00 N")
        self.subtotal_label.setAlignment(Qt.AlignRight)
        self.subtotal_label.setStyleSheet("font-size: 12px;")
        subtotal_layout.addWidget(self.subtotal_label)
        summary_layout.addLayout(subtotal_layout)

        # Discount
        discount_layout = QHBoxLayout()
        discount_lbl = QLabel("Discount:")
        discount_lbl.setStyleSheet("font-size: 12px; font-weight: bold;")
        discount_layout.addWidget(discount_lbl)
        discount_layout.addStretch()
        self.discount_label = QLabel("(0.00%) 0.00 N")
        self.discount_label.setAlignment(Qt.AlignRight)
        self.discount_label.setStyleSheet("font-size: 12px;")
        discount_layout.addWidget(self.discount_label)
        summary_layout.addLayout(discount_layout)

        # Tax
        tax_layout = QHBoxLayout()
        tax_lbl = QLabel("Tax:")
        tax_lbl.setStyleSheet("font-size: 12px; font-weight: bold;")
        tax_layout.addWidget(tax_lbl)
        tax_layout.addStretch()
        self.tax_label = QLabel("0.00 N")
        self.tax_label.setAlignment(Qt.AlignRight)
        self.tax_label.setStyleSheet("font-size: 12px;")
        tax_layout.addWidget(self.tax_label)
        summary_layout.addLayout(tax_layout)

        right_layout.addLayout(summary_layout)
        right_layout.addStretch()

        # Payment & Sale button
        payment_layout = QHBoxLayout()
        payment_layout.addWidget(QLabel("Payment Method:"))
        self.sales_payment_method = QComboBox()
        self.sales_payment_method.addItems(["Cash", "Card", "Transfer"])
        payment_layout.addWidget(self.sales_payment_method)
        
        payment_layout.addWidget(QLabel("Amount Paid:"))
        self.sales_amount_paid = QDoubleSpinBox()
        self.sales_amount_paid.setMinimum(0)
        self.sales_amount_paid.setMaximum(999999.99)
        self.sales_amount_paid.setDecimals(2)
        payment_layout.addWidget(self.sales_amount_paid)
        right_layout.addLayout(payment_layout)

        # Sale button (green, large)
        self.complete_sale_btn = QPushButton("COMPLETE SALE")
        self.complete_sale_btn.setMinimumHeight(70)
        self.complete_sale_btn.setMinimumWidth(200)
        self.complete_sale_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                font-size: 18px;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        self.complete_sale_btn.clicked.connect(self.complete_sale)
        right_layout.addWidget(self.complete_sale_btn)

        # Printer quick actions: Test and Reprint
        printer_actions_layout = QHBoxLayout()
        self.printer_test_btn = QPushButton("Printer Test")
        self.printer_test_btn.setToolTip("Send a small test print to configured printer (or save to file fallback)")
        self.printer_test_btn.clicked.connect(self.printer_test)
        printer_actions_layout.addWidget(self.printer_test_btn)

        self.reprint_last_btn = QPushButton("Reprint Last Receipt")
        self.reprint_last_btn.setToolTip("Reprint the most recent sale receipt")
        self.reprint_last_btn.clicked.connect(self.reprint_last_receipt)
        printer_actions_layout.addWidget(self.reprint_last_btn)

        right_layout.addLayout(printer_actions_layout)

        # Total amount display
        self.total_amount_label = QLabel("0.00 N")
        self.total_amount_label.setAlignment(Qt.AlignRight)
        self.total_amount_label.setStyleSheet("font-weight: bold; font-size: 22px; color: #28a745; padding: 10px;")
        self.total_amount_label.setMinimumHeight(40)
        right_layout.addWidget(self.total_amount_label)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        main_layout.addWidget(right_widget, 1)
        main_layout.setStretchFactor(left_widget, 0)
        main_layout.setStretchFactor(right_widget, 1)

        widget.setLayout(main_layout)
        
        # Load products on startup
        self.load_sales_products()
        
        return widget

    def create_inventory_tab(self) -> QWidget:
        """Create inventory management tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Inventory Management"))

        # Stock receipt section
        layout.addWidget(QLabel("Receive Stock"))
        receipt_layout = QHBoxLayout()
        
        receipt_layout.addWidget(QLabel("Product ID:"))
        self.product_id_input = QLineEdit()
        receipt_layout.addWidget(self.product_id_input)

        receipt_layout.addWidget(QLabel("Quantity:"))
        self.stock_qty_input = QSpinBox()
        receipt_layout.addWidget(self.stock_qty_input)

        receipt_btn = QPushButton("Receive Stock")
        receipt_btn.clicked.connect(self.receive_stock)
        receipt_layout.addWidget(receipt_btn)
        layout.addLayout(receipt_layout)

        # Bulk expiry controls
        expiry_layout = QHBoxLayout()
        expiry_layout.addWidget(QLabel("Store ID:"))
        self.expiry_store_input = QLineEdit()
        self.expiry_store_input.setPlaceholderText("Leave empty for primary store")
        expiry_layout.addWidget(self.expiry_store_input)

        expiry_layout.addWidget(QLabel("Expire within (days):"))
        self.expiry_days_input = QSpinBox()
        self.expiry_days_input.setRange(1, 3650)
        self.expiry_days_input.setValue(30)
        expiry_layout.addWidget(self.expiry_days_input)

        expiry_btn = QPushButton("Expire Batches Within Days")
        expiry_btn.clicked.connect(self.expire_batches_action)
        expiry_layout.addWidget(expiry_btn)
        layout.addLayout(expiry_layout)

        # Stock view
        layout.addWidget(QLabel("Current Stock"))
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(5)
        self.inventory_table.setHorizontalHeaderLabels(
            ["Batch ID", "Product ID", "Batch #", "Expiry", "Qty"]
        )
        layout.addWidget(self.inventory_table)

        widget.setLayout(layout)
        return widget

    def create_products_tab(self) -> QWidget:
        """Create products management tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Product Catalog"))

        # Control buttons
        button_layout = QHBoxLayout()
        
        create_btn = QPushButton("+ New Product")
        create_btn.clicked.connect(self.show_create_product_dialog)
        button_layout.addWidget(create_btn)

        import_btn = QPushButton("Import Products")
        import_btn.clicked.connect(self.show_import_dialog)
        button_layout.addWidget(import_btn)

        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_products_csv)
        button_layout.addWidget(export_btn)

        template_btn = QPushButton("Export to JSON")
        template_btn.clicked.connect(self.export_products_json)
        button_layout.addWidget(template_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_products_table)
        button_layout.addWidget(refresh_btn)

        layout.addLayout(button_layout)

        # Products table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(13)
        self.products_table.setHorizontalHeaderLabels(
            ["ID", "Name", "SKU", "Cost Price", "Retail Price", "Bulk Price", "Bulk Qty", 
             "Wholesale Price", "Wholesale Qty", "Min Stock", "Max Stock", "Reorder Level", "Status"]
        )
        self.products_table.setColumnWidth(1, 120)
        self.products_table.setColumnWidth(2, 80)
        layout.addWidget(self.products_table)

        # Load products on startup
        self.load_products_table()

        widget.setLayout(layout)
        return widget

    def load_products_table(self) -> None:
        """Load and display all products in the table."""
        try:
            products = self.product_service.get_all_products(active_only=False)
            self.products_table.setRowCount(len(products))

            for i, product in enumerate(products):
                self.products_table.setItem(i, 0, QTableWidgetItem(str(product["id"])))
                self.products_table.setItem(i, 1, QTableWidgetItem(product["name"]))
                self.products_table.setItem(i, 2, QTableWidgetItem(product["sku"]))
                self.products_table.setItem(i, 3, QTableWidgetItem(f"₦{product.get('cost_price', 0)}"))
                self.products_table.setItem(i, 4, QTableWidgetItem(f"₦{product.get('retail_price', 0)}"))
                bulk_price = f"₦{product.get('bulk_price', 0)}" if product.get('bulk_price') else "-"
                self.products_table.setItem(i, 5, QTableWidgetItem(bulk_price))
                bulk_qty = str(product.get('bulk_quantity', "-")) if product.get('bulk_quantity') else "-"
                self.products_table.setItem(i, 6, QTableWidgetItem(bulk_qty))
                wholesale_price = f"₦{product.get('wholesale_price', 0)}" if product.get('wholesale_price') else "-"
                self.products_table.setItem(i, 7, QTableWidgetItem(wholesale_price))
                wholesale_qty = str(product.get('wholesale_quantity', "-")) if product.get('wholesale_quantity') else "-"
                self.products_table.setItem(i, 8, QTableWidgetItem(wholesale_qty))
                self.products_table.setItem(i, 9, QTableWidgetItem(str(product.get('min_stock', 0))))
                self.products_table.setItem(i, 10, QTableWidgetItem(str(product.get('max_stock', 0))))
                reorder = str(product.get('reorder_level', "-")) if product.get('reorder_level') else "-"
                self.products_table.setItem(i, 11, QTableWidgetItem(reorder))
                status = "Active" if product.get("is_active") else "Inactive"
                self.products_table.setItem(i, 12, QTableWidgetItem(status))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products: {str(e)}")

    def show_create_product_dialog(self) -> None:
        """Show dialog to create a new product with pricing tiers and stock alerts."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Product")
        dialog.setGeometry(200, 200, 600, 800)

        main_layout = QVBoxLayout()

        # Scrollable area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)

        # ===== SECTION 1: Basic Product Information =====
        layout.addWidget(QLabel("<b>Product Information</b>"))
        layout.addWidget(self._create_separator())

        # Name
        layout.addWidget(QLabel("Product Name:"))
        name_input = QLineEdit()
        layout.addWidget(name_input)

        # Generic Name
        layout.addWidget(QLabel("Generic Name (Optional):"))
        generic_input = QLineEdit()
        layout.addWidget(generic_input)

        # SKU
        layout.addWidget(QLabel("SKU:"))
        sku_input = QLineEdit()
        layout.addWidget(sku_input)

        # Barcode
        layout.addWidget(QLabel("Barcode (Optional):"))
        barcode_input = QLineEdit()
        layout.addWidget(barcode_input)

        # NAFDAC Number
        layout.addWidget(QLabel("NAFDAC Number:"))
        nafdac_input = QLineEdit()
        layout.addWidget(nafdac_input)

        layout.addSpacing(10)

        # ===== SECTION 2: Cost & Basic Pricing =====
        layout.addWidget(QLabel("<b>Cost & Basic Pricing</b>"))
        layout.addWidget(self._create_separator())

        # Cost Price
        layout.addWidget(QLabel("Cost Price (₦):"))
        cost_input = QDoubleSpinBox()
        cost_input.setMinimum(0)
        cost_input.setMaximum(999999.99)
        cost_input.setDecimals(2)
        layout.addWidget(cost_input)

        # Selling Price
        layout.addWidget(QLabel("Selling Price (₦):"))
        selling_input = QDoubleSpinBox()
        selling_input.setMinimum(0)
        selling_input.setMaximum(999999.99)
        selling_input.setDecimals(2)
        layout.addWidget(selling_input)

        layout.addSpacing(10)

        # ===== SECTION 3: Pricing Tiers =====
        layout.addWidget(QLabel("<b>Pricing Tiers</b>"))
        layout.addWidget(self._create_separator())

        # Retail Price
        layout.addWidget(QLabel("Retail Price (₦):"))
        retail_input = QDoubleSpinBox()
        retail_input.setMinimum(0)
        retail_input.setMaximum(999999.99)
        retail_input.setDecimals(2)
        layout.addWidget(retail_input)

        # Bulk Price Section
        layout.addWidget(QLabel("Bulk Price (₦) (Optional):"))
        bulk_price_input = QDoubleSpinBox()
        bulk_price_input.setMinimum(0)
        bulk_price_input.setMaximum(999999.99)
        bulk_price_input.setDecimals(2)
        layout.addWidget(bulk_price_input)

        layout.addWidget(QLabel("Minimum Quantity for Bulk Price:"))
        bulk_qty_input = QSpinBox()
        bulk_qty_input.setMinimum(1)
        bulk_qty_input.setMaximum(100000)
        bulk_qty_input.setValue(10)
        layout.addWidget(bulk_qty_input)

        # Wholesale Price Section
        layout.addWidget(QLabel("Wholesale Price (₦) (Optional):"))
        wholesale_price_input = QDoubleSpinBox()
        wholesale_price_input.setMinimum(0)
        wholesale_price_input.setMaximum(999999.99)
        wholesale_price_input.setDecimals(2)
        layout.addWidget(wholesale_price_input)

        layout.addWidget(QLabel("Minimum Quantity for Wholesale Price:"))
        wholesale_qty_input = QSpinBox()
        wholesale_qty_input.setMinimum(1)
        wholesale_qty_input.setMaximum(100000)
        wholesale_qty_input.setValue(50)
        layout.addWidget(wholesale_qty_input)

        layout.addSpacing(10)

        # ===== SECTION 4: Stock Alerts =====
        layout.addWidget(QLabel("<b>Stock Alerts</b>"))
        layout.addWidget(self._create_separator())

        layout.addWidget(QLabel("Minimum Stock Alert:"))
        min_stock_input = QSpinBox()
        min_stock_input.setMinimum(0)
        min_stock_input.setMaximum(100000)
        min_stock_input.setValue(10)
        layout.addWidget(min_stock_input)

        layout.addWidget(QLabel("Maximum Stock Alert:"))
        max_stock_input = QSpinBox()
        max_stock_input.setMinimum(1)
        max_stock_input.setMaximum(1000000)
        max_stock_input.setValue(500)
        layout.addWidget(max_stock_input)

        layout.addWidget(QLabel("Reorder Level (Optional):"))
        reorder_input = QSpinBox()
        reorder_input.setMinimum(0)
        reorder_input.setMaximum(100000)
        layout.addWidget(reorder_input)

        layout.addSpacing(10)

        # ===== SECTION 5: Description =====
        layout.addWidget(QLabel("<b>Description</b>"))
        layout.addWidget(self._create_separator())

        layout.addWidget(QLabel("Description (Optional):"))
        description_input = QTextEdit()
        description_input.setMaximumHeight(80)
        layout.addWidget(description_input)

        layout.addStretch()
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        # Buttons
        button_layout = QHBoxLayout()

        def create_product():
            try:
                if not name_input.text().strip():
                    QMessageBox.warning(dialog, "Validation", "Product name is required")
                    return
                if not sku_input.text().strip():
                    QMessageBox.warning(dialog, "Validation", "SKU is required")
                    return
                if not nafdac_input.text().strip():
                    QMessageBox.warning(dialog, "Validation", "NAFDAC number is required")
                    return
                if min_stock_input.value() > max_stock_input.value():
                    QMessageBox.warning(dialog, "Validation", "Min stock cannot exceed max stock")
                    return

                # Use retail price as fallback if not set
                retail_price = Decimal(str(retail_input.value())) if retail_input.value() > 0 else Decimal(str(selling_input.value()))

                product = self.product_service.create_product(
                    name=name_input.text().strip(),
                    sku=sku_input.text().strip(),
                    cost_price=Decimal(str(cost_input.value())),
                    selling_price=Decimal(str(selling_input.value())),
                    nafdac_number=nafdac_input.text().strip(),
                    generic_name=generic_input.text().strip(),
                    barcode=barcode_input.text().strip(),
                    description=description_input.toPlainText().strip(),
                    retail_price=retail_price,
                    bulk_price=Decimal(str(bulk_price_input.value())) if bulk_price_input.value() > 0 else None,
                    bulk_quantity=bulk_qty_input.value() if bulk_price_input.value() > 0 else None,
                    wholesale_price=Decimal(str(wholesale_price_input.value())) if wholesale_price_input.value() > 0 else None,
                    wholesale_quantity=wholesale_qty_input.value() if wholesale_price_input.value() > 0 else None,
                    min_stock=min_stock_input.value(),
                    max_stock=max_stock_input.value(),
                    reorder_level=reorder_input.value() if reorder_input.value() > 0 else None,
                )
                QMessageBox.information(dialog, "Success", f"Product created: {product['name']}\n\nRetail: ₦{product['retail_price']}\nBulk: ₦{product['bulk_price']}\nWholesale: ₦{product['wholesale_price']}\nStock Alerts: {product['min_stock']}-{product['max_stock']}")
                self.load_products_table()
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to create product: {str(e)}")

        create_btn = QPushButton("Create Product")
        create_btn.clicked.connect(create_product)
        button_layout.addWidget(create_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        main_layout.addLayout(button_layout)
        dialog.setLayout(main_layout)
        dialog.exec_()

    def show_import_dialog(self) -> None:
        """Show dialog to import products."""
        file_filter = "CSV Files (*.csv);;JSON Files (*.json);;All Files (*.*)"
        filepath, selected_filter = QFileDialog.getOpenFileName(
            self, "Import Products", "", file_filter
        )

        if not filepath:
            return

        try:
            exporter = ProductImportExporter(self.db_path)
            
            # Validate file first
            file_format = "csv" if filepath.endswith(".csv") else "json"
            is_valid, errors = exporter.validate_file(filepath, file_format)
            
            if not is_valid:
                error_msg = "Validation errors:\n\n" + "\n".join(errors[:10])
                if len(errors) > 10:
                    error_msg += f"\n... and {len(errors) - 10} more errors"
                QMessageBox.warning(self, "Validation Failed", error_msg)
                return

            # Ask to update existing
            reply = QMessageBox.question(
                self,
                "Update Existing?",
                "Update products if SKU already exists?",
                QMessageBox.Yes | QMessageBox.No,
            )
            update_existing = reply == QMessageBox.Yes

            # Import
            if file_format == "csv":
                imported_count, errors = exporter.import_from_csv(filepath, update_existing)
            else:
                imported_count, errors = exporter.import_from_json(filepath, update_existing)

            # Show results
            msg = f"Imported: {imported_count} products\n"
            if errors:
                msg += f"\nErrors: {len(errors)}\n"
                msg += "\n".join(errors[:5])
                if len(errors) > 5:
                    msg += f"\n... and {len(errors) - 5} more errors"

            QMessageBox.information(self, "Import Complete", msg)
            self.load_products_table()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {str(e)}")

    def export_products_csv(self) -> None:
        """Export products to CSV file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Products", "products.csv", "CSV Files (*.csv)"
        )

        if not filepath:
            return

        try:
            exporter = ProductImportExporter(self.db_path)
            success, message = exporter.export_to_csv(filepath)
            if success:
                QMessageBox.information(self, "Export Success", message)
            else:
                QMessageBox.warning(self, "Export Failed", message)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")

    def export_products_json(self) -> None:
        """Export products to JSON file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Products", "products.json", "JSON Files (*.json)"
        )

        if not filepath:
            return

        try:
            exporter = ProductImportExporter(self.db_path)
            success, message = exporter.export_to_json(filepath)
            if success:
                QMessageBox.information(self, "Export Success", message)
            else:
                QMessageBox.warning(self, "Export Failed", message)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")

    def create_reports_tab(self) -> QWidget:
        """Create reports tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Reports & Analytics"))

        # Report selector
        report_layout = QHBoxLayout()
        report_layout.addWidget(QLabel("Select Report:"))
        self.report_type = QComboBox()
        self.report_type.addItems([
            "Daily Sales",
            "Top Products",
            "Stock Valuation",
            "Expiring Items"
        ])
        report_layout.addWidget(self.report_type)

        report_layout.addWidget(QLabel("Date:"))
        self.report_date = QDateEdit()
        self.report_date.setDate(QDate.currentDate())
        report_layout.addWidget(self.report_date)

        generate_btn = QPushButton("Generate Report")
        generate_btn.clicked.connect(self.generate_report)
        report_layout.addWidget(generate_btn)
        layout.addLayout(report_layout)

        self.report_table = QTableWidget()
        layout.addWidget(self.report_table)

        widget.setLayout(layout)
        return widget

    def load_dashboard_data(self) -> None:
        """Load and display dashboard data."""
        try:
            # Get store info
            store = self.store_service.get_primary_store()
            if not store:
                return

            # Get inventory alerts
            alerts_service = InventoryAlerts(self.db_path)
            alerts = alerts_service.generate_alerts(store["id"])

            # Update dashboard table
            self.dashboard_table.setRowCount(len(alerts["alerts"]))
            for i, alert in enumerate(alerts["alerts"]):
                self.dashboard_table.setItem(i, 0, QTableWidgetItem(alert["type"].upper()))
                self.dashboard_table.setItem(i, 1, QTableWidgetItem(alert["message"]))

            # Update alerts table
            self.alerts_table.setRowCount(len(alerts["alerts"]))
            for i, alert in enumerate(alerts["alerts"]):
                self.alerts_table.setItem(i, 0, QTableWidgetItem(alert["type"]))
                self.alerts_table.setItem(i, 1, QTableWidgetItem(alert["message"]))

            alerts_service.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load dashboard: {str(e)}")

    def load_sales_products(self) -> None:
        """Load all products into the sales product grid."""
        try:
            products = self.product_service.get_all_products(active_only=True)
            
            # Clear existing cards
            while self.products_cards_layout.count():
                item = self.products_cards_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Create product cards (max 4 columns)
            for i, product in enumerate(products):
                card = self.create_product_card(product)
                row = i // 4
                col = i % 4
                self.products_cards_layout.addWidget(card, row, col)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products: {str(e)}")

    def create_product_card(self, product: dict) -> QWidget:
        """Create a clickable product card for the sales grid."""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
            QWidget:hover {
                background-color: #e8e8e8;
            }
        """)
        card.setCursor(Qt.PointingHandCursor)
        layout = QVBoxLayout(card)
        layout.setSpacing(5)

        # Product image placeholder
        image_label = QLabel()
        image_label.setMinimumHeight(100)
        image_label.setStyleSheet("background-color: #ccc; border-radius: 3px;")
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setText("No Image")
        layout.addWidget(image_label)

        # Product name
        name_label = QLabel(product['name'])
        name_label.setWordWrap(True)
        name_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        layout.addWidget(name_label)

        # Stock info
        stock_label = QLabel(f"Stock: {product.get('quantity', 0)} units")
        stock_label.setStyleSheet("font-size: 9px; color: #666;")
        layout.addWidget(stock_label)

        # Price
        price_label = QLabel(f"{product.get('retail_price', product.get('selling_price', 0))} N")
        price_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #28a745;")
        layout.addWidget(price_label)

        # Store product data on card
        card.product_id = product['id']
        card.product_name = product['name']
        card.product_price = float(product.get('retail_price', product.get('selling_price', 0)))

        # Make card clickable
        def on_card_clicked():
            self.add_product_to_sales_cart(product)
        
        card.mousePressEvent = lambda event: on_card_clicked()

        return card

    def add_product_to_sales_cart(self, product: dict) -> None:
        """Add product to sales cart."""
        try:
            # Check if product already in cart
            for row in range(self.sales_cart_table.rowCount()):
                name_item = self.sales_cart_table.item(row, 0)
                if name_item and name_item.text() == product['name']:
                    # Increment quantity
                    qty_item = self.sales_cart_table.item(row, 2)
                    current_qty = int(qty_item.text())
                    qty_item.setText(str(current_qty + 1))
                    self.update_sales_summary()
                    return

            # Add new row to cart
            row = self.sales_cart_table.rowCount()
            self.sales_cart_table.insertRow(row)

            price = float(product.get('retail_price', product.get('selling_price', 0)))

            # Name
            self.sales_cart_table.setItem(row, 0, QTableWidgetItem(product['name']))

            # Price
            self.sales_cart_table.setItem(row, 1, QTableWidgetItem(f"{price:.2f}"))

            # Quantity (default 1)
            qty_item = QTableWidgetItem("1")
            qty_item.setTextAlignment(Qt.AlignCenter)
            self.sales_cart_table.setItem(row, 2, qty_item)

            # Discount (default 0%)
            discount_item = QTableWidgetItem("0%")
            discount_item.setTextAlignment(Qt.AlignCenter)
            self.sales_cart_table.setItem(row, 3, discount_item)

            # Total (price * 1)
            self.sales_cart_table.setItem(row, 4, QTableWidgetItem(f"{price:.2f}"))

            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.setMaximumWidth(60)
            delete_btn.setMinimumHeight(30)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 3px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            delete_btn.clicked.connect(lambda: self.remove_from_cart(row))
            self.sales_cart_table.setCellWidget(row, 5, delete_btn)

            # Store product ID
            self.sales_cart_table.item(row, 0).product_id = product['id']

            self.update_sales_summary()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add product: {str(e)}")

    def remove_from_cart(self, row: int) -> None:
        """Remove item from sales cart."""
        self.sales_cart_table.removeRow(row)
        self.update_sales_summary()

    def update_sales_summary(self) -> None:
        """Update cart summary (subtotal, tax, total)."""
        subtotal = 0.0
        
        for row in range(self.sales_cart_table.rowCount()):
            qty_text = self.sales_cart_table.item(row, 2).text()
            price_text = self.sales_cart_table.item(row, 1).text()
            qty = int(qty_text) if qty_text else 0
            price = float(price_text) if price_text else 0.0
            subtotal += qty * price

        # Calculate tax (assuming 7.5% VAT)
        tax = subtotal * 0.075
        total = subtotal + tax

        # Update labels
        self.subtotal_label.setText(f"{subtotal:.2f} N")
        self.discount_label.setText(f"(0.00%) 0.00 N")
        self.tax_label.setText(f"{tax:.2f} N")
        self.total_amount_label.setText(f"{total:.2f} N")

        # Update amount paid default
        self.sales_amount_paid.setValue(total)

    def on_product_search(self) -> None:
        """Filter products based on search input."""
        search_text = self.product_search.text().lower()
        try:
            if search_text:
                products = self.product_service.get_all_products(active_only=True)
                filtered = [
                    p for p in products 
                    if search_text in p['name'].lower() 
                    or search_text in p.get('sku', '').lower()
                    or search_text in p.get('barcode', '').lower()
                ]
            else:
                filtered = self.product_service.get_all_products(active_only=True)
            
            # Clear and reload
            while self.products_cards_layout.count():
                item = self.products_cards_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            for i, product in enumerate(filtered):
                card = self.create_product_card(product)
                row = i // 4
                col = i % 4
                self.products_cards_layout.addWidget(card, row, col)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Search failed: {str(e)}")

    def add_to_cart(self) -> None:
        """Open sales cart dialog with FEFO allocation."""
        try:
            dialog = SalesCartDialog(self.session, self)
            if dialog.exec_() == QDialog.Accepted:
                # Store cart data for later checkout
                self.current_cart = dialog.checkout_data
                
                # Display cart summary
                total_items = sum(item["quantity"] for item in self.current_cart)
                total_amount = sum(
                    item["quantity"] * item["unit_price"] 
                    for item in self.current_cart
                )
                
                self.sales_status.setText(
                    f"Cart: {total_items} items | Total: ₦{total_amount:.2f}"
                )
                QMessageBox.information(
                    self, 
                    "Cart Ready", 
                    f"Added {total_items} item(s) to cart\n"
                    f"Total: ₦{total_amount:.2f}\n\n"
                    "Review cart and proceed to payment"
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open cart: {str(e)}")

    def complete_sale(self) -> None:
        """Complete sale transaction with payment."""
        try:
            # Check if cart has items
            if self.sales_cart_table.rowCount() == 0:
                QMessageBox.warning(self, "Empty Cart", "Add items to cart first")
                return

            # Get payment details
            payment_method = self.sales_payment_method.currentText()
            amount_paid = self.sales_amount_paid.value()

            # Extract cart items from table
            cart_items = []
            subtotal = 0.0
            
            for row in range(self.sales_cart_table.rowCount()):
                name_item = self.sales_cart_table.item(row, 0)
                price_item = self.sales_cart_table.item(row, 1)
                qty_item = self.sales_cart_table.item(row, 2)
                
                if name_item and price_item and qty_item:
                    name = name_item.text()
                    price = float(price_item.text()) if price_item.text() else 0.0
                    qty = int(qty_item.text()) if qty_item.text() else 0
                    
                    if qty > 0:
                        product_id = getattr(name_item, 'product_id', None)
                        cart_items.append({
                            "product_id": product_id,
                            "product_name": name,
                            "unit_price": price,
                            "quantity": qty,
                        })
                        subtotal += price * qty

            if not cart_items:
                QMessageBox.warning(self, "Empty Cart", "Add items to cart first")
                return

            # Calculate tax and total
            tax = subtotal * 0.075  # 7.5% VAT
            total_amount = subtotal + tax

            if amount_paid < total_amount:
                QMessageBox.warning(
                    self,
                    "Insufficient Payment",
                    f"Subtotal: ₦{subtotal:.2f}\n"
                    f"Tax (7.5%): ₦{tax:.2f}\n"
                    f"Total: ₦{total_amount:.2f}\n"
                    f"Paid: ₦{amount_paid:.2f}\n"
                    f"Shortfall: ₦{total_amount - amount_paid:.2f}",
                )
                return

            # Allocate batches using FEFO for each product
            sales_service = SalesService(get_session())
            inventory_service = InventoryService(get_session())
            store = self.store_service.get_primary_store()
            user_id = getattr(self.user_session, "user_id", 1)
            
            allocated_items = []
            for cart_item in cart_items:
                # Get available batches for product (FEFO - earliest expiry first)
                batches = inventory_service.get_available_batches(
                    product_id=cart_item["product_id"],
                    store_id=store["id"],
                    quantity_needed=cart_item["quantity"],
                )
                
                if not batches or sum(b["available_quantity"] for b in batches) < cart_item["quantity"]:
                    QMessageBox.warning(
                        self,
                        "Insufficient Stock",
                        f"Not enough stock for {cart_item['product_name']}\n"
                        f"Needed: {cart_item['quantity']}\n"
                        f"Available: {sum(b['available_quantity'] for b in batches)}",
                    )
                    return
                
                # Allocate from batches
                remaining_qty = cart_item["quantity"]
                for batch in batches:
                    if remaining_qty <= 0:
                        break
                    
                    qty_to_take = min(remaining_qty, batch["available_quantity"])
                    allocated_items.append({
                        "batch_id": batch["id"],
                        "quantity": qty_to_take,
                        "unit_price": cart_item["unit_price"],
                    })
                    remaining_qty -= qty_to_take

            # Create sale
            sale_result = sales_service.create_sale(
                user_id=user_id,
                store_id=store["id"],
                items=allocated_items,
                payment_method=payment_method,
                amount_paid=Decimal(str(amount_paid)),
            )

            change = amount_paid - total_amount
            QMessageBox.information(
                self,
                "Sale Completed",
                f"Receipt #: {sale_result['receipt_number']}\n"
                f"Subtotal: ₦{subtotal:.2f}\n"
                f"Tax (7.5%): ₦{tax:.2f}\n"
                f"Total: ₦{total_amount:.2f}\n"
                f"Amount Paid: ₦{amount_paid:.2f}\n"
                f"Change: ₦{change:.2f}",
            )

            # Print receipt to thermal printer
            self.print_thermal_receipt(
                receipt_number=sale_result['receipt_number'],
                items=cart_items,
                subtotal=subtotal,
                tax=tax,
                total=total_amount,
                payment_method=payment_method,
                amount_paid=amount_paid,
                change=change,
            )
            
            # Display confirmation message
            QMessageBox.information(
                self,
                "Sale Completed",
                f"Receipt #: {sale_result['receipt_number']}\n"
                f"Subtotal: ₦{subtotal:.2f}\n"
                f"Tax (7.5%): ₦{tax:.2f}\n"
                f"Total: ₦{total_amount:.2f}\n"
                f"Amount Paid: ₦{amount_paid:.2f}\n"
                f"Change: ₦{change:.2f}",
            )

            # Clear cart and reset UI
            self.sales_cart_table.setRowCount(0)
            self.customer_input.clear()
            self.sales_amount_paid.setValue(0)
            self.sales_payment_method.setCurrentIndex(0)
            self.update_sales_summary()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to complete sale: {str(e)}")

    def print_thermal_receipt(self, receipt_number: str, items: list, subtotal: float, tax: float, total: float,
                              payment_method: str, amount_paid: float, change: float) -> None:
        """Format and send the receipt to a thermal printer (or save to file fallback)."""
        try:
            from desktop_app.thermal_printer import ThermalPrinter, format_receipt

            store = self.store_service.get_primary_store() if hasattr(self, 'store_service') else None

            receipt_text = format_receipt(
                receipt_number=str(receipt_number),
                items=items,
                subtotal=subtotal,
                tax=tax,
                total=total,
                payment_method=payment_method,
                amount_paid=amount_paid,
                change=change,
                store=store,
            )

            # Instantiate printer with no backend to use file fallback by default.
            printer = ThermalPrinter(backend=None)
            result = printer.print_text(receipt_text)

            if result.get('status') == 'printed':
                QMessageBox.information(self, 'Printer', 'Receipt sent to thermal printer.')
            else:
                path = result.get('path')
                QMessageBox.information(self, 'Receipt Saved', f'Receipt saved to: {path}')

        except Exception as e:
            QMessageBox.warning(self, 'Print Error', f'Failed to print receipt: {e}')


    def receive_stock(self) -> None:
        """Open dialog to receive stock with comprehensive pricing and alerts."""
        try:
            # Open receiving dialog
            dialog = StockReceivingDialog(self.session, self)
            if dialog.exec_() == QDialog.Accepted:
                data = dialog.result_data
                if not data:
                    return

                # Use InventoryService to receive stock
                inv_service = InventoryService(self.session)
                user_id = getattr(self.user_session, "user_id", 1)

                batch = inv_service.receive_stock(
                    product_id=data["product_id"],
                    store_id=data["store_id"],
                    batch_number=data["batch_number"],
                    quantity=data["quantity"],
                    expiry_date=data["expiry_date"],
                    cost_price=data["cost_price"],
                    retail_price=data.get("retail_price"),
                    bulk_price=data.get("bulk_price"),
                    bulk_quantity=data.get("bulk_quantity"),
                    wholesale_price=data.get("wholesale_price"),
                    wholesale_quantity=data.get("wholesale_quantity"),
                    min_stock=data.get("min_stock", 0),
                    max_stock=data.get("max_stock", 9999),
                    reorder_level=data.get("reorder_level"),
                )

                QMessageBox.information(
                    self,
                    "Success",
                    f"Stock received successfully!\n\n"
                    f"Batch ID: {batch['id']}\n"
                    f"Quantity: {data['quantity']} units\n"
                    f"Expiry Date: {data['expiry_date']}\n"
                    f"Cost Price: ₦{data['cost_price']}\n"
                    f"Retail Price: ₦{batch.get('retail_price', 'N/A')}\n"
                    f"Stock Alerts: Min={data.get('min_stock', 0)}, Max={data.get('max_stock', 9999)}\n"
                    f"Store: {data['store_id']}",
                )

                # Refresh inventory table
                self.refresh_inventory_table()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to receive stock: {str(e)}")

    def refresh_inventory_table(self) -> None:
        """Refresh inventory table with current stock batches."""
        try:
            inv_service = InventoryService(self.session)
            store = self.store_service.get_primary_store()
            if not store:
                return

            # Get all batches for primary store (ordered by expiry - FEFO)
            batches = inv_service.get_store_inventory(store["id"])
            self.inventory_table.setRowCount(len(batches))

            for i, batch in enumerate(batches):
                self.inventory_table.setItem(i, 0, QTableWidgetItem(str(batch["id"])))
                self.inventory_table.setItem(i, 1, QTableWidgetItem(str(batch["product_id"])))
                self.inventory_table.setItem(i, 2, QTableWidgetItem(batch["batch_number"]))
                self.inventory_table.setItem(i, 3, QTableWidgetItem(str(batch["expiry_date"])))
                self.inventory_table.setItem(i, 4, QTableWidgetItem(str(batch["quantity"])))

            inv_service.session.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh inventory: {str(e)}")


    def printer_test(self) -> None:
        """Send a small test print using the thermal printer helper (file fallback)."""
        try:
            from desktop_app.thermal_printer import ThermalPrinter
            from datetime import datetime

            printer = ThermalPrinter(backend=None)
            test_text = (
                "PRINTER TEST\n"
                "PharmaPOS Thermal Printer Test\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                "------------------------------\n"
                "This is a test print.\n"
            )
            res = printer.print_text(test_text)
            if res.get('status') == 'printed':
                QMessageBox.information(self, 'Printer Test', 'Test printed to device successfully.')
            else:
                path = res.get('path')
                QMessageBox.information(self, 'Printer Test', f'Test saved to file: {path}')
        except Exception as e:
            QMessageBox.warning(self, 'Printer Test', f'Printer test failed: {e}')


    def reprint_last_receipt(self) -> None:
        """Re-generate and print (or save) the most recent sale receipt."""
        try:
            # Local imports to avoid top-level dependencies
            from desktop_app.models import get_session, SalesService
            from desktop_app.database import sales as sales_table, sale_items as sale_items_table, product_batches, products
            from sqlalchemy import select
            from desktop_app.thermal_printer import ThermalPrinter, format_receipt

            session = get_session()
            # Fetch most recent sale
            stmt = select(sales_table).order_by(sales_table.c.created_at.desc())
            row = session.execute(stmt).fetchone()
            if not row:
                QMessageBox.information(self, 'Reprint', 'No sales found to reprint.')
                return

            sale = dict(row._mapping)
            sale_id = sale['id']

            # Get sale items
            sales_service = SalesService(session)
            items = sales_service.get_sale_items(sale_id)

            # Build printable items list with product names
            printable_items = []
            for it in items:
                # Lookup batch and product
                batch_row = session.execute(select(product_batches).where(product_batches.c.id == it['product_batch_id'])).fetchone()
                batch = dict(batch_row._mapping) if batch_row else None
                prod = None
                if batch:
                    prod_row = session.execute(select(products).where(products.c.id == batch['product_id'])).fetchone()
                    prod = dict(prod_row._mapping) if prod_row else None

                printable_items.append({
                    'product_name': prod['name'] if prod else f"Batch {batch.get('batch_number') if batch else it['product_batch_id']}",
                    'quantity': it['quantity'],
                    'unit_price': float(it['unit_price']),
                })

            store = self.store_service.get_primary_store()
            receipt_text = format_receipt(
                receipt_number=sale['receipt_number'],
                items=printable_items,
                subtotal=float(sale.get('total_amount', 0)),
                tax=0.0,
                total=float(sale.get('total_amount', 0)),
                payment_method=sale.get('payment_method', 'Unknown'),
                amount_paid=float(sale.get('amount_paid', 0)),
                change=float(sale.get('change_amount', 0)),
                store=store,
            )

            printer = ThermalPrinter(backend=None)
            res = printer.print_text(receipt_text)
            if res.get('status') == 'printed':
                QMessageBox.information(self, 'Reprint', 'Receipt sent to printer.')
            else:
                QMessageBox.information(self, 'Reprint', f'Receipt saved to: {res.get("path")}')

        except Exception as e:
            QMessageBox.warning(self, 'Reprint Error', f'Failed to reprint receipt: {e}')

    def expire_batches_action(self) -> None:
        """UI action to expire batches within given days for selected store."""
        try:
            days = int(self.expiry_days_input.value())
            store_text = self.expiry_store_input.text().strip()
            if store_text:
                try:
                    store_id = int(store_text)
                except ValueError:
                    QMessageBox.warning(self, "Input Error", "Store ID must be an integer")
                    return
            else:
                store = self.store_service.get_primary_store()
                if not store:
                    QMessageBox.warning(self, "Store Error", "No primary store configured")
                    return
                store_id = store["id"]

            inv_service = InventoryService(self.session)
            # Use current user id if available, otherwise 0
            user_id = getattr(self.user_session, "user_id", 0)
            expired_count = inv_service.expire_batches_within_days(store_id, days, user_id)
            QMessageBox.information(self, "Expiry Result", f"Expired {expired_count} batches")
            inv_service.session.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to expire batches: {str(e)}")

    def generate_report(self) -> None:
        """Generate selected report."""
        report_type = self.report_type.currentText()
        QMessageBox.information(self, "Report", f"Generated {report_type} report (demo)")

    def open_printer_settings(self) -> None:
        """Open printer settings dialog."""
        dialog = PrinterSettingsDialog(self)
        dialog.exec_()

    def logout(self) -> None:
        """Logout user."""
        self.auth_service.logout(self.user_session.session_id)
        self.close()


# --- Application Entry Point ------------------------------------------------
def main() -> None:
    """Main application entry point."""
    from desktop_app.database import init_db
    
    app = QApplication(sys.argv)

    # Initialize database
    init_db()

    # Initialize authentication service
    auth_service = AuthenticationService()

    # Show login dialog
    login_dialog = LoginDialog(auth_service)
    if login_dialog.exec_() == QDialog.Accepted:
        # Show main window
        window = MainWindow(auth_service, login_dialog.user_session)
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit()


if __name__ == "__main__":
    main()

    def print_thermal_receipt(
        self,
        receipt_number: str,
        items: list,
        subtotal: float,
        tax: float,
        total: float,
        payment_method: str,
        amount_paid: float,
        change: float,
    ) -> None:
        """Print receipt to thermal printer (ESC/POS protocol)."""
        try:
            # Initialize thermal printer (FILE mode for testing/demo)
            # Change PrinterType.FILE to:
            #   PrinterType.USB for USB thermal printer (Epson TM series)
            #   PrinterType.SERIAL for Serial thermal printer (COM port)
            #   PrinterType.NETWORK for Network printer (LAN)
            printer = ThermalPrinter(
                printer_type=PrinterType.FILE,  # Change to USB/SERIAL/NETWORK for actual printer
                output_file="receipts/receipt_{}.txt".format(receipt_number)
            )

            # Prepare receipt items for printing
            receipt_items = []
            for item in items:
                receipt_items.append({
                    "product_name": item.get("product_name", "Unknown Product"),
                    "quantity": item.get("quantity", 0),
                    "unit_price": item.get("unit_price", 0),
                })

            # Get store info
            store = self.store_service.get_primary_store()
            store_name = store.get("name", "PharmaPOS Store") if store else "PharmaPOS Store"

            # Print receipt
            success = printer.print_receipt(
                receipt_number=receipt_number,
                store_name=store_name,
                items=receipt_items,
                subtotal=subtotal,
                tax=tax,
                total=total,
                payment_method=payment_method,
                amount_paid=amount_paid,
                change=change,
                customer_name=self.customer_input.text() or "Walk-in Customer",
                cashier_name=self.user_session.username if self.user_session else "Cashier",
            )

            if success:
                print(f"Receipt #{receipt_number} printed successfully")
            else:
                print(f"Warning: Failed to print receipt #{receipt_number}")
                
            printer.close()

        except Exception as e:
            print(f"Error printing receipt: {str(e)}")

    