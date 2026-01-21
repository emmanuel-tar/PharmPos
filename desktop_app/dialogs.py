"""
PharmaPOS Dialog Classes

This module contains all dialog classes extracted from the monolithic ui.py file.
Each dialog is now properly separated and uses the new UI components and constants.
"""

import sys
from decimal import Decimal
from typing import Optional, Dict, Any, List
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QTabWidget, QTableWidget,
    QTableWidgetItem, QDialog, QLineEdit, QSpinBox, QComboBox,
    QMessageBox, QDateEdit, QDoubleSpinBox, QFileDialog, QTextEdit,
    QScrollArea, QFrame, QCheckBox, QShortcut, QGroupBox,
    QFormLayout, QSplitter, QProgressBar
)
from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPixmap

from .ui_constants import Colors, Fonts, Dimensions, Styles, Messages
from .ui_components import (
    StyledButton, FormField, Card, LoadingIndicator, ConfirmationDialog,
    StyledTable, SearchWidget, StatusBar, show_message, show_error,
    show_success, ask_confirmation, get_input, WorkerThread
)
from .auth import AuthenticationService, UserSession
from .models import (
    StoreService, UserService, ProductService, InventoryService,
    SalesService, get_session
)
from .sales import SalesTransaction
from .printer import ThermalPrinter, PrinterType, ReceiptGenerator
from .inventory import BatchManager, InventoryAlerts
from .reports import SalesReporter, InventoryReporter
from .product_manager import ProductImportExporter
from .config import load_printer_config, save_printer_config
from .dashboard_widgets import (
    KPICard, SalesTrendChart, ProfitMarginWidget, InventoryAlertWidget
)
from .settings_dialog import SettingsDialog
from .user_management_dialog import UserManagementDialog
from .compliance_dashboard import ComplianceDashboard
from .analytics import DashboardAnalytics


class PrinterSettingsDialog(QDialog):
    """Dialog to configure thermal printer settings with modern UI."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Printer Settings")
        self.setFixedSize(Dimensions.DIALOG_WIDTH, Dimensions.DIALOG_HEIGHT)
        self.setup_ui()
        self.load_config()

    def setup_ui(self) -> None:
        """Setup modern printer settings UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(Dimensions.MARGIN_MEDIUM, Dimensions.MARGIN_MEDIUM,
                                Dimensions.MARGIN_MEDIUM, Dimensions.MARGIN_MEDIUM)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Title
        title = QLabel("🖨 Printer Configuration")
        title.setFont(Fonts.TITLE)
        title.setStyleSheet(f"color: {Colors.PRIMARY}; margin-bottom: {Dimensions.SPACING_LARGE}px;")
        layout.addWidget(title)

        # Enable checkbox
        enable_layout = QHBoxLayout()
        enable_layout.addWidget(QLabel("Enable Thermal Printer:"))
        self.enable_checkbox = QCheckBox()
        self.enable_checkbox.setFont(Fonts.BODY)
        enable_layout.addWidget(self.enable_checkbox)
        enable_layout.addStretch()
        layout.addLayout(enable_layout)

        # Printer Type selection
        type_card = Card("Printer Type & Connection")
        type_layout = QVBoxLayout()
        type_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Type selection
        type_select_layout = QHBoxLayout()
        type_select_layout.addWidget(QLabel("Printer Type:"))
        self.printer_type_combo = QComboBox()
        self.printer_type_combo.addItems(["FILE", "USB", "SERIAL", "NETWORK", "SYSTEM"])
        self.printer_type_combo.currentTextChanged.connect(self.on_printer_type_changed)
        self.printer_type_combo.setStyleSheet(Styles.input_field())
        type_select_layout.addWidget(self.printer_type_combo)
        type_layout.addLayout(type_select_layout)

        # System printer picker
        system_layout = QHBoxLayout()
        system_layout.addWidget(QLabel("System Printer:"))
        self.system_printer_combo = QComboBox()
        self.system_printer_combo.setStyleSheet(Styles.input_field())
        system_layout.addWidget(self.system_printer_combo)

        detect_btn = StyledButton("Detect Devices", "primary")
        detect_btn.clicked.connect(self.detect_devices)
        system_layout.addWidget(detect_btn)
        type_layout.addLayout(system_layout)

        type_card.add_widget(QWidget())
        type_card.layout.addLayout(type_layout)
        layout.addWidget(type_card)

        # Connection settings cards
        self.usb_card = self._create_usb_settings_card()
        self.serial_card = self._create_serial_settings_card()
        self.network_card = self._create_network_settings_card()

        layout.addWidget(self.usb_card)
        layout.addWidget(self.serial_card)
        layout.addWidget(self.network_card)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_btn = StyledButton("Save Settings", "success")
        self.save_btn.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_btn)

        self.test_btn = StyledButton("Test Printer", "primary")
        self.test_btn.clicked.connect(self.test_printer)
        button_layout.addWidget(self.test_btn)

        cancel_btn = StyledButton("Cancel", "danger")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Initially hide connection cards
        self.on_printer_type_changed()

    def _create_usb_settings_card(self) -> Card:
        """Create USB settings card."""
        card = Card("USB Printer Settings")
        layout = QVBoxLayout()
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        layout.addWidget(FormField("Vendor ID:", QLineEdit("0x04b8"),
                                 tooltip="USB Vendor ID (hex format, e.g., 0x04b8)"))
        layout.addWidget(FormField("Product ID:", QLineEdit("0x0202"),
                                 tooltip="USB Product ID (hex format, e.g., 0x0202)"))

        card.add_widget(QWidget())
        card.layout.addLayout(layout)
        return card

    def _create_serial_settings_card(self) -> Card:
        """Create serial settings card."""
        card = Card("Serial Printer Settings")
        layout = QVBoxLayout()
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Serial Port:"))
        self.serial_port_combo = QComboBox()
        self.serial_port_combo.setStyleSheet(Styles.input_field())
        port_layout.addWidget(self.serial_port_combo)
        layout.addLayout(port_layout)

        baud_layout = QHBoxLayout()
        baud_layout.addWidget(QLabel("Baudrate:"))
        self.serial_baudrate_input = QSpinBox()
        self.serial_baudrate_input.setRange(300, 921600)
        self.serial_baudrate_input.setValue(9600)
        self.serial_baudrate_input.setStyleSheet(Styles.input_field())
        baud_layout.addWidget(self.serial_baudrate_input)
        layout.addLayout(baud_layout)

        card.add_widget(QWidget())
        card.layout.addLayout(layout)
        return card

    def _create_network_settings_card(self) -> Card:
        """Create network settings card."""
        card = Card("Network Printer Settings")
        layout = QVBoxLayout()
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        layout.addWidget(FormField("Host:", QLineEdit("192.168.1.100"),
                                 tooltip="Printer IP address or hostname"))
        layout.addWidget(FormField("Port:", QSpinBox(),
                                 tooltip="Printer port number"))

        card.add_widget(QWidget())
        card.layout.addLayout(layout)
        return card

    def detect_devices(self) -> None:
        """Detect installed system printers, serial ports and USB devices."""
        try:
            from PyQt5.QtPrintSupport import QPrinterInfo
            printers = [p.printerName() for p in QPrinterInfo.availablePrinters()]
            self.system_printer_combo.clear()
            if printers:
                self.system_printer_combo.addItems(printers)
            else:
                self.system_printer_combo.addItem("(no system printers found)")
        except Exception:
            if self.system_printer_combo.count() == 0:
                self.system_printer_combo.addItem("(Qt not available)")

        # Detect serial ports
        try:
            import serial.tools.list_ports as list_ports
            ports = [p.device for p in list_ports.comports()]
            self.serial_port_combo.clear()
            if ports:
                self.serial_port_combo.addItems(ports)
            else:
                self.serial_port_combo.addItems([f"COM{i}" for i in range(1, 11)])
        except Exception:
            self.serial_port_combo.clear()
            self.serial_port_combo.addItems([f"COM{i}" for i in range(1, 11)])

        # Detect USB devices
        try:
            import usb.core
            devs = list(usb.core.find(find_all=True))
            if devs and len(devs) > 0:
                d = devs[0]
                try:
                    # Update USB fields with first device found
                    vendor_id = hex(d.idVendor)
                    product_id = hex(d.idProduct)
                    # Note: Would need to access the actual input fields here
                except Exception:
                    pass
        except Exception:
            pass

    def load_config(self) -> None:
        """Load printer configuration."""
        config = load_printer_config()
        self.enable_checkbox.setChecked(bool(config.get("enabled", False)))
        self.printer_type_combo.setCurrentText(config.get("type", "FILE"))

        usb_cfg = config.get("usb", {})
        # Set USB values in the card inputs

        serial_cfg = config.get("serial", {})
        port = serial_cfg.get("port", "COM1")
        self.detect_devices()  # Populate combo first
        idx = self.serial_port_combo.findText(port)
        if idx >= 0:
            self.serial_port_combo.setCurrentIndex(idx)
        else:
            self.serial_port_combo.addItem(port)
            self.serial_port_combo.setCurrentText(port)

        self.serial_baudrate_input.setValue(serial_cfg.get("baudrate", 9600))

        network_cfg = config.get("network", {})
        # Set network values in the card inputs

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
        """Show/hide connection settings based on printer type."""
        printer_type = self.printer_type_combo.currentText()

        self.usb_card.setVisible(printer_type == "USB")
        self.serial_card.setVisible(printer_type == "SERIAL")
        self.network_card.setVisible(printer_type == "NETWORK")
        self.system_printer_combo.setVisible(printer_type == "SYSTEM")

    def save_config(self) -> None:
        """Save printer configuration."""
        cfg_type = self.printer_type_combo.currentText()
        cfg = {
            "enabled": self.enable_checkbox.isChecked(),
            "type": cfg_type,
            "usb": {
                "vendor_id": "0x04b8",  # Get from USB card inputs
                "product_id": "0x0202",
            },
            "serial": {
                "port": self.serial_port_combo.currentText(),
                "baudrate": self.serial_baudrate_input.value(),
            },
            "network": {
                "host": "192.168.1.100",  # Get from network card inputs
                "port": 9100,
            },
            "system": {
                "name": self.system_printer_combo.currentText(),
            },
        }

        if save_printer_config(cfg):
            show_success(self, "Printer settings saved successfully.")
            self.accept()
        else:
            show_error(self, "Failed to save printer settings.")

    def test_printer(self) -> None:
        """Perform a test print."""
        try:
            from datetime import datetime

            cfg_type = self.printer_type_combo.currentText()
            device_info = {}

            if cfg_type == "SYSTEM":
                device_info = {"name": self.system_printer_combo.currentText()}
            elif cfg_type == "USB":
                device_info = {"vendor_id": "0x04b8", "product_id": "0x0202"}
            elif cfg_type == "SERIAL":
                device_info = {
                    "port": self.serial_port_combo.currentText(),
                    "baudrate": self.serial_baudrate_input.value(),
                }
            elif cfg_type == "NETWORK":
                device_info = {"host": "192.168.1.100", "port": 9100}

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
                show_success(self, "Test printed successfully!")
            else:
                show_message(self, "Test Result", f"Test saved to file:\n{res.get('path')}")
        except Exception as e:
            show_error(self, f"Printer test failed: {e}")


class StockReceivingDialog(QDialog):
    """Modern dialog for receiving stock with comprehensive pricing and alerts."""

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.product_service = ProductService(session)
        self.result_data = None
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup modern stock receiving UI."""
        self.setWindowTitle("📦 Receive Stock")
        self.setFixedSize(Dimensions.DIALOG_WIDTH + 200, Dimensions.DIALOG_HEIGHT + 100)

        layout = QVBoxLayout()
        layout.setContentsMargins(Dimensions.MARGIN_MEDIUM, Dimensions.MARGIN_MEDIUM,
                                Dimensions.MARGIN_MEDIUM, Dimensions.MARGIN_MEDIUM)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Title
        title = QLabel("📦 Stock Receiving")
        title.setFont(Fonts.TITLE)
        title.setStyleSheet(f"color: {Colors.PRIMARY}; margin-bottom: {Dimensions.SPACING_LARGE}px;")
        layout.addWidget(title)

        # Scroll area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        form_layout = QVBoxLayout(scroll_widget)
        form_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Product Information Card
        product_card = Card("🏷 Product Information")
        product_layout = QVBoxLayout()

        self.product_combo = QComboBox()
        self.product_combo.currentIndexChanged.connect(self._on_product_changed)
        self.product_combo.setStyleSheet(Styles.input_field())
        product_layout.addWidget(QLabel("Select Product:"))
        product_layout.addWidget(self.product_combo)

        product_card.add_widget(QWidget())
        product_card.layout.addLayout(product_layout)
        form_layout.addWidget(product_card)

        # Batch Details Card
        batch_card = Card("📦 Batch Details")
        batch_layout = QVBoxLayout()
        batch_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        self.batch_number_input = QLineEdit()
        self.batch_number_input.setPlaceholderText("e.g., BATCH-001, LOT-2025-001")
        batch_layout.addWidget(FormField("Batch Number:", self.batch_number_input, required=True))

        quantity_layout = QHBoxLayout()
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 100000)
        self.quantity_input.setValue(1)
        quantity_layout.addWidget(FormField("Quantity (units):", self.quantity_input, required=True))
        batch_layout.addLayout(quantity_layout)

        self.expiry_date_input = QDateEdit()
        self.expiry_date_input.setCalendarPopup(True)
        self.expiry_date_input.setDate(QDate.currentDate().addMonths(12))
        self.expiry_date_input.setDateRange(QDate.currentDate(), QDate(2099, 12, 31))
        batch_layout.addWidget(FormField("Expiry Date:", self.expiry_date_input, required=True))

        batch_card.add_widget(QWidget())
        batch_card.layout.addLayout(batch_layout)
        form_layout.addWidget(batch_card)

        # Pricing Card
        pricing_card = Card("💰 Cost & Pricing")
        pricing_layout = QVBoxLayout()
        pricing_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        self.cost_price_input = QDoubleSpinBox()
        self.cost_price_input.setRange(0, 999999.99)
        self.cost_price_input.setDecimals(2)
        pricing_layout.addWidget(FormField("Cost Price (₦):", self.cost_price_input, required=True))

        self.retail_price_input = QDoubleSpinBox()
        self.retail_price_input.setRange(0, 999999.99)
        self.retail_price_input.setDecimals(2)
        pricing_layout.addWidget(FormField("Retail Price (₦):", self.retail_price_input, required=True))

        # Bulk pricing
        bulk_group = QGroupBox("Bulk Pricing (Optional)")
        bulk_group.setStyleSheet(Styles.group_box())
        bulk_layout = QHBoxLayout()
        self.bulk_price_input = QDoubleSpinBox()
        self.bulk_price_input.setRange(0, 999999.99)
        self.bulk_price_input.setDecimals(2)
        bulk_layout.addWidget(FormField("Price (₦):", self.bulk_price_input))

        self.bulk_quantity_input = QSpinBox()
        self.bulk_quantity_input.setRange(1, 100000)
        self.bulk_quantity_input.setValue(10)
        bulk_layout.addWidget(FormField("Min Qty:", self.bulk_quantity_input))
        bulk_group.setLayout(bulk_layout)
        pricing_layout.addWidget(bulk_group)

        # Wholesale pricing
        wholesale_group = QGroupBox("Wholesale Pricing (Optional)")
        wholesale_group.setStyleSheet(Styles.group_box())
        wholesale_layout = QHBoxLayout()
        self.wholesale_price_input = QDoubleSpinBox()
        self.wholesale_price_input.setRange(0, 999999.99)
        self.wholesale_price_input.setDecimals(2)
        wholesale_layout.addWidget(FormField("Price (₦):", self.wholesale_price_input))

        self.wholesale_quantity_input = QSpinBox()
        self.wholesale_quantity_input.setRange(1, 100000)
        self.wholesale_quantity_input.setValue(50)
        wholesale_layout.addWidget(FormField("Min Qty:", self.wholesale_quantity_input))
        wholesale_group.setLayout(wholesale_layout)
        pricing_layout.addWidget(wholesale_group)

        pricing_card.add_widget(QWidget())
        pricing_card.layout.addLayout(pricing_layout)
        form_layout.addWidget(pricing_card)

        # Stock Alerts Card
        alerts_card = Card("⚠ Stock Alerts")
        alerts_layout = QHBoxLayout()
        alerts_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        self.min_stock_input = QSpinBox()
        self.min_stock_input.setRange(0, 100000)
        self.min_stock_input.setValue(10)
        alerts_layout.addWidget(FormField("Min Stock:", self.min_stock_input))

        self.max_stock_input = QSpinBox()
        self.max_stock_input.setRange(1, 1000000)
        self.max_stock_input.setValue(500)
        alerts_layout.addWidget(FormField("Max Stock:", self.max_stock_input))

        self.reorder_level_input = QSpinBox()
        self.reorder_level_input.setRange(0, 100000)
        alerts_layout.addWidget(FormField("Reorder Level:", self.reorder_level_input))

        alerts_card.add_widget(QWidget())
        alerts_card.layout.addLayout(alerts_layout)
        form_layout.addWidget(alerts_card)

        # Store Selection Card
        store_card = Card("🏪 Store & Location")
        store_layout = QVBoxLayout()

        self.store_combo = QComboBox()
        self.store_combo.setStyleSheet(Styles.input_field())
        store_layout.addWidget(QLabel("Select Store:"))
        store_layout.addWidget(self.store_combo)

        store_card.add_widget(QWidget())
        store_card.layout.addLayout(store_layout)
        form_layout.addWidget(store_card)

        form_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        receive_btn = StyledButton("📦 Receive Stock", "success")
        receive_btn.clicked.connect(self.accept_receive)
        button_layout.addWidget(receive_btn)

        cancel_btn = StyledButton("Cancel", "danger")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Load data
        self.load_products()
        self.load_stores()

    def _on_product_changed(self) -> None:
        """Update pricing fields when product changes."""
        # Could pre-fill pricing from product defaults
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
            show_error(self, f"Failed to load products: {str(e)}")

    def load_stores(self) -> None:
        """Load stores into combo box."""
        try:
            store_service = StoreService(self.session)
            stores = store_service.get_all_stores()
            self.store_combo.clear()
            for store in stores:
                self.store_combo.addItem(store["name"], store["id"])
        except Exception as e:
            show_error(self, f"Failed to load stores: {str(e)}")

    def accept_receive(self) -> None:
        """Validate and accept stock receiving."""
        # Validation
        if not self.batch_number_input.text().strip():
            show_error(self, "Please enter a batch number")
            return

        if self.quantity_input.value() <= 0:
            show_error(self, "Quantity must be greater than 0")
            return

        if self.cost_price_input.value() < 0:
            show_error(self, "Cost price cannot be negative")
            return

        if self.retail_price_input.value() <= 0:
            show_error(self, "Retail price must be greater than 0")
            return

        if self.min_stock_input.value() > self.max_stock_input.value():
            show_error(self, "Min stock cannot exceed Max stock")
            return

        # Store result data
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


class SalesCartDialog(QDialog):
    """Modern dialog for managing sales cart with FEFO allocation."""

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.inv_service = InventoryService(session)
        self.product_service = ProductService(session)
        self.store_service = StoreService(session)
        self.cart_items = []
        self.setup_ui()

    def setup_ui(self):
        """Setup modern sales cart UI."""
        self.setWindowTitle("🛒 Sales Cart (FEFO)")
        self.setFixedSize(Dimensions.DIALOG_WIDTH, Dimensions.DIALOG_HEIGHT)

        layout = QVBoxLayout()
        layout.setContentsMargins(Dimensions.MARGIN_MEDIUM, Dimensions.MARGIN_MEDIUM,
                                Dimensions.MARGIN_MEDIUM, Dimensions.MARGIN_MEDIUM)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Title
        title = QLabel("🛒 Sales Cart Management")
        title.setFont(Fonts.TITLE)
        title.setStyleSheet(f"color: {Colors.PRIMARY}; margin-bottom: {Dimensions.SPACING_LARGE}px;")
        layout.addWidget(title)

        # Product selection card
        select_card = Card("➕ Add Product")
        select_layout = QVBoxLayout()
        select_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Product selection
        product_layout = QHBoxLayout()
        product_layout.addWidget(QLabel("Product:"))
        self.product_combo = QComboBox()
        self.product_combo.setStyleSheet(Styles.input_field())
        self._load_products()
        product_layout.addWidget(self.product_combo)
        select_layout.addLayout(product_layout)

        # Quantity and price
        qty_price_layout = QHBoxLayout()
        qty_price_layout.addWidget(QLabel("Quantity:"))
        self.qty_input = QSpinBox()
        self.qty_input.setMinimum(1)
        self.qty_input.setValue(1)
        qty_price_layout.addWidget(self.qty_input)

        qty_price_layout.addWidget(QLabel("Unit Price:"))
        self.unit_price_input = QDoubleSpinBox()
        self.unit_price_input.setMinimum(0)
        self.unit_price_input.setValue(0)
        qty_price_layout.addWidget(self.unit_price_input)

        add_btn = StyledButton("Add to Cart", "success")
        add_btn.clicked.connect(self._add_item_to_cart)
        qty_price_layout.addWidget(add_btn)
        select_layout.addLayout(qty_price_layout)

        select_card.add_widget(QWidget())
        select_card.layout.addLayout(select_layout)
        layout.addWidget(select_card)

        # Cart table card
        cart_card = Card("📋 Cart Items (FEFO Allocation)")
        self.cart_table = StyledTable(["Product", "Qty", "Unit Price", "Subtotal", "Batches (FEFO)", "Remove"])
        cart_card.add_widget(self.cart_table)
        layout.addWidget(cart_card)

        # Summary card
        summary_card = Card("💰 Cart Summary")
        summary_layout = QHBoxLayout()
        summary_layout.addStretch()

        self.total_label = QLabel("Total: ₦0.00")
        self.total_label.setFont(Fonts.SUBTITLE)
        self.total_label.setStyleSheet(f"color: {Colors.SUCCESS}; font-weight: bold;")
        summary_layout.addWidget(self.total_label)

        summary_card.add_widget(QWidget())
        summary_card.layout.addLayout(summary_layout)
        layout.addWidget(summary_card)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        clear_btn = StyledButton("🗑 Clear Cart", "danger")
        clear_btn.clicked.connect(self._clear_cart)
        button_layout.addWidget(clear_btn)

        checkout_btn = StyledButton("💳 Checkout", "primary")
        checkout_btn.clicked.connect(self._checkout)
        button_layout.addWidget(checkout_btn)

        cancel_btn = StyledButton("Cancel", "secondary")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
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
            show_error(self, f"Failed to load products: {str(e)}")

    def _add_item_to_cart(self):
        """Add product to cart using FEFO allocation."""
        try:
            product_id = self.product_combo.currentData()
            qty = self.qty_input.value()
            unit_price = self.unit_price_input.value()

            if qty <= 0:
                show_error(self, "Quantity must be > 0")
                return

            if unit_price < 0:
                show_error(self, "Unit price cannot be negative")
                return

            # Get primary store
            store = self.store_service.get_primary_store()
            if not store:
                show_error(self, "No primary store configured")
                return

            # Use FEFO allocation
            allocated_batches = self.inv_service.allocate_stock_for_sale(
                product_id=product_id,
                store_id=store["id"],
                quantity=qty,
            )

            if not allocated_batches:
                show_error(self, f"Not enough stock for product ID {product_id}")
                return

            # Add to cart
            product = self.product_service.get_product(product_id)
            cart_item = {
                "product_id": product_id,
                "product_name": product["name"],
                "quantity": qty,
                "unit_price": unit_price,
                "batches": allocated_batches,
            }
            self.cart_items.append(cart_item)

            # Refresh cart display
            self._refresh_cart_table()
            show_success(self, f"Added {qty} units to cart")

        except Exception as e:
            show_error(self, f"Failed to add item: {str(e)}")

    def _refresh_cart_table(self):
        """Refresh cart table display."""
        self.cart_table.clear_table()
        total = 0

        for i, item in enumerate(self.cart_items):
            subtotal = item["quantity"] * item["unit_price"]
            total += subtotal

            batch_info = ", ".join(
                [f"B{b['batch_id']}:{b['quantity']}" for b in item["batches"]]
            )

            remove_btn = StyledButton("Remove", "danger")
            remove_btn.clicked.connect(lambda checked, idx=i: self._remove_item(idx))

            self.cart_table.add_row([
                item["product_name"],
                str(item["quantity"]),
                f"₦{item['unit_price']:.2f}",
                f"₦{subtotal:.2f}",
                batch_info,
                ""  # Remove button will be handled separately
            ])

        # Update total
        self.total_label.setText(f"Total: ₦{total:.2f}")

    def _remove_item(self, index):
        """Remove item from cart."""
        if 0 <= index < len(self.cart_items):
            self.cart_items.pop(index)
            self._refresh_cart_table()

    def _clear_cart(self):
        """Clear all items from cart."""
        if ask_confirmation(self, "Are you sure you want to clear the entire cart?"):
            self.cart_items.clear()
            self._refresh_cart_table()

    def _checkout(self):
        """Proceed to checkout."""
        if not self.cart_items:
            show_error(self, "Add items before checkout")
            return

        # Store checkout data and accept
        self.checkout_data = self.cart_items
        self.accept()


class LoginDialog(QDialog):
    """Modern user login dialog."""

    def __init__(self, auth_service: AuthenticationService):
        super().__init__()
        self.auth_service = auth_service
        self.user_session = None
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup modern login UI."""
        self.setWindowTitle("🔐 PharmaPOS - Login")
        self.setFixedSize(Dimensions.DIALOG_WIDTH, 400)
        self.setStyleSheet(f"background-color: {Colors.LIGHT};")

        layout = QVBoxLayout()
        layout.setContentsMargins(Dimensions.MARGIN_LARGE, Dimensions.MARGIN_LARGE,
                                Dimensions.MARGIN_LARGE, Dimensions.MARGIN_LARGE)
        layout.setSpacing(Dimensions.SPACING_LARGE)

        # Logo/Title
        title = QLabel("🏥 PharmaPOS NG")
        title.setFont(Fonts.TITLE)
        title.setStyleSheet(f"color: {Colors.PRIMARY}; margin-bottom: {Dimensions.SPACING_MEDIUM}px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Pharmacy Management System")
        subtitle.setFont(Fonts.SUBTITLE)
        subtitle.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; margin-bottom: {Dimensions.SPACING_LARGE}px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # Login form card
        login_card = Card("🔐 Sign In")
        login_layout = QVBoxLayout()
        login_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Username
        self.username_combo = QComboBox()
        self.username_combo.setStyleSheet(Styles.input_field())
        login_layout.addWidget(FormField("👤 Username:", self.username_combo))

        # Password
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(Styles.input_field())
        login_layout.addWidget(FormField("🔒 Password:", self.password_input))

        # Error message
        self.error_label = QLabel()
        self.error_label.setStyleSheet(f"color: {Colors.DANGER}; font-size: 12px;")
        self.error_label.setVisible(False)
        login_layout.addWidget(self.error_label)

        login_card.add_widget(QWidget())
        login_card.layout.addLayout(login_layout)
        layout.addWidget(login_card)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        login_btn = StyledButton("🚀 Login", "primary")
        login_btn.setFixedWidth(120)
        login_btn.clicked.connect(self.login)
        button_layout.addWidget(login_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Load usernames
        self.load_usernames()

    def load_usernames(self) -> None:
        """Load available usernames."""
        try:
            from .database import users
            session = get_session()

            result = session.query(users.c.username).filter(
                users.c.is_active == True
            ).order_by(users.c.username).all()

            if result:
                usernames = [row[0] for row in result]
                self.username_combo.addItems(usernames)
            else:
                self.username_combo.addItems(["admin", "manager1", "cashier1"])
            session.close()
        except Exception:
            self.username_combo.addItems(["admin", "manager1", "cashier1"])

    def login(self) -> None:
        """Attempt login."""
        username = self.username_combo.currentText()
        password = self.password_input.text()

        if not username or not password:
            self.error_label.setText("Please select username and enter password")
            self.error_label.setVisible(True)
            return

        user_session = self.auth_service.login(username, password)
        if user_session:
            self.user_session = user_session
            self.accept()
        else:
            self.error_label.setText("Invalid username or password")
            self.error_label.setVisible(True)
