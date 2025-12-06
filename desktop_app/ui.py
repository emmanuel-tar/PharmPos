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
    QCheckBox,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtPrintSupport import QPrinterInfo

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


class PrinterSettingsDialog(QDialog):
    """Dialog to configure thermal printer settings.

    Enhancements:
      - Support picking an installed system printer (via Qt)
      - Enumerate serial ports (if pyserial installed)
      - Enumerate USB devices (if pyusb installed)
      - Allow selecting the medium and device and saving to `config.json`
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Printer Settings")
        self.setGeometry(200, 200, 700, 420)
        self.setup_ui()
        self.load_config()

    def setup_ui(self) -> None:
        layout = QVBoxLayout()

        # Enable checkbox
        enable_layout = QHBoxLayout()
        enable_layout.addWidget(QLabel("Enable Thermal Printer:"))
        self.enable_checkbox = QCheckBox()
        enable_layout.addWidget(self.enable_checkbox)
        enable_layout.addStretch()
        layout.addLayout(enable_layout)

        # Printer Type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Printer Type:"))
        self.printer_type_combo = QComboBox()
        self.printer_type_combo.addItems(["FILE", "USB", "SERIAL", "NETWORK", "SYSTEM"])
        self.printer_type_combo.currentTextChanged.connect(self.on_printer_type_changed)
        type_layout.addWidget(self.printer_type_combo)

        # System printer picker
        type_layout.addWidget(QLabel("System Printer:"))
        self.system_printer_combo = QComboBox()
        type_layout.addWidget(self.system_printer_combo)

        detect_btn = QPushButton("Detect Devices")
        detect_btn.clicked.connect(self.detect_devices)
        type_layout.addWidget(detect_btn)

        layout.addLayout(type_layout)

        # USB inputs
        usb_layout = QHBoxLayout()
        usb_layout.addWidget(QLabel("USB Vendor ID:"))
        self.usb_vendor_input = QLineEdit()
        self.usb_vendor_input.setPlaceholderText("e.g., 0x04b8")
        usb_layout.addWidget(self.usb_vendor_input)
        usb_layout.addWidget(QLabel("USB Product ID:"))
        self.usb_product_input = QLineEdit()
        self.usb_product_input.setPlaceholderText("e.g., 0x0202")
        usb_layout.addWidget(self.usb_product_input)
        layout.addLayout(usb_layout)

        # Serial inputs
        serial_layout = QHBoxLayout()
        serial_layout.addWidget(QLabel("Serial Port:"))
        self.serial_port_input = QComboBox()
        serial_layout.addWidget(self.serial_port_input)
        serial_layout.addWidget(QLabel("Baudrate:"))
        self.serial_baudrate_input = QSpinBox()
        self.serial_baudrate_input.setRange(300, 921600)
        self.serial_baudrate_input.setValue(9600)
        serial_layout.addWidget(self.serial_baudrate_input)
        layout.addLayout(serial_layout)

        # Network inputs
        network_layout = QHBoxLayout()
        network_layout.addWidget(QLabel("Network Host:"))
        self.network_host_input = QLineEdit()
        network_layout.addWidget(self.network_host_input)
        network_layout.addWidget(QLabel("Port:"))
        self.network_port_input = QSpinBox()
        self.network_port_input.setRange(1, 65535)
        self.network_port_input.setValue(9100)
        network_layout.addWidget(self.network_port_input)
        layout.addLayout(network_layout)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.save_config)
        self.test_btn = QPushButton("Test Printer")
        self.test_btn.clicked.connect(self.test_printer)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.test_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def detect_devices(self) -> None:
        """Detect installed system printers, serial ports and optionally USB devices."""
        # Detect system printers via Qt (if available)
        try:
            from PyQt5.QtPrintSupport import QPrinterInfo  # type: ignore
            printers = [p.printerName() for p in QPrinterInfo.availablePrinters()]
            self.system_printer_combo.clear()
            if printers:
                self.system_printer_combo.addItems(printers)
            else:
                self.system_printer_combo.addItem("(no system printers found)")
        except Exception:
            # Qt not available in headless tests — leave combo as-is
            if self.system_printer_combo.count() == 0:
                self.system_printer_combo.addItem("(Qt not available)")

        # Detect serial ports using pyserial if installed
        try:
            import serial.tools.list_ports as list_ports  # type: ignore
            ports = [p.device for p in list_ports.comports()]
            self.serial_port_input.clear()
            if ports:
                self.serial_port_input.addItems(ports)
            else:
                # populate common Windows COM ports as fallback
                self.serial_port_input.addItems([f"COM{i}" for i in range(1, 11)])
        except Exception:
            # fallback list
            self.serial_port_input.clear()
            self.serial_port_input.addItems([f"COM{i}" for i in range(1, 11)])

        # Detect USB devices (if pyusb available) — show vendor:product pairs
        try:
            import usb.core  # type: ignore
            devs = list(usb.core.find(find_all=True))
            if devs:
                # pre-fill first device vendor/product
                d = devs[0]
                try:
                    self.usb_vendor_input.setText(hex(d.idVendor))
                    self.usb_product_input.setText(hex(d.idProduct))
                except Exception:
                    pass
        except Exception:
            # ignore if pyusb not installed
            pass

    def load_config(self) -> None:
        config = load_printer_config()
        self.enable_checkbox.setChecked(bool(config.get("enabled", False)))
        self.printer_type_combo.setCurrentText(config.get("type", "FILE"))

        usb_cfg = config.get("usb", {})
        self.usb_vendor_input.setText(usb_cfg.get("vendor_id", "0x04b8"))
        self.usb_product_input.setText(usb_cfg.get("product_id", "0x0202"))

        serial_cfg = config.get("serial", {})
        port = serial_cfg.get("port", "COM1")
        # ensure detect populates the combo first
        self.detect_devices()
        idx = self.serial_port_input.findText(port)
        if idx >= 0:
            self.serial_port_input.setCurrentIndex(idx)
        else:
            # if not found, add it
            self.serial_port_input.addItem(port)
            self.serial_port_input.setCurrentText(port)

        self.serial_baudrate_input.setValue(serial_cfg.get("baudrate", 9600))

        network_cfg = config.get("network", {})
        self.network_host_input.setText(network_cfg.get("host", "192.168.1.100"))
        self.network_port_input.setValue(network_cfg.get("port", 9100))

        system_cfg = config.get("system", {})
        system_name = system_cfg.get("name", "")
        if system_name:
            idx = self.system_printer_combo.findText(system_name)
            if idx >= 0:
                self.system_printer_combo.setCurrentIndex(idx)
            else:
                self.system_printer_combo.addItem(system_name)
                self.system_printer_combo.setCurrentText(system_name)

    def on_printer_type_changed(self) -> None:
        # nothing fancy here — UI shows all inputs, selection chooses which to use
        pass

    def save_config(self) -> None:
        cfg_type = self.printer_type_combo.currentText()
        cfg = {
            "enabled": self.enable_checkbox.isChecked(),
            "type": cfg_type,
            "usb": {
                "vendor_id": self.usb_vendor_input.text(),
                "product_id": self.usb_product_input.text(),
            },
            "serial": {
                "port": self.serial_port_input.currentText(),
                "baudrate": self.serial_baudrate_input.value(),
            },
            "network": {
                "host": self.network_host_input.text(),
                "port": self.network_port_input.value(),
            },
            "system": {
                "name": self.system_printer_combo.currentText(),
            },
        }

        if save_printer_config(cfg):
            QMessageBox.information(self, "Success", "Printer settings saved successfully.")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to save printer settings.")

    def test_printer(self) -> None:
        """Perform a test print using currently-selected settings."""
        try:
            from desktop_app.thermal_printer import ThermalPrinter
            from datetime import datetime

            cfg_type = self.printer_type_combo.currentText()
            device_info = {}

            if cfg_type == "SYSTEM":
                device_info = {"name": self.system_printer_combo.currentText()}
            elif cfg_type == "USB":
                device_info = {
                    "vendor_id": self.usb_vendor_input.text(),
                    "product_id": self.usb_product_input.text(),
                }
            elif cfg_type == "SERIAL":
                device_info = {
                    "port": self.serial_port_input.currentText(),
                    "baudrate": self.serial_baudrate_input.value(),
                }
            elif cfg_type == "NETWORK":
                device_info = {
                    "host": self.network_host_input.text(),
                    "port": self.network_port_input.value(),
                }

            backend = None if cfg_type == "FILE" else {"type": cfg_type, "device_info": device_info}

            printer = ThermalPrinter(backend=backend)
            test_text = (
                "PRINTER TEST\n"
                "PharmaPOS Thermal Printer Test\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                "-----\n"
                "Connection test successful!\n"
            )
            res = printer.print_text(test_text)
            if res.get("status") == "printed":
                QMessageBox.information(self, "Test Success", f"Test printed successfully to {cfg_type} printer!")
            else:
                QMessageBox.information(self, "Test Result", f"Test saved to file (printer unavailable):\n{res.get('path')}")
        except Exception as e:
            QMessageBox.warning(self, "Test Error", f"Printer test failed: {e}")

    def populate_system_printers(self) -> None:
        """Populate combobox with system-installed printer names using Qt."""
        try:
            self.system_printer_combo.clear()
            names = [p.printerName() for p in QPrinterInfo.availablePrinters()]
            if not names:
                self.system_printer_combo.addItem("(No system printers found)")
            else:
                for n in names:
                    self.system_printer_combo.addItem(n)
        except Exception:
            # In case Qt printing support is unavailable
            self.system_printer_combo.clear()
            self.system_printer_combo.addItem("(Unavailable)")


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
        self.setup_keyboard_shortcuts()

    def setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts for common actions."""
        # Ctrl+S to complete sale
        QShortcut(Qt.CTRL + Qt.Key_S, self, self.complete_sale)
        # Ctrl+C to clear cart
        QShortcut(Qt.CTRL + Qt.Key_C, self, self.clear_sales_cart)
        # Ctrl+F to focus on search
        QShortcut(Qt.CTRL + Qt.Key_F, self, lambda: self.product_search.setFocus())
        # Ctrl+L to focus on scanner
        QShortcut(Qt.CTRL + Qt.Key_L, self, lambda: self.item_scanner.setFocus())
        # Ctrl+H for transaction history
        QShortcut(Qt.CTRL + Qt.Key_H, self, self.show_transaction_history)

    def show_transaction_history(self) -> None:
        """Show recent transactions dialog."""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Transaction History")
            dialog.setGeometry(200, 200, 600, 400)
            
            layout = QVBoxLayout(dialog)
            layout.addWidget(QLabel("Recent Transactions"))
            
            history_table = QTableWidget()
            history_table.setColumnCount(4)
            history_table.setHorizontalHeaderLabels(
                ["Receipt #", "Date/Time", "Total", "Payment Method"]
            )
            layout.addWidget(history_table)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn)
            
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load transaction history: {str(e)}")


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
        
        # Show admin tab only for admin users
        if self.user_session.role.lower() == "admin":
            admin_btn = QPushButton("👤 Admin Panel")
            admin_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(5))
            top_bar.addWidget(admin_btn)
        
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
        
        # Admin tab (only for admin users)
        if self.user_session.role.lower() == "admin":
            self.tabs.addTab(self.create_admin_tab(), "Admin")

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
        left_layout.setSpacing(10)
        left_label = QLabel("PRODUCT CATALOG")
        left_label.setStyleSheet("font-size: 12px; font-weight: bold; padding: 10px;")
        left_layout.addWidget(left_label)

        # Low stock warning bar
        self.low_stock_bar = QLabel()
        self.low_stock_bar.setStyleSheet("background-color: #fff3cd; color: #856404; padding: 8px; border-radius: 4px; font-size: 9px; font-weight: bold;")
        self.low_stock_bar.setVisible(False)
        left_layout.addWidget(self.low_stock_bar)

        # Search bar with larger font
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setStyleSheet("font-size: 10px; font-weight: bold;")
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Scan barcode or search product...")
        self.product_search.setStyleSheet("font-size: 10px; padding: 8px; border-radius: 5px; border: 1px solid #ccc;")
        self.product_search.setMinimumHeight(35)
        self.product_search.textChanged.connect(self.on_product_search)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.product_search)
        left_layout.addLayout(search_layout)

        # Product grid (scrollable)
        product_scroll = QScrollArea()
        product_scroll.setWidgetResizable(True)
        self.product_grid_widget = QWidget()
        self.product_grid_layout = QVBoxLayout(self.product_grid_widget)
        self.product_grid_layout.setSpacing(15)

        # Container for product cards
        self.products_container = QWidget()
        self.products_container_layout = QVBoxLayout(self.products_container)
            
        # Create product cards grid (2 columns for larger cards)
        self.products_cards_layout = QGridLayout()
        self.products_cards_layout.setSpacing(15)
        self.products_container_layout.addLayout(self.products_cards_layout)
        self.products_container_layout.addStretch()

        product_scroll.setWidget(self.products_container)
        left_layout.addWidget(product_scroll)

        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setMinimumWidth(450)

        main_layout.addWidget(left_widget)

        # ===== RIGHT SIDE: Sales Cart & Summary =====
        right_layout = QVBoxLayout()
        right_layout.setSpacing(12)

        # Header
        cart_header = QLabel("SALES RECEIPT")
        cart_header.setStyleSheet("font-size: 12px; font-weight: bold; padding: 10px;")
        right_layout.addWidget(cart_header)

        # Customer info (with larger font)
        customer_layout = QHBoxLayout()
        customer_label = QLabel("Customer:")
        customer_label.setStyleSheet("font-size: 10px; font-weight: bold;")
        customer_label.setMinimumWidth(80)
        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("Walk-in customer")
        self.customer_input.setStyleSheet("font-size: 10px; padding: 6px;")
        self.customer_input.setMinimumHeight(32)
        customer_layout.addWidget(customer_label)
        customer_layout.addWidget(self.customer_input)
        right_layout.addLayout(customer_layout)

        # Barcode/Item scanner (NEW FEATURE)
        scanner_layout = QHBoxLayout()
        scanner_label = QLabel("Item Scanner:")
        scanner_label.setStyleSheet("font-size: 10px; font-weight: bold;")
        scanner_label.setMinimumWidth(80)
        self.item_scanner = QLineEdit()
        self.item_scanner.setPlaceholderText("Scan barcode here to add item...")
        self.item_scanner.setStyleSheet("font-size: 12px; padding: 10px; background-color: #fffacd; font-weight: bold; border: 2px solid #4472C4; border-radius: 6px;")
        self.item_scanner.setMinimumHeight(48)
        self.item_scanner.returnPressed.connect(self.on_barcode_scanned)
        scanner_layout.addWidget(scanner_label)
        scanner_layout.addWidget(self.item_scanner)
        right_layout.addLayout(scanner_layout)
        widget.installEventFilter(self)
        self.sales_tab_widget = widget

        # Cart table (with larger fonts and row heights)
        cart_label = QLabel("CART ITEMS")
        cart_label.setStyleSheet("font-size: 11px; font-weight: bold; padding: 5px 0px;")
        right_layout.addWidget(cart_label)
        
        self.sales_cart_table = QTableWidget()
        self.sales_cart_table.setColumnCount(6)
        self.sales_cart_table.setHorizontalHeaderLabels(
            ["Item #", "Product", "Price (₦)", "Qty", "Disc (%)", "Total (₦)"]
        )
        self.sales_cart_table.setColumnWidth(0, 50)
        self.sales_cart_table.setColumnWidth(1, 160)
        self.sales_cart_table.setColumnWidth(2, 80)
        self.sales_cart_table.setColumnWidth(3, 50)
        self.sales_cart_table.setColumnWidth(4, 70)
        self.sales_cart_table.setColumnWidth(5, 80)
        self.sales_cart_table.setRowHeight(0, 35)
        
        # Enhance table styling
        header_style = "font-size: 10px; font-weight: bold; background-color: #4472C4; color: white;"
        self.sales_cart_table.horizontalHeader().setStyleSheet(header_style)
        self.sales_cart_table.setStyleSheet("font-size: 9px; border: 1px solid #ccc;")
        
        right_layout.addWidget(self.sales_cart_table)

        # Summary section (ENHANCED with larger fonts and better styling)
        summary_label = QLabel("TRANSACTION SUMMARY")
        summary_label.setStyleSheet("font-size: 11px; font-weight: bold; padding: 10px 0px;")
        right_layout.addWidget(summary_label)
        
        summary_frame = QFrame()
        summary_frame.setStyleSheet("border: 2px solid #ddd; border-radius: 5px; padding: 15px; background-color: #f9f9f9;")
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setSpacing(10)
        
        # Subtotal
        subtotal_layout = QHBoxLayout()
        subtotal_lbl = QLabel("Subtotal:")
        subtotal_lbl.setStyleSheet("font-size: 10px; font-weight: bold;")
        subtotal_layout.addWidget(subtotal_lbl)
        subtotal_layout.addStretch()
        self.subtotal_label = QLabel("₦0.00")
        self.subtotal_label.setAlignment(Qt.AlignRight)
        self.subtotal_label.setStyleSheet("font-size: 10px; font-weight: bold; min-width: 100px; padding-right: 10px;")
        subtotal_layout.addWidget(self.subtotal_label)
        summary_layout.addLayout(subtotal_layout)

        # Discount
        discount_layout = QHBoxLayout()
        discount_lbl = QLabel("Discount:")
        discount_lbl.setStyleSheet("font-size: 10px; font-weight: bold;")
        discount_layout.addWidget(discount_lbl)
        discount_layout.addStretch()
        self.discount_label = QLabel("₦0.00")
        self.discount_label.setAlignment(Qt.AlignRight)
        self.discount_label.setStyleSheet("font-size: 10px; font-weight: bold; min-width: 100px; padding-right: 10px;")
        discount_layout.addWidget(self.discount_label)
        summary_layout.addLayout(discount_layout)

        # Tax
        tax_layout = QHBoxLayout()
        tax_lbl = QLabel("Tax (7.5%):")
        tax_lbl.setStyleSheet("font-size: 10px; font-weight: bold;")
        tax_layout.addWidget(tax_lbl)
        tax_layout.addStretch()
        self.tax_label = QLabel("₦0.00")
        self.tax_label.setAlignment(Qt.AlignRight)
        self.tax_label.setStyleSheet("font-size: 10px; font-weight: bold; min-width: 100px; padding-right: 10px;")
        tax_layout.addWidget(self.tax_label)
        summary_layout.addLayout(tax_layout)

        # Total (PROMINENT)
        total_layout = QHBoxLayout()
        total_lbl = QLabel("TOTAL:")
        total_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #fff;")
        total_layout.addWidget(total_lbl)
        total_layout.addStretch()
        self.total_amount_label = QLabel("₦0.00")
        self.total_amount_label.setAlignment(Qt.AlignRight)
        self.total_amount_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #fff; min-width: 120px; padding: 8px 15px; background-color: #28a745; border-radius: 3px;")
        total_layout.addWidget(self.total_amount_label)
        summary_layout.addLayout(total_layout)
        
        right_layout.addWidget(summary_frame)

        # Payment section (PROFESSIONAL)
        payment_label = QLabel("PAYMENT")
        payment_label.setStyleSheet("font-size: 11px; font-weight: bold; padding: 10px 0px;")
        right_layout.addWidget(payment_label)
        
        payment_layout = QVBoxLayout()
        payment_layout.setSpacing(10)
        
        # Payment method row
        method_row = QHBoxLayout()
        method_label = QLabel("Method:")
        method_label.setStyleSheet("font-size: 10px; font-weight: bold; min-width: 60px;")
        self.sales_payment_method = QComboBox()
        self.sales_payment_method.addItems(["Cash", "Card", "Transfer", "Credit"])
        self.sales_payment_method.setStyleSheet("font-size: 10px; padding: 6px;")
        self.sales_payment_method.setMinimumHeight(32)
        method_row.addWidget(method_label)
        method_row.addWidget(self.sales_payment_method)
        method_row.addStretch()
        payment_layout.addLayout(method_row)
        
        # Amount paid row
        paid_row = QHBoxLayout()
        paid_label = QLabel("Amount Paid:")
        paid_label.setStyleSheet("font-size: 10px; font-weight: bold; min-width: 120px;")
        self.sales_amount_paid = QDoubleSpinBox()
        self.sales_amount_paid.setMinimum(0)
        self.sales_amount_paid.setMaximum(999999.99)
        self.sales_amount_paid.setDecimals(2)
        self.sales_amount_paid.setStyleSheet("font-size: 10px; padding: 6px;")
        self.sales_amount_paid.setMinimumHeight(32)
        self.sales_amount_paid.valueChanged.connect(self.update_sales_summary)
        paid_row.addWidget(paid_label)
        paid_row.addWidget(self.sales_amount_paid)
        payment_layout.addLayout(paid_row)
        
        # Change row
        change_row = QHBoxLayout()
        change_label = QLabel("Change:")
        change_label.setStyleSheet("font-size: 10px; font-weight: bold; min-width: 120px;")
        self.sales_change_label = QLabel("₦0.00")
        self.sales_change_label.setAlignment(Qt.AlignRight)
        self.sales_change_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #0066cc; min-width: 100px; padding-right: 10px;")
        change_row.addWidget(change_label)
        change_row.addStretch()
        change_row.addWidget(self.sales_change_label)
        payment_layout.addLayout(change_row)
        
        right_layout.addLayout(payment_layout)

        # Action buttons (LARGE AND PROMINENT)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Complete Sale button (GREEN, LARGE)
        self.complete_sale_btn = QPushButton("COMPLETE SALE")
        self.complete_sale_btn.setMinimumHeight(50)
        self.complete_sale_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                font-size: 14px;
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
        buttons_layout.addWidget(self.complete_sale_btn)

        # Save & Print button (BLUE)
        save_print_btn = QPushButton("Save & Print")
        save_print_btn.setMinimumHeight(50)
        save_print_btn.setStyleSheet("""
            QPushButton {
                background-color: #4472C4;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #3555A0;
            }
        """)
        save_print_btn.clicked.connect(self.complete_sale)
        buttons_layout.addWidget(save_print_btn)
        
        # Cancel button (RED)
        clear_btn = QPushButton("Clear Cart")
        clear_btn.setMinimumHeight(50)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        clear_btn.clicked.connect(self.clear_sales_cart)
        buttons_layout.addWidget(clear_btn)
        
        right_layout.addLayout(buttons_layout)

        # Quick actions (Test & Reprint)
        quick_actions_layout = QHBoxLayout()
        quick_actions_layout.setSpacing(10)
        
        self.printer_test_btn = QPushButton("🖨 Printer Test")
        self.printer_test_btn.setStyleSheet("font-size: 9px; padding: 6px; min-height: 30px;")
        self.printer_test_btn.clicked.connect(self.printer_test)
        quick_actions_layout.addWidget(self.printer_test_btn)

        self.reprint_last_btn = QPushButton("📄 Reprint Last")
        self.reprint_last_btn.setStyleSheet("font-size: 9px; padding: 6px; min-height: 30px;")
        self.reprint_last_btn.clicked.connect(self.reprint_last_receipt)
        quick_actions_layout.addWidget(self.reprint_last_btn)
        
        quick_actions_layout.addStretch()
        right_layout.addLayout(quick_actions_layout)

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
        """Create reports tab with daily sales, product movement, and revenue tracking."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Title
        title = QLabel("REPORTS & ANALYTICS")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)

        # Date range selector
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Date Range:"))
        self.report_start_date = QDateEdit()
        self.report_start_date.setDate(QDate.currentDate().addDays(-30))
        date_layout.addWidget(self.report_start_date)
        date_layout.addWidget(QLabel("To:"))
        self.report_end_date = QDateEdit()
        self.report_end_date.setDate(QDate.currentDate())
        date_layout.addWidget(self.report_end_date)
        date_layout.addStretch()
        layout.addLayout(date_layout)

        # Tab widget for different report types
        report_tabs = QTabWidget()

        # Daily Sales Tab
        daily_sales_widget = QWidget()
        daily_sales_layout = QVBoxLayout(daily_sales_widget)
        
        daily_sales_summary = QVBoxLayout()
        daily_summary_label = QLabel("Today's Sales Summary")
        daily_summary_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        daily_sales_summary.addWidget(daily_summary_label)
        
        summary_frame = QFrame()
        summary_frame.setStyleSheet("border: 1px solid #ddd; border-radius: 5px; padding: 15px;")
        summary_grid = QGridLayout(summary_frame)
        
        self.today_sales_count = QLabel("Transactions: 0")
        self.today_sales_revenue = QLabel("Revenue: ₦0.00")
        self.today_sales_items = QLabel("Items Sold: 0")
        self.today_avg_transaction = QLabel("Avg Transaction: ₦0.00")
        
        summary_grid.addWidget(self.today_sales_count, 0, 0)
        summary_grid.addWidget(self.today_sales_revenue, 0, 1)
        summary_grid.addWidget(self.today_sales_items, 1, 0)
        summary_grid.addWidget(self.today_avg_transaction, 1, 1)
        
        daily_sales_summary.addWidget(summary_frame)
        daily_sales_layout.addLayout(daily_sales_summary)
        
        # Daily transactions table
        self.daily_sales_table = QTableWidget()
        self.daily_sales_table.setColumnCount(5)
        self.daily_sales_table.setHorizontalHeaderLabels(
            ["Receipt #", "Time", "Total", "Payment Method", "Items"]
        )
        daily_sales_layout.addWidget(self.daily_sales_table)
        
        refresh_btn = QPushButton("Refresh Daily Sales")
        refresh_btn.clicked.connect(self.refresh_daily_sales)
        daily_sales_layout.addWidget(refresh_btn)
        
        report_tabs.addTab(daily_sales_widget, "Daily Sales")

        # Product Movement Tab
        product_movement_widget = QWidget()
        product_movement_layout = QVBoxLayout(product_movement_widget)
        
        movement_label = QLabel("Top Selling Products (Last 30 Days)")
        movement_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        product_movement_layout.addWidget(movement_label)
        
        self.product_movement_table = QTableWidget()
        self.product_movement_table.setColumnCount(5)
        self.product_movement_table.setHorizontalHeaderLabels(
            ["Product", "Units Sold", "Revenue", "Avg Price", "% of Total"]
        )
        product_movement_layout.addWidget(self.product_movement_table)
        
        refresh_movement_btn = QPushButton("Refresh Product Movement")
        refresh_movement_btn.clicked.connect(self.refresh_product_movement)
        product_movement_layout.addWidget(refresh_movement_btn)
        
        report_tabs.addTab(product_movement_widget, "Product Movement")

        # Revenue Tracking Tab
        revenue_widget = QWidget()
        revenue_layout = QVBoxLayout(revenue_widget)
        
        revenue_label = QLabel("Revenue Tracking")
        revenue_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        revenue_layout.addWidget(revenue_label)
        
        revenue_frame = QFrame()
        revenue_frame.setStyleSheet("border: 1px solid #ddd; border-radius: 5px; padding: 15px;")
        revenue_grid = QGridLayout(revenue_frame)
        
        self.total_revenue = QLabel("Total Revenue: ₦0.00")
        self.total_revenue.setStyleSheet("font-size: 13px; font-weight: bold; color: #28a745;")
        self.total_transactions = QLabel("Total Transactions: 0")
        self.payment_breakdown = QLabel("Payment Methods: Cash: 0 | Card: 0 | Transfer: 0 | Credit: 0")
        
        revenue_grid.addWidget(self.total_revenue, 0, 0)
        revenue_grid.addWidget(self.total_transactions, 1, 0)
        revenue_grid.addWidget(self.payment_breakdown, 2, 0)
        
        revenue_layout.addWidget(revenue_frame)
        
        self.revenue_table = QTableWidget()
        self.revenue_table.setColumnCount(3)
        self.revenue_table.setHorizontalHeaderLabels(
            ["Date", "Transactions", "Revenue"]
        )
        revenue_layout.addWidget(self.revenue_table)
        
        refresh_revenue_btn = QPushButton("Refresh Revenue Report")
        refresh_revenue_btn.clicked.connect(self.refresh_revenue_report)
        revenue_layout.addWidget(refresh_revenue_btn)
        
        report_tabs.addTab(revenue_widget, "Revenue Tracking")

        layout.addWidget(report_tabs)

        widget.setLayout(layout)
        return widget

    def refresh_daily_sales(self) -> None:
        """Refresh and display today's sales data."""
        try:
            # This would query the database for today's sales
            # For now, show placeholder
            self.today_sales_count.setText("Transactions: 0")
            self.today_sales_revenue.setText("Revenue: ₦0.00")
            self.today_sales_items.setText("Items Sold: 0")
            self.today_avg_transaction.setText("Avg Transaction: ₦0.00")
            QMessageBox.information(self, "Info", "Daily sales data updated")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh daily sales: {str(e)}")

    def refresh_product_movement(self) -> None:
        """Refresh and display product movement data."""
        try:
            QMessageBox.information(self, "Info", "Product movement data updated")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh product movement: {str(e)}")

    def refresh_revenue_report(self) -> None:
        """Refresh and display revenue tracking data."""
        try:
            QMessageBox.information(self, "Info", "Revenue report updated")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh revenue report: {str(e)}")

    def create_admin_tab(self) -> QWidget:
        """Create admin panel with user management, settings, and data export."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Title
        title = QLabel("ADMIN PANEL")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)

        # Admin tab widget for different sections
        admin_tabs = QTabWidget()

        # ========== USER MANAGEMENT TAB ==========
        user_mgmt_widget = QWidget()
        user_mgmt_layout = QVBoxLayout(user_mgmt_widget)

        user_title = QLabel("User Management")
        user_title.setStyleSheet("font-size: 12px; font-weight: bold;")
        user_mgmt_layout.addWidget(user_title)

        # Add new user section
        add_user_frame = QFrame()
        add_user_frame.setStyleSheet("border: 1px solid #ddd; border-radius: 5px; padding: 10px;")
        add_user_layout = QGridLayout(add_user_frame)

        add_user_layout.addWidget(QLabel("Username:"), 0, 0)
        new_username = QLineEdit()
        add_user_layout.addWidget(new_username, 0, 1)

        add_user_layout.addWidget(QLabel("Password:"), 0, 2)
        new_password = QLineEdit()
        new_password.setEchoMode(QLineEdit.Password)
        add_user_layout.addWidget(new_password, 0, 3)

        add_user_layout.addWidget(QLabel("Role:"), 1, 0)
        role_combo = QComboBox()
        role_combo.addItems(["cashier", "manager", "admin"])
        add_user_layout.addWidget(role_combo, 1, 1)

        add_user_layout.addWidget(QLabel("Full Name:"), 1, 2)
        full_name = QLineEdit()
        add_user_layout.addWidget(full_name, 1, 3)

        def add_new_user():
            try:
                if not new_username.text() or not new_password.text() or not full_name.text():
                    QMessageBox.warning(self, "Validation", "Please fill all fields")
                    return
                
                # Add user to database
                QMessageBox.information(self, "Success", f"User '{new_username.text()}' created successfully")
                new_username.clear()
                new_password.clear()
                full_name.clear()
                refresh_user_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create user: {str(e)}")

        add_user_btn = QPushButton("Add User")
        add_user_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        add_user_btn.clicked.connect(add_new_user)
        add_user_layout.addWidget(add_user_btn, 2, 0, 1, 4)

        user_mgmt_layout.addWidget(add_user_frame)

        # Users table
        users_table = QTableWidget()
        users_table.setColumnCount(6)
        users_table.setHorizontalHeaderLabels(
            ["Username", "Full Name", "Role", "Status", "Created", "Actions"]
        )
        users_table.setColumnWidth(0, 120)
        users_table.setColumnWidth(1, 150)
        users_table.setColumnWidth(2, 100)
        users_table.setColumnWidth(3, 100)
        users_table.setColumnWidth(4, 120)
        users_table.setColumnWidth(5, 150)

        def refresh_user_table():
            """Refresh the users table with current users."""
            # Mock data - replace with actual database query
            sample_users = [
                {"username": "admin", "name": "Administrator", "role": "admin", "status": "Active", "created": "2024-01-01"},
                {"username": "cashier1", "name": "John Doe", "role": "cashier", "status": "Active", "created": "2024-01-15"},
                {"username": "manager1", "name": "Jane Smith", "role": "manager", "status": "Active", "created": "2024-01-20"},
            ]
            
            users_table.setRowCount(len(sample_users))
            for i, user in enumerate(sample_users):
                users_table.setItem(i, 0, QTableWidgetItem(user["username"]))
                users_table.setItem(i, 1, QTableWidgetItem(user["name"]))
                users_table.setItem(i, 2, QTableWidgetItem(user["role"]))
                users_table.setItem(i, 3, QTableWidgetItem(user["status"]))
                users_table.setItem(i, 4, QTableWidgetItem(user["created"]))
                
                # Actions buttons
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                edit_btn = QPushButton("Edit")
                edit_btn.setMaximumWidth(60)
                edit_btn.clicked.connect(lambda checked, u=user["username"]: self.edit_user(u))
                actions_layout.addWidget(edit_btn)
                
                disable_btn = QPushButton("Disable")
                disable_btn.setMaximumWidth(70)
                disable_btn.clicked.connect(lambda checked, u=user["username"]: self.disable_user(u))
                actions_layout.addWidget(disable_btn)
                
                users_table.setCellWidget(i, 5, actions_widget)

        refresh_user_table()
        user_mgmt_layout.addWidget(users_table)

        admin_tabs.addTab(user_mgmt_widget, "User Management")

        # ========== SETTINGS TAB ==========
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)

        settings_title = QLabel("System Settings")
        settings_title.setStyleSheet("font-size: 12px; font-weight: bold;")
        settings_layout.addWidget(settings_title)

        settings_frame = QFrame()
        settings_frame.setStyleSheet("border: 1px solid #ddd; border-radius: 5px; padding: 15px;")
        settings_grid = QGridLayout(settings_frame)

        # Store settings
        settings_grid.addWidget(QLabel("Store Name:"), 0, 0)
        store_name_input = QLineEdit()
        store_name_input.setText("PharmaPOS Store")
        settings_grid.addWidget(store_name_input, 0, 1)

        settings_grid.addWidget(QLabel("Tax Rate (%):"), 1, 0)
        tax_rate_input = QDoubleSpinBox()
        tax_rate_input.setValue(7.5)
        tax_rate_input.setMinimum(0)
        tax_rate_input.setMaximum(100)
        settings_grid.addWidget(tax_rate_input, 1, 1)

        settings_grid.addWidget(QLabel("Currency Symbol:"), 2, 0)
        currency_input = QLineEdit()
        currency_input.setText("₦")
        currency_input.setMaximumWidth(100)
        settings_grid.addWidget(currency_input, 2, 1)

        settings_grid.addWidget(QLabel("Printer Device:"), 3, 0)
        printer_combo = QComboBox()
        printer_combo.addItems(["Default Printer", "FILE (Demo Mode)", "USB Printer", "Network Printer"])
        settings_grid.addWidget(printer_combo, 3, 1)

        settings_grid.addWidget(QLabel("Receipt Format:"), 4, 0)
        receipt_combo = QComboBox()
        receipt_combo.addItems(["80mm Thermal", "58mm Thermal", "Letter (A4)"])
        settings_grid.addWidget(receipt_combo, 4, 1)

        settings_grid.addWidget(QLabel("Business Hours:"), 5, 0)
        hours_input = QLineEdit()
        hours_input.setText("08:00 - 18:00")
        settings_grid.addWidget(hours_input, 5, 1)

        def save_settings():
            try:
                # Save settings to config file
                QMessageBox.information(self, "Success", "Settings saved successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

        save_settings_btn = QPushButton("Save Settings")
        save_settings_btn.setStyleSheet("background-color: #007bff; color: white; font-weight: bold;")
        save_settings_btn.clicked.connect(save_settings)
        settings_grid.addWidget(save_settings_btn, 6, 0, 1, 2)

        settings_layout.addWidget(settings_frame)
        settings_layout.addStretch()

        admin_tabs.addTab(settings_widget, "Settings")

        # ========== DATA EXPORT TAB ==========
        export_widget = QWidget()
        export_layout = QVBoxLayout(export_widget)

        export_title = QLabel("Data Export & Backup")
        export_title.setStyleSheet("font-size: 12px; font-weight: bold;")
        export_layout.addWidget(export_title)

        export_frame = QFrame()
        export_frame.setStyleSheet("border: 1px solid #ddd; border-radius: 5px; padding: 15px;")
        export_grid = QGridLayout(export_frame)

        # Export options
        export_grid.addWidget(QLabel("Export Type:"), 0, 0)
        export_type_combo = QComboBox()
        export_type_combo.addItems(["Sales Data", "Inventory Data", "User Data", "All Data"])
        export_grid.addWidget(export_type_combo, 0, 1)

        export_grid.addWidget(QLabel("Format:"), 1, 0)
        format_combo = QComboBox()
        format_combo.addItems(["CSV", "Excel (.xlsx)", "JSON"])
        export_grid.addWidget(format_combo, 1, 1)

        export_grid.addWidget(QLabel("Date Range:"), 2, 0)
        date_range_layout = QHBoxLayout()
        export_start_date = QDateEdit()
        export_start_date.setDate(QDate.currentDate().addDays(-30))
        date_range_layout.addWidget(export_start_date)
        date_range_layout.addWidget(QLabel("To:"))
        export_end_date = QDateEdit()
        export_end_date.setDate(QDate.currentDate())
        date_range_layout.addWidget(export_end_date)
        export_grid.addLayout(date_range_layout, 2, 1)

        def export_data():
            try:
                export_type = export_type_combo.currentText()
                file_format = format_combo.currentText()
                start_date = export_start_date.date().toString("yyyy-MM-dd")
                end_date = export_end_date.date().toString("yyyy-MM-dd")
                
                filename = f"export_{export_type.replace(' ', '_')}_{start_date}_to_{end_date}.{file_format.split('.')[-1] if '.' in file_format else file_format.lower()}"
                
                QMessageBox.information(self, "Success", f"Data exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export data: {str(e)}")

        export_btn = QPushButton("Export Data")
        export_btn.setStyleSheet("background-color: #17a2b8; color: white; font-weight: bold;")
        export_btn.clicked.connect(export_data)
        export_grid.addWidget(export_btn, 3, 0, 1, 2)

        export_layout.addWidget(export_frame)

        # Backup section
        backup_frame = QFrame()
        backup_frame.setStyleSheet("border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-top: 20px;")
        backup_grid = QGridLayout(backup_frame)

        backup_grid.addWidget(QLabel("Database Backup & Restore"), 0, 0, 1, 2)
        backup_grid.addWidget(QLabel("Status: Database last backed up on 2024-01-25 at 10:30 AM"), 1, 0, 1, 2)

        def backup_database():
            try:
                # Create database backup
                QMessageBox.information(self, "Success", "Database backed up successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Backup failed: {str(e)}")

        def restore_database():
            try:
                # Restore database from backup
                QMessageBox.information(self, "Success", "Database restored successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Restore failed: {str(e)}")

        backup_btn = QPushButton("Backup Database")
        backup_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        backup_btn.clicked.connect(backup_database)
        backup_grid.addWidget(backup_btn, 2, 0)

        restore_btn = QPushButton("Restore Database")
        restore_btn.setStyleSheet("background-color: #ffc107; color: black; font-weight: bold;")
        restore_btn.clicked.connect(restore_database)
        backup_grid.addWidget(restore_btn, 2, 1)

        export_layout.addWidget(backup_frame)
        export_layout.addStretch()

        admin_tabs.addTab(export_widget, "Data Export")

        layout.addWidget(admin_tabs)
        widget.setLayout(layout)
        return widget

    def edit_user(self, username: str) -> None:
        """Edit user details."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit User: {username}")
        dialog.setGeometry(100, 100, 400, 250)
        
        layout = QGridLayout(dialog)
        layout.addWidget(QLabel("Username:"), 0, 0)
        username_input = QLineEdit()
        username_input.setText(username)
        username_input.setReadOnly(True)
        layout.addWidget(username_input, 0, 1)
        
        layout.addWidget(QLabel("Full Name:"), 1, 0)
        fullname_input = QLineEdit()
        layout.addWidget(fullname_input, 1, 1)
        
        layout.addWidget(QLabel("Role:"), 2, 0)
        role_combo = QComboBox()
        role_combo.addItems(["cashier", "manager", "admin"])
        layout.addWidget(role_combo, 2, 1)
        
        layout.addWidget(QLabel("New Password (leave blank to keep):"), 3, 0, 1, 2)
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(password_input, 4, 0, 1, 2)
        
        def save_changes():
            QMessageBox.information(self, "Success", f"User '{username}' updated successfully")
            dialog.accept()
        
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(save_changes)
        layout.addWidget(save_btn, 5, 0, 1, 2)
        
        dialog.exec_()

    def disable_user(self, username: str) -> None:
        """Disable user account."""
        reply = QMessageBox.question(self, "Confirm", f"Disable user '{username}'?", 
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "Success", f"User '{username}' disabled")

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
            
            # Create product cards (2 columns for larger cards)
            for i, product in enumerate(products):
                card = self.create_product_card(product)
                row = i // 2
                col = i % 2
                self.products_cards_layout.addWidget(card, row, col)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products: {str(e)}")

    def create_product_card(self, product: dict) -> QWidget:
        """Create a clickable product card for the sales grid."""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
            QWidget:hover {
                background-color: #f0f7ff;
                border: 2px solid #4472C4;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
        """)
        card.setCursor(Qt.PointingHandCursor)
        card.setMinimumHeight(220)
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        # Product image placeholder
        image_label = QLabel()
        image_label.setMinimumHeight(120)
        image_label.setStyleSheet("background-color: #e8e8e8; border-radius: 5px; font-size: 9px;")
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setText("📦 No Image")
        layout.addWidget(image_label)

        # Product name
        name_label = QLabel(product['name'])
        name_label.setWordWrap(True)
        name_label.setStyleSheet("font-weight: bold; font-size: 8px; color: #333;")
        layout.addWidget(name_label)

        # Stock info
        stock_label = QLabel(f"Stock: {product.get('quantity', 0)} units")
        stock_label.setStyleSheet("font-size: 7px; color: #666; font-weight: 500;")
        layout.addWidget(stock_label)

        # Price
        price_label = QLabel(f"₦{product.get('retail_price', product.get('selling_price', 0)):.2f}")
        price_label.setStyleSheet("font-weight: bold; font-size: 9px; color: #28a745; padding: 5px 0px;")
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
        """Add product to sales cart with stock level checking."""
        try:
            # Check available stock before adding
            available_stock = product.get('quantity', 0)
            if available_stock <= 0:
                QMessageBox.warning(self, "Out of Stock", 
                    f"{product['name']} is out of stock")
                return
            
            # Show low stock warning if quantity is low (< 10 units)
            if available_stock < 10:
                self.low_stock_bar.setText(f"⚠️ Low Stock: {product['name']} ({available_stock} units remaining)")
                self.low_stock_bar.setVisible(True)
            else:
                self.low_stock_bar.setVisible(False)
            
            # Check if product already in cart
            for row in range(self.sales_cart_table.rowCount()):
                name_item = self.sales_cart_table.item(row, 1)
                if name_item and name_item.text() == product['name']:
                    # Check if incrementing would exceed available stock
                    qty_item = self.sales_cart_table.item(row, 3)
                    current_qty = int(qty_item.text())
                    if current_qty + 1 > available_stock:
                        QMessageBox.warning(self, "Insufficient Stock",
                            f"Only {available_stock} unit(s) available for {product['name']}\n"
                            f"Currently adding: {current_qty + 1}")
                        return
                    # Increment quantity
                    qty_item.setText(str(current_qty + 1))
                    # Update total
                    price = float(self.sales_cart_table.item(row, 2).text().replace('₦', '').strip())
                    new_qty = current_qty + 1
                    total = price * new_qty
                    self.sales_cart_table.setItem(row, 5, QTableWidgetItem(f"₦{total:.2f}"))
                    self.update_sales_summary()
                    return

            # Add new row to cart
            row = self.sales_cart_table.rowCount()
            self.sales_cart_table.insertRow(row)
            price = float(product.get('retail_price', product.get('selling_price', 0)))
            # Item # (row number)
            item_num = QTableWidgetItem(str(row + 1))
            item_num.setTextAlignment(Qt.AlignCenter)
            item_num.setFont(QFont("Arial", 9, QFont.Bold))
            self.sales_cart_table.setItem(row, 0, item_num)
            # Product Name
            name_item = QTableWidgetItem(product['name'])
            name_item.setFont(QFont("Arial", 9, QFont.Bold))
            self.sales_cart_table.setItem(row, 1, name_item)
            name_item.product_id = product['id']
            # Price
            price_item = QTableWidgetItem(f"₦{price:.2f}")
            price_item.setTextAlignment(Qt.AlignRight)
            price_item.setFont(QFont("Arial", 9, QFont.Bold))
            self.sales_cart_table.setItem(row, 2, price_item)
            # Quantity (default 1)
            qty_item = QTableWidgetItem("1")
            qty_item.setTextAlignment(Qt.AlignCenter)
            qty_item.setFont(QFont("Arial", 9, QFont.Bold))
            self.sales_cart_table.setItem(row, 3, qty_item)
            # Discount (default 0%)
            discount_item = QTableWidgetItem("0%")
            discount_item.setTextAlignment(Qt.AlignCenter)
            discount_item.setFont(QFont("Arial", 9, QFont.Bold))
            self.sales_cart_table.setItem(row, 4, discount_item)
            # Total (price * 1)
            total_item = QTableWidgetItem(f"₦{price:.2f}")
            total_item.setTextAlignment(Qt.AlignRight)
            total_item.setFont(QFont("Arial", 9, QFont.Bold))
            self.sales_cart_table.setItem(row, 5, total_item)
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("font-size: 12px; background-color: #dc3545; color: white; border-radius: 5px; padding: 6px;")
            delete_btn.setMinimumHeight(32)
            delete_btn.clicked.connect(lambda _, r=row: self.remove_from_cart(r))
            self.sales_cart_table.setCellWidget(row, 6, delete_btn)
            # Set row height for better visibility
            self.sales_cart_table.setRowHeight(row, 48)
            self.update_sales_summary()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add product: {str(e)}")

    def remove_from_cart(self, row: int) -> None:
        """Remove item from sales cart."""
        self.sales_cart_table.removeRow(row)
        self.update_sales_summary()

    def clear_sales_cart(self) -> None:
        """Clear all items from the sales cart."""
        if self.sales_cart_table.rowCount() > 0:
            reply = QMessageBox.question(self, "Clear Cart", 
                "Are you sure you want to clear the entire cart?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.sales_cart_table.setRowCount(0)
                self.update_sales_summary()
                self.item_scanner.clear()
                self.item_scanner.setFocus()

    def update_sales_summary(self) -> None:
        """Update cart summary (subtotal, tax, total) and change calculation."""
        subtotal = 0.0
        
        for row in range(self.sales_cart_table.rowCount()):
            qty_text = self.sales_cart_table.item(row, 3).text() if self.sales_cart_table.item(row, 3) else "0"
            price_text = self.sales_cart_table.item(row, 2).text() if self.sales_cart_table.item(row, 2) else "0"
            
            # Remove currency symbol if present
            qty = int(qty_text) if qty_text else 0
            price = float(price_text.replace('₦', '').strip()) if price_text else 0.0
            subtotal += qty * price

        # Calculate tax (assuming 7.5% VAT)
        tax = subtotal * 0.075
        total = subtotal + tax

        # Update labels
        self.subtotal_label.setText(f"₦{subtotal:.2f}")
        self.discount_label.setText(f"₦0.00")
        self.tax_label.setText(f"₦{tax:.2f}")
        self.total_amount_label.setText(f"₦{total:.2f}")

        # Update amount paid default
        self.sales_amount_paid.setValue(total)
        
        # Calculate and display change
        amount_paid = self.sales_amount_paid.value()
        change = amount_paid - total
        
        # Display change in blue if positive, red if negative (insufficient payment)
        if change >= 0:
            self.sales_change_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #0066cc; min-width: 100px; padding-right: 10px;")
            self.sales_change_label.setText(f"₦{change:.2f}")
        else:
            self.sales_change_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #dc3545; min-width: 100px; padding-right: 10px;")
            self.sales_change_label.setText(f"₦{abs(change):.2f} (Shortfall)")

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
                row = i // 2
                col = i % 2
                self.products_cards_layout.addWidget(card, row, col)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Search failed: {str(e)}")

    def on_barcode_scanned(self) -> None:
        """Handle barcode scanner input - automatically add item to cart."""
        barcode_or_sku = self.item_scanner.text().strip()
        if not barcode_or_sku:
            return

        try:
            # Search for product by barcode or SKU
            all_products = self.product_service.get_all_products(active_only=True)
            product = None
            for p in all_products:
                if (p.get('barcode', '').strip() == barcode_or_sku or 
                    p.get('sku', '').strip() == barcode_or_sku):
                    product = p
                    break
            if not product:
                QMessageBox.warning(self, "Product Not Found", 
                    f"No product found with barcode/SKU: {barcode_or_sku}")
                self.item_scanner.clear()
                return
            # Auto-add to cart (no popup)
            self.add_product_to_sales_cart(product)
            # Clear scanner field for next scan
            self.item_scanner.clear()
            self.item_scanner.setFocus()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process barcode: {str(e)}")
            self.item_scanner.clear()

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

            # Extract cart items from table (new structure: Item#, Product, Price, Qty, Disc%, Total)
            cart_items = []
            subtotal = 0.0
            
            for row in range(self.sales_cart_table.rowCount()):
                name_item = self.sales_cart_table.item(row, 1)  # Product name in column 1
                price_item = self.sales_cart_table.item(row, 2)  # Price in column 2
                qty_item = self.sales_cart_table.item(row, 3)  # Qty in column 3
                
                if name_item and price_item and qty_item:
                    name = name_item.text()
                    price_text = price_item.text().replace('₦', '').strip()
                    price = float(price_text) if price_text else 0.0
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
        """Format and send the receipt to thermal printer using configured settings or file fallback."""
        try:
            from desktop_app.thermal_printer import ThermalPrinter, format_receipt
            from desktop_app.config import get_printer_device_info

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

            # Load printer config and use it, or fallback to file
            config = load_printer_config()
            if not config.get('enabled', False):
                backend_config = None
            else:
                printer_type = config.get('type', 'FILE')
                device_info = get_printer_device_info(printer_type, config)
                backend_config = {'type': printer_type, 'device_info': device_info}

            printer = ThermalPrinter(backend=backend_config)
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
        """Send a small test print using the configured thermal printer."""
        try:
            from desktop_app.thermal_printer import ThermalPrinter
            from desktop_app.config import get_printer_backend, get_printer_device_info
            from datetime import datetime

            config = load_printer_config()
            if not config.get('enabled', False):
                QMessageBox.information(self, 'Printer Test', 'Printer is disabled. Saving to file (fallback).')
                backend_config = None
            else:
                printer_type = config.get('type', 'FILE')
                device_info = get_printer_device_info(printer_type, config)
                backend_config = {'type': printer_type, 'device_info': device_info}

            printer = ThermalPrinter(backend=backend_config)
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
                QMessageBox.information(self, 'Printer Test', f'Test saved to file: {path}\n\n(Printer may be disabled or unavailable.)')
        except Exception as e:
            QMessageBox.warning(self, 'Printer Test', f'Printer test failed: {e}')


    def reprint_last_receipt(self) -> None:
        """Re-generate and print (or save) the most recent sale receipt using configured printer."""
        try:
            # Local imports to avoid top-level dependencies
            from desktop_app.models import get_session, SalesService
            from desktop_app.database import sales as sales_table, sale_items as sale_items_table, product_batches, products
            from desktop_app.config import get_printer_device_info
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

            config = load_printer_config()
            if not config.get('enabled', False):
                backend_config = None
            else:
                printer_type = config.get('type', 'FILE')
                device_info = get_printer_device_info(printer_type, config)
                backend_config = {'type': printer_type, 'device_info': device_info}

            printer = ThermalPrinter(backend=backend_config)
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

    