"""
PharmaPOS Main Window

This module contains the main application window class extracted from the monolithic ui.py file.
The MainWindow class handles the primary UI layout, tab management, and coordinates between
different business logic components.
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
    QFormLayout, QSplitter, QProgressBar, QHeaderView
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
from .dialogs import (
    PrinterSettingsDialog, StockReceivingDialog, SalesCartDialog, LoginDialog
)
from .purchase_order_ui import PurchaseOrderUI


class MainWindow(QMainWindow):
    """Main application window with modern UI and comprehensive pharmacy management features."""

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
        self.analytics_service = DashboardAnalytics(session)

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
            show_error(self, f"Failed to load transaction history: {str(e)}")

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
        settings_btn = StyledButton("⚙ Printer Settings", "primary")
        settings_btn.clicked.connect(self.open_printer_settings)
        top_bar.addWidget(settings_btn)

        # Show admin tab only for admin users
        if self.user_session.role.lower() == "admin":
            admin_btn = StyledButton("👤 Admin Panel", "secondary")
            admin_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(5))
            top_bar.addWidget(admin_btn)

        logout_btn = StyledButton("Logout", "danger")
        logout_btn.clicked.connect(self.logout)
        top_bar.addWidget(logout_btn)
        layout.addLayout(top_bar)

        # Back Office Toolbar
        self.setup_back_office_toolbar(layout)

        # Tab widget
        self.tabs = QTabWidget()

        # Dashboard tab
        self.tabs.addTab(self.create_dashboard_tab(), "Dashboard")

        # Sales tab
        self.tabs.addTab(self.create_sales_tab(), "Sales")

        # Stock tab
        self.tabs.addTab(self.create_stock_tab(), "Stock")

        # Products tab
        self.tabs.addTab(self.create_products_tab(), "Products")

        # Reports tab
        self.tabs.addTab(self.create_reports_tab(), "Reports")

        # Purchase Order tabs
        self.purchase_order_ui = PurchaseOrderUI(self)
        self.tabs.addTab(self.purchase_order_ui.create_purchasing_tab(), "Purchasing")
        self.tabs.addTab(self.purchase_order_ui.create_purchase_order_tab(), "Purchase Orders")
        self.tabs.addTab(self.purchase_order_ui.create_purchase_invoice_tab(), "Purchase Invoices")
        self.tabs.addTab(self.purchase_order_ui.create_suppliers_tab(), "Suppliers")
        self.tabs.addTab(self.purchase_order_ui.create_warehouse_tab(), "Warehouse")

        # Admin tab (only for admin users)
        if self.user_session.role.lower() == "admin":
            self.tabs.addTab(self.create_admin_tab(), "Admin")

        layout.addWidget(self.tabs)
        central.setLayout(layout)

    def setup_back_office_toolbar(self, parent_layout):
        """Setup toolbar for back-office functions."""
        toolbar = QHBoxLayout()
        toolbar.setSpacing(Dimensions.SPACING_MEDIUM)

        # Dashboard (Already current tab 0)

        # User Management (Admin/Manager only)
        if self.user_session.has_permission("manage_users"):
            btn_users = StyledButton("👥 Users", "primary")
            btn_users.clicked.connect(self.open_user_management)
            toolbar.addWidget(btn_users)

        # Settings (Admin only usually, checking role)
        if self.user_session.role == "admin":
            btn_settings = StyledButton("⚙ System Settings", "secondary")
            btn_settings.clicked.connect(self.open_settings)
            toolbar.addWidget(btn_settings)

        # Compliance (Pharmacist/Manager/Admin)
        if self.user_session.role in ["admin", "manager", "pharmacist"]:
            btn_compliance = StyledButton("📜 Compliance", "info")
            btn_compliance.clicked.connect(self.open_compliance)
            toolbar.addWidget(btn_compliance)

        toolbar.addStretch()
        parent_layout.addLayout(toolbar)

    def open_user_management(self):
        dialog = UserManagementDialog(self.user_session, self)
        dialog.exec_()

    def open_settings(self):
        dialog = SettingsDialog(self.user_session, self)
        dialog.exec_()

    def open_compliance(self):
        dialog = ComplianceDashboard(self.user_session, self)
        dialog.exec_()

    def create_dashboard_tab(self) -> QWidget:
        """Create comprehensive analytics dashboard with live reports."""
        widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(Dimensions.SPACING_MEDIUM)
        main_layout.setContentsMargins(Dimensions.MARGIN_MEDIUM, Dimensions.MARGIN_MEDIUM,
                                     Dimensions.MARGIN_MEDIUM, Dimensions.MARGIN_MEDIUM)

        # Scroll Area for smaller screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)

        # Title
        title = QLabel("📊 Analytics Dashboard")
        title.setFont(Fonts.TITLE)
        title.setStyleSheet(f"color: {Colors.PRIMARY}; margin-bottom: {Dimensions.SPACING_LARGE}px;")
        content_layout.addWidget(title)

        # Top Row: KPI Cards
        cards_layout = QHBoxLayout()
        self.card_sales = KPICard("Today's Sales", "₦0.00", "0 txns", Colors.SUCCESS)
        self.card_profit = KPICard("Profit (30d)", "₦0.00", "0% Margin", Colors.INFO)
        self.card_stock = KPICard("Inventory Value", "₦0.00", "0 items", Colors.WARNING)
        self.card_alerts = KPICard("Active Alerts", "0", "Critical", Colors.DANGER)

        cards_layout.addWidget(self.card_sales)
        cards_layout.addWidget(self.card_profit)
        cards_layout.addWidget(self.card_stock)
        cards_layout.addWidget(self.card_alerts)
        content_layout.addLayout(cards_layout)

        # Middle Row: Charts
        charts_layout = QHBoxLayout()
        self.chart_sales = SalesTrendChart()
        self.chart_profit = ProfitMarginWidget()

        charts_layout.addWidget(self.chart_sales, stretch=2)
        charts_layout.addWidget(self.chart_profit, stretch=1)
        content_layout.addLayout(charts_layout)

        # Bottom Row: Tables & Alerts
        bottom_layout = QHBoxLayout()

        # Top Products
        self.top_products_group = QGroupBox("🏆 Top Products (30 Days)")
        self.top_products_group.setStyleSheet(Styles.group_box())
        tp_layout = QVBoxLayout()
        self.top_products_table = StyledTable(["Product", "Qty", "Revenue"])
        tp_layout.addWidget(self.top_products_table)
        self.top_products_group.setLayout(tp_layout)

        # Alerts Widget
        self.alerts_widget = InventoryAlertWidget()

        bottom_layout.addWidget(self.top_products_group, stretch=1)
        bottom_layout.addWidget(self.alerts_widget, stretch=1)
        content_layout.addLayout(bottom_layout)

        # Refresh Button
        refresh_btn = StyledButton("🔄 Refresh Data", "primary")
        refresh_btn.clicked.connect(self.load_dashboard_data)
        content_layout.addWidget(refresh_btn, alignment=Qt.AlignRight)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        widget.setLayout(main_layout)

        return widget

    def load_dashboard_data(self):
        """Load data into dashboard widgets."""
        try:
            # Check permissions
            store_id = self.user_session.store_id
            # If admin/manager, maybe show all? kept simple to session store for now

            data = self.analytics_service.get_dashboard_summary(store_id)

            # Update KPIs
            sales = data.get('today_sales', {})
            self.card_sales.update_value(
                f"₦{sales.get('total_sales', 0):,.2f}",
                f"{sales.get('transaction_count', 0)} txns"
            )

            profit = data.get('profit_analysis', {})
            self.card_profit.update_value(
                f"₦{profit.get('gross_profit', 0):,.2f}",
                f"{profit.get('profit_margin_percent', 0)}% Margin"
            )

            inv = data.get('inventory_value', {})
            self.card_stock.update_value(
                f"₦{inv.get('total_value', 0):,.2f}",
                f"{inv.get('unique_products', 0)} SKUs"
            )

            alerts_count = len(data.get('low_stock', [])) + len(data.get('expiring_soon', []))
            self.card_alerts.update_value(str(alerts_count), "Items Attention")

            # Update Charts
            trend = data.get('sales_trend', [])
            dates = [d['date'] for d in trend]
            values = [d['total_sales'] for d in trend]
            self.chart_sales.plot_data(dates, values)

            self.chart_profit.plot_data(
                profit.get('total_revenue', 0),
                profit.get('total_cost', 0),
                profit.get('gross_profit', 0)
            )

            # Update Top Products
            products = data.get('top_products', [])
            self.top_products_table.clear_table()
            for row, p in enumerate(products):
                self.top_products_table.add_row([
                    p['product_name'],
                    str(p['quantity_sold']),
                    f"₦{p['revenue']:,.2f}"
                ])

            # Update Alerts Widget
            self.alerts_widget.update_alerts(
                data.get('low_stock', []),
                data.get('expiring_soon', [])
            )

        except Exception as e:
            show_error(self, f"Failed to load dashboard: {str(e)}")

    def create_sales_tab(self) -> QWidget:
        """Create professional POS sales screen with product grid and cart."""
        widget = QWidget()
        main_layout = QHBoxLayout()

        # ===== LEFT SIDE: Product Catalog =====
        left_layout = QVBoxLayout()
        left_layout.setSpacing(Dimensions.SPACING_MEDIUM)
        left_label = QLabel("PRODUCT CATALOG")
        left_label.setFont(Fonts.SUBTITLE)
        left_label.setStyleSheet(f"font-weight: bold; padding: {Dimensions.SPACING_MEDIUM}px;")
        left_layout.addWidget(left_label)

        # Low stock warning bar
        self.low_stock_bar = QLabel()
        self.low_stock_bar.setStyleSheet(f"background-color: {Colors.WARNING_LIGHT}; color: {Colors.WARNING_DARK}; padding: 8px; border-radius: 4px; font-size: 9px; font-weight: bold;")
        self.low_stock_bar.setVisible(False)
        left_layout.addWidget(self.low_stock_bar)

        # Search bar with larger font
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setFont(Fonts.BODY)
        search_label.setStyleSheet("font-weight: bold;")
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Scan barcode or search product...")
        self.product_search.setStyleSheet(Styles.input_field())
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
        self.product_grid_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Container for product cards
        self.products_container = QWidget()
        self.products_container_layout = QVBoxLayout(self.products_container)

        # Create product cards grid (2 columns for larger cards)
        self.products_cards_layout = QGridLayout()
        self.products_cards_layout.setSpacing(Dimensions.SPACING_MEDIUM)
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
        right_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Header
        cart_header = QLabel("SALES RECEIPT")
        cart_header.setFont(Fonts.SUBTITLE)
        cart_header.setStyleSheet(f"font-weight: bold; padding: {Dimensions.SPACING_MEDIUM}px;")
        right_layout.addWidget(cart_header)

        # Customer info (with larger font)
        customer_layout = QHBoxLayout()
        customer_label = QLabel("Customer:")
        customer_label.setFont(Fonts.BODY)
        customer_label.setStyleSheet("font-weight: bold;")
        customer_label.setMinimumWidth(80)
        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("Walk-in customer")
        self.customer_input.setStyleSheet(Styles.input_field())
        self.customer_input.setMinimumHeight(32)
        customer_layout.addWidget(customer_label)
        customer_layout.addWidget(self.customer_input)
        right_layout.addLayout(customer_layout)

        # Barcode/Item scanner (NEW FEATURE)
        scanner_layout = QHBoxLayout()
        scanner_label = QLabel("Item Scanner:")
        scanner_label.setFont(Fonts.BODY)
        scanner_label.setStyleSheet("font-weight: bold;")
        scanner_label.setMinimumWidth(80)
        self.item_scanner = QLineEdit()
        self.item_scanner.setPlaceholderText("Scan barcode here to add item...")
        self.item_scanner.setStyleSheet(f"font-size: 12px; padding: 10px; background-color: {Colors.LIGHT}; font-weight: bold; border: 2px solid {Colors.PRIMARY}; border-radius: 6px;")
        self.item_scanner.setMinimumHeight(48)
        self.item_scanner.returnPressed.connect(self.on_barcode_scanned)
        scanner_layout.addWidget(scanner_label)
        scanner_layout.addWidget(self.item_scanner)
        right_layout.addLayout(scanner_layout)
        widget.installEventFilter(self)
        self.sales_tab_widget = widget

        # Cart table (with larger fonts and row heights)
        cart_label = QLabel("CART ITEMS")
        cart_label.setFont(Fonts.BODY)
        cart_label.setStyleSheet(f"font-weight: bold; padding: {Dimensions.SPACING_MEDIUM}px 0px;")
        right_layout.addWidget(cart_label)

        self.sales_cart_table = StyledTable(["Item #", "Product", "Price (₦)", "Qty", "Disc (%)", "Total (₦)"])
        self.sales_cart_table.setColumnWidth(0, 50)
        self.sales_cart_table.setColumnWidth(1, 280)  # Product Name - wider for long names
        self.sales_cart_table.setColumnWidth(2, 80)
        self.sales_cart_table.setColumnWidth(3, 50)
        self.sales_cart_table.setColumnWidth(4, 70)
        self.sales_cart_table.setColumnWidth(5, 80)
        right_layout.addWidget(self.sales_cart_table)

        # Summary section (ENHANCED with larger fonts and better styling)
        summary_label = QLabel("TRANSACTION SUMMARY")
        summary_label.setFont(Fonts.BODY)
        summary_label.setStyleSheet(f"font-weight: bold; padding: {Dimensions.SPACING_MEDIUM}px 0px;")
        right_layout.addWidget(summary_label)

        summary_frame = QFrame()
        summary_frame.setStyleSheet(f"border: 2px solid {Colors.BORDER}; border-radius: 5px; padding: 15px; background-color: {Colors.LIGHT};")
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Subtotal
        subtotal_layout = QHBoxLayout()
        subtotal_lbl = QLabel("Subtotal:")
        subtotal_lbl.setFont(Fonts.BODY)
        subtotal_lbl.setStyleSheet("font-weight: bold;")
        subtotal_layout.addWidget(subtotal_lbl)
        subtotal_layout.addStretch()
        self.subtotal_label = QLabel("₦0.00")
        self.subtotal_label.setAlignment(Qt.AlignRight)
        self.subtotal_label.setFont(Fonts.BODY)
        self.subtotal_label.setStyleSheet(f"font-weight: bold; min-width: 100px; padding-right: {Dimensions.SPACING_MEDIUM}px;")
        subtotal_layout.addWidget(self.subtotal_label)
        summary_layout.addLayout(subtotal_layout)

        # Discount
        discount_layout = QHBoxLayout()
        discount_lbl = QLabel("Discount:")
        discount_lbl.setFont(Fonts.BODY)
        discount_lbl.setStyleSheet("font-weight: bold;")
        discount_layout.addWidget(discount_lbl)
        discount_layout.addStretch()
        self.discount_label = QLabel("₦0.00")
        self.discount_label.setAlignment(Qt.AlignRight)
        self.discount_label.setFont(Fonts.BODY)
        self.discount_label.setStyleSheet(f"font-weight: bold; min-width: 100px; padding-right: {Dimensions.SPACING_MEDIUM}px;")
        discount_layout.addWidget(self.discount_label)
        summary_layout.addLayout(discount_layout)

        # Tax
        tax_layout = QHBoxLayout()
        tax_lbl = QLabel("Tax (7.5%):")
        tax_lbl.setFont(Fonts.BODY)
        tax_lbl.setStyleSheet("font-weight: bold;")
        tax_layout.addWidget(tax_lbl)
        tax_layout.addStretch()
        self.tax_label = QLabel("₦0.00")
        self.tax_label.setAlignment(Qt.AlignRight)
        self.tax_label.setFont(Fonts.BODY)
        self.tax_label.setStyleSheet(f"font-weight: bold; min-width: 100px; padding-right: {Dimensions.SPACING_MEDIUM}px;")
        tax_layout.addWidget(self.tax_label)
        summary_layout.addLayout(tax_layout)

        # Total (PROMINENT)
        total_layout = QHBoxLayout()
        total_lbl = QLabel("TOTAL:")
        total_lbl.setFont(Fonts.SUBTITLE)
        total_lbl.setStyleSheet("font-weight: bold;")
        total_layout.addWidget(total_lbl)
        total_layout.addStretch()
        self.total_amount_label = QLabel("₦0.00")
        self.total_amount_label.setAlignment(Qt.AlignRight)
        self.total_amount_label.setFont(Fonts.TITLE)
        self.total_amount_label.setStyleSheet(f"font-weight: bold; min-width: 120px; padding: 8px 15px; background-color: {Colors.SUCCESS}; border-radius: 3px;")
        total_layout.addWidget(self.total_amount_label)
        summary_layout.addLayout(total_layout)

        right_layout.addWidget(summary_frame)

        # Payment section (PROFESSIONAL)
        payment_label = QLabel("PAYMENT")
        payment_label.setFont(Fonts.BODY)
        payment_label.setStyleSheet(f"font-weight: bold; padding: {Dimensions.SPACING_MEDIUM}px 0px;")
        right_layout.addWidget(payment_label)

        payment_layout = QVBoxLayout()
        payment_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Payment method row
        method_row = QHBoxLayout()
        method_label = QLabel("Method:")
        method_label.setFont(Fonts.BODY)
        method_label.setStyleSheet("font-weight: bold;")
        method_label.setMinimumWidth(60)
        self.sales_payment_method = QComboBox()
        self.sales_payment_method.addItems(["Cash", "Card", "Transfer", "Credit"])
        self.sales_payment_method.setStyleSheet(Styles.input_field())
        self.sales_payment_method.setMinimumHeight(32)
        method_row.addWidget(method_label)
        method_row.addWidget(self.sales_payment_method)
        method_row.addStretch()
        payment_layout.addLayout(method_row)

        # Amount paid row
        paid_row = QHBoxLayout()
        paid_label = QLabel("Amount Paid:")
        paid_label.setFont(Fonts.BODY)
        paid_label.setStyleSheet("font-weight: bold;")
        paid_label.setMinimumWidth(120)
        self.sales_amount_paid = QDoubleSpinBox()
        self.sales_amount_paid.setMinimum(0)
        self.sales_amount_paid.setMaximum(999999.99)
        self.sales_amount_paid.setDecimals(2)
        self.sales_amount_paid.setStyleSheet(Styles.input_field())
        self.sales_amount_paid.setMinimumHeight(32)
        self.sales_amount_paid.valueChanged.connect(self.update_sales_summary)
        paid_row.addWidget(paid_label)
        paid_row.addWidget(self.sales_amount_paid)
        payment_layout.addLayout(paid_row)

        # Change row
        change_row = QHBoxLayout()
        change_label = QLabel("Change:")
        change_label.setFont(Fonts.BODY)
        change_label.setStyleSheet("font-weight: bold;")
        change_label.setMinimumWidth(120)
        self.sales_change_label = QLabel("₦0.00")
        self.sales_change_label.setAlignment(Qt.AlignRight)
        self.sales_change_label.setFont(Fonts.BODY)
        self.sales_change_label.setStyleSheet(f"font-weight: bold; min-width: 100px; padding-right: {Dimensions.SPACING_MEDIUM}px;")
        change_row.addWidget(change_label)
        change_row.addStretch()
        change_row.addWidget(self.sales_change_label)
        payment_layout.addLayout(change_row)

        right_layout.addLayout(payment_layout)

        # Action buttons (LARGE AND PROMINENT)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Complete Sale button (GREEN, LARGE)
        self.complete_sale_btn = StyledButton("COMPLETE SALE", "success")
        self.complete_sale_btn.setMinimumHeight(50)
        self.complete_sale_btn.clicked.connect(self.complete_sale)
        buttons_layout.addWidget(self.complete_sale_btn)

        # Save & Print button (BLUE)
        save_print_btn = StyledButton("Save & Print", "primary")
        save_print_btn.setMinimumHeight(50)
        save_print_btn.clicked.connect(self.complete_sale)
        buttons_layout.addWidget(save_print_btn)

        # Cancel button (RED)
        clear_btn = StyledButton("Clear Cart", "danger")
        clear_btn.setMinimumHeight(50)
        clear_btn.clicked.connect(self.clear_sales_cart)
        buttons_layout.addWidget(clear_btn)

        right_layout.addLayout(buttons_layout)

        # Quick actions (Test & Reprint)
        quick_actions_layout = QHBoxLayout()
        quick_actions_layout.setSpacing(Dimensions.SPACING_MEDIUM)

        self.printer_test_btn = StyledButton("🖨 Printer Test", "info")
        self.printer_test_btn.setStyleSheet(f"font-size: 9px; padding: 6px; min-height: 30px;")
        self.printer_test_btn.clicked.connect(self.printer_test)
        quick_actions_layout.addWidget(self.printer_test_btn)

        self.reprint_last_btn = StyledButton("📄 Reprint Last", "secondary")
        self.reprint_last_btn.setStyleSheet(f"font-size: 9px; padding: 6px; min-height: 30px;")
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

    def create_stock_tab(self) -> QWidget:
        """Create stock overview tab showing all products and quantities."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(Dimensions.SPACING_MEDIUM)
        layout.setContentsMargins(Dimensions.MARGIN_MEDIUM, Dimensions.MARGIN_MEDIUM,
                                Dimensions.MARGIN_MEDIUM, Dimensions.MARGIN_MEDIUM)

        # Title and controls
        header_layout = QHBoxLayout()

        title = QLabel("📦 Stock Overview")
        title.setFont(Fonts.TITLE)
        title.setStyleSheet(f"font-weight: bold; color: {Colors.PRIMARY};")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Quick Add Stock button
        quick_add_btn = StyledButton("⚡ Quick Add Stock", "success")
        quick_add_btn.clicked.connect(self.quick_add_stock)
        header_layout.addWidget(quick_add_btn)

        # Receive Stock button
        receive_btn = StyledButton("📥 Receive Stock", "primary")
        receive_btn.clicked.connect(self.receive_stock)
        header_layout.addWidget(receive_btn)

        # Refresh button
        refresh_btn = StyledButton("🔄 Refresh", "secondary")
        refresh_btn.clicked.connect(self.load_stock_table)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Stock table
        self.stock_table = StyledTable([
            "Product Name", "SKU", "Total Stock", "Cost Price", "Retail Price", "Status"
        ])

        # Make product name column very spacious
        self.stock_table.setColumnWidth(0, 400)  # Product Name - very wide
        self.stock_table.setColumnWidth(1, 120)  # SKU
        self.stock_table.setColumnWidth(2, 100)  # Total Stock
        self.stock_table.setColumnWidth(3, 100)  # Cost Price
        self.stock_table.setColumnWidth(4, 100)  # Retail Price
        self.stock_table.setColumnWidth(5, 100)  # Status

        layout.addWidget(self.stock_table)

        widget.setLayout(layout)

        # Load stock data
        self.load_stock_table()

        return widget

    def create_products_tab(self) -> QWidget:
        """Create products management tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Product Catalog"))

        # Control buttons
        button_layout = QHBoxLayout()

        create_btn = StyledButton("+ New Product", "success")
        create_btn.clicked.connect(self.show_create_product_dialog)
        button_layout.addWidget(create_btn)

        import_btn = StyledButton("Import Products", "primary")
        import_btn.clicked.connect(self.show_import_dialog)
        button_layout.addWidget(import_btn)

        export_btn = StyledButton("Export to CSV", "secondary")
        export_btn.clicked.connect(self.export_products_csv)
        button_layout.addWidget(export_btn)

        template_btn = StyledButton("Export to JSON", "info")
        template_btn.clicked.connect(self.export_products_json)
        button_layout.addWidget(template_btn)

        refresh_btn = StyledButton("Refresh", "secondary")
        refresh_btn.clicked.connect(self.load_products_table)
        button_layout.addWidget(refresh_btn)

        layout.addLayout(button_layout)

        # Products table
        self.products_table = StyledTable([
            "ID", "Name", "SKU", "Cost Price", "Retail Price", "Bulk Price",
            "Bulk Qty", "Wholesale Price", "Wholesale Qty", "Min Stock",
            "Max Stock", "Reorder Level", "Status"
        ])
        self.products_table.setColumnWidth(1, 250)  # Product Name - wider for long names
        self.products_table.setColumnWidth(2, 120)  # SKU - wider
        layout.addWidget(self.products_table)

        # Load products on startup
        self.load_products_table()

        widget.setLayout(layout)
        return widget

    def create_reports_tab(self) -> QWidget:
        """Create reports tab with daily sales, product movement, and revenue tracking."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Title
        title = QLabel("REPORTS & ANALYTICS")
        title.setFont(Fonts.SUBTITLE)
        title.setStyleSheet(f"font-weight: bold; padding: {Dimensions.SPACING_MEDIUM}px;")
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
        daily_summary_label.setFont(Fonts.BODY)
        daily_summary_label.setStyleSheet("font-weight: bold;")
        daily_sales_summary.addWidget(daily_summary_label)

        summary_frame = QFrame()
        summary_frame.setStyleSheet(f"border: 1px solid {Colors.BORDER}; border-radius: 5px; padding: 15px;")
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
        self.daily_sales_table = StyledTable([
            "Receipt #", "Time", "Total", "Payment Method", "Items"
        ])
        daily_sales_layout.addWidget(self.daily_sales_table)

        refresh_btn = StyledButton("Refresh Daily Sales", "primary")
        refresh_btn.clicked.connect(self.load_daily_sales_report)
        daily_sales_layout.addWidget(refresh_btn)

        report_tabs.addTab(daily_sales_widget, "Daily Sales")

        # Product Movement Tab
        product_movement_widget = QWidget()
        product_movement_layout = QVBoxLayout(product_movement_widget)

        self.product_movement_table = StyledTable([
            "Product", "Opening Stock", "Stock In", "Stock Out", "Closing Stock", "Value"
        ])
        product_movement_layout.addWidget(self.product_movement_table)

        refresh_movement_btn = StyledButton("Refresh Product Movement", "primary")
        refresh_movement_btn.clicked.connect(self.load_product_movement_report)
        product_movement_layout.addWidget(refresh_movement_btn)

        report_tabs.addTab(product_movement_widget, "Product Movement")

        # Revenue Analysis Tab
        revenue_widget = QWidget()
        revenue_layout = QVBoxLayout(revenue_widget)

        self.revenue_table = StyledTable([
            "Date", "Revenue", "Cost", "Profit", "Margin %", "Transactions"
        ])
        revenue_layout.addWidget(self.revenue_table)

        refresh_revenue_btn = StyledButton("Refresh Revenue Analysis", "primary")
        refresh_revenue_btn.clicked.connect(self.load_revenue_analysis_report)
        revenue_layout.addWidget(refresh_revenue_btn)

        report_tabs.addTab(revenue_widget, "Revenue Analysis")

        layout.addWidget(report_tabs)

        # Export buttons
        export_layout = QHBoxLayout()
        export_layout.addStretch()

        export_pdf_btn = StyledButton("Export PDF", "primary")
        export_pdf_btn.clicked.connect(self.export_reports_pdf)
        export_layout.addWidget(export_pdf_btn)

        export_excel_btn = StyledButton("Export Excel", "success")
        export_excel_btn.clicked.connect(self.export_reports_excel)
        export_layout.addWidget(export_excel_btn)

        layout.addLayout(export_layout)

        widget.setLayout(layout)

        # Load initial reports
        self.load_daily_sales_report()

        return widget

    def create_admin_tab(self) -> QWidget:
        """Create admin panel with system settings and user management."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Title
        title = QLabel("ADMIN PANEL")
        title.setFont(Fonts.SUBTITLE)
        title.setStyleSheet(f"font-weight: bold; padding: {Dimensions.SPACING_MEDIUM}px;")
        layout.addWidget(title)

        # Admin functions grid
        admin_grid = QGridLayout()
        admin_grid.setSpacing(Dimensions.SPACING_MEDIUM)

        # User Management
        user_mgmt_btn = StyledButton("👥 User Management", "primary")
        user_mgmt_btn.setMinimumHeight(60)
        user_mgmt_btn.clicked.connect(self.open_user_management)
        admin_grid.addWidget(user_mgmt_btn, 0, 0)

        # System Settings
        sys_settings_btn = StyledButton("⚙ System Settings", "secondary")
        sys_settings_btn.setMinimumHeight(60)
        sys_settings_btn.clicked.connect(self.open_settings)
        admin_grid.addWidget(sys_settings_btn, 0, 1)

        # Database Backup
        backup_btn = StyledButton("💾 Database Backup", "info")
        backup_btn.setMinimumHeight(60)
        backup_btn.clicked.connect(self.backup_database)
        admin_grid.addWidget(backup_btn, 1, 0)

        # Compliance Dashboard
        compliance_btn = StyledButton("📜 Compliance", "warning")
        compliance_btn.setMinimumHeight(60)
        compliance_btn.clicked.connect(self.open_compliance)
        admin_grid.addWidget(compliance_btn, 1, 1)

        # Activity Logs
        logs_btn = StyledButton("📋 Activity Logs", "secondary")
        logs_btn.setMinimumHeight(60)
        logs_btn.clicked.connect(self.show_activity_logs)
        admin_grid.addWidget(logs_btn, 2, 0)

        # System Info
        info_btn = StyledButton("ℹ System Info", "info")
        info_btn.setMinimumHeight(60)
        info_btn.clicked.connect(self.show_system_info)
        admin_grid.addWidget(info_btn, 2, 1)

        layout.addLayout(admin_grid)

        # System status section
        status_group = QGroupBox("System Status")
        status_group.setStyleSheet(Styles.group_box())
        status_layout = QVBoxLayout(status_group)

        self.system_status_table = StyledTable([
            "Component", "Status", "Last Check", "Details"
        ])
        status_layout.addWidget(self.system_status_table)

        refresh_status_btn = StyledButton("Refresh Status", "primary")
        refresh_status_btn.clicked.connect(self.load_system_status)
        status_layout.addWidget(refresh_status_btn)

        layout.addWidget(status_group)

        widget.setLayout(layout)

        # Load system status
        self.load_system_status()

        return widget

    # ===== SALES TAB METHODS =====

    def load_sales_products(self):
        """Load products for sales tab."""
        try:
            products = self.product_service.get_all_products()
            self.display_products(products)
        except Exception as e:
            show_error(self, f"Failed to load products: {str(e)}")

    def display_products(self, products):
        """Display products in grid layout."""
        # Clear existing products
        for i in reversed(range(self.products_cards_layout.count())):
            self.products_cards_layout.itemAt(i).widget().setParent(None)

        row = 0
        col = 0
        max_cols = 2

        for product in products:
            card = self.create_product_card(product)
            self.products_cards_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def create_product_card(self, product: dict) -> QWidget:
        """Create a clickable product card for the sales grid."""
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: {Colors.LIGHT};
                border: 2px solid {Colors.LIGHT_MEDIUM};
                border-radius: 8px;
                padding: 15px;
            }}
            QWidget:hover {{
                background-color: {Colors.LIGHT};
                border: 2px solid {Colors.PRIMARY};
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
        """)
        card.setCursor(Qt.PointingHandCursor)
        card.setMinimumHeight(220)
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        # Product image placeholder
        image_label = QLabel()
        image_label.setMinimumHeight(120)
        image_label.setStyleSheet(f"background-color: {Colors.LIGHT_MEDIUM}; border-radius: 5px; font-size: 9px;")
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
                show_error(self, f"{product['name']} is out of stock")
                return

            # Check if product already in cart
            for row in range(self.sales_cart_table.rowCount()):
                name_item = self.sales_cart_table.item(row, 1)
                if name_item and name_item.text() == product['name']:
                    # Check if incrementing would exceed available stock
                    qty_item = self.sales_cart_table.item(row, 3)
                    current_qty = int(qty_item.text())
                    if current_qty + 1 > available_stock:
                        show_error(self, f"Only {available_stock} unit(s) available for {product['name']}")
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
            delete_btn = StyledButton("Delete", "danger")
            delete_btn.setMaximumWidth(80)
            delete_btn.clicked.connect(lambda _, r=row: self.remove_from_cart(r))
            self.sales_cart_table.setCellWidget(row, 6, delete_btn)
            # Set row height for better visibility
            self.sales_cart_table.setRowHeight(row, 48)
            self.update_sales_summary()
        except Exception as e:
            show_error(self, f"Failed to add product: {str(e)}")

    def remove_from_cart(self, row: int) -> None:
        """Remove item from sales cart."""
        self.sales_cart_table.removeRow(row)
        self.update_sales_summary()

    def clear_sales_cart(self) -> None:
        """Clear all items from the sales cart."""
        if self.sales_cart_table.rowCount() > 0:
            if ask_confirmation(self, "Are you sure you want to clear the entire cart?"):
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

        # Calculate tax and total
        tax = subtotal * 0.075  # 7.5% VAT
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
            self.sales_change_label.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {Colors.INFO}; min-width: 100px; padding-right: 10px;")
            self.sales_change_label.setText(f"₦{change:.2f}")
        else:
            self.sales_change_label.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {Colors.DANGER}; min-width: 100px; padding-right: 10px;")
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
            for i in reversed(range(self.products_cards_layout.count())):
                self.products_cards_layout.itemAt(i).widget().setParent(None)

            row = 0
            col = 0
            max_cols = 2
            for product in filtered:
                card = self.create_product_card(product)
                self.products_cards_layout.addWidget(card, row, col)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
        except Exception as e:
            show_error(self, f"Search failed: {str(e)}")

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
                show_error(self, f"No product found with barcode/SKU: {barcode_or_sku}")
                self.item_scanner.clear()
                return
            # Auto-add to cart (no popup)
            self.add_product_to_sales_cart(product)
            # Clear scanner field for next scan
            self.item_scanner.clear()
            self.item_scanner.setFocus()
        except Exception as e:
            show_error(self, f"Failed to process barcode: {str(e)}")
            self.item_scanner.clear()

    def complete_sale(self) -> None:
        """Complete sale transaction with payment."""
        try:
            # Check if cart has items
            if self.sales_cart_table.rowCount() == 0:
                show_error(self, "Add items to cart first")
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
                show_error(self, "Add items to cart first")
                return

            # Calculate tax and total
            tax = subtotal * 0.075  # 7.5% VAT
            total_amount = subtotal + tax

            if amount_paid < total_amount:
                show_error(self, f"Insufficient Payment\nSubtotal: ₦{subtotal:.2f}\nTax (7.5%): ₦{tax:.2f}\nTotal: ₦{total_amount:.2f}\nPaid: ₦{amount_paid:.2f}\nShortfall: ₦{total_amount - amount_paid:.2f}")
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
                    show_error(self, f"Not enough stock for {cart_item['product_name']}\nNeeded: {cart_item['quantity']}\nAvailable: {sum(b['available_quantity'] for b in batches)}")
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
                user_id=self.user_session.user_id,
                store_id=store["id"],
                items=allocated_items,
                payment_method=payment_method,
                amount_paid=Decimal(str(amount_paid)),
            )

            change = amount_paid - total_amount
            show_success(self, f"Sale Completed\nReceipt #: {sale_result['receipt_number']}\nSubtotal: ₦{subtotal:.2f}\nTax (7.5%): ₦{tax:.2f}\nTotal: ₦{total_amount:.2f}\nAmount Paid: ₦{amount_paid:.2f}\nChange: ₦{change:.2f}")

            # Print receipt to thermal printer
            self.print_thermal_receipt(
                receipt_number=str(sale_result['receipt_number']),
                items=cart_items,
                subtotal=subtotal,
                tax=tax,
                total=total_amount,
                payment_method=payment_method,
                amount_paid=amount_paid,
                change=change,
            )

            # Clear cart and reset UI
            self.sales_cart_table.setRowCount(0)
            self.customer_input.clear()
            self.sales_amount_paid.setValue(0)
            self.sales_payment_method.setCurrentIndex(0)
            self.update_sales_summary()

        except Exception as e:
            show_error(self, f"Failed to complete sale: {str(e)}")

    def print_thermal_receipt(self, receipt_number: str, items: list, subtotal: float, tax: float, total: float,
                              payment_method: str, amount_paid: float, change: float) -> None:
        """Format and send the receipt to thermal printer using configured settings or file fallback."""
        try:
            from .thermal_printer import ThermalPrinter, format_receipt
            from .config import get_printer_device_info

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
                show_message(self, 'Printer', 'Receipt sent to thermal printer.')
            else:
                path = result.get('path')
                show_message(self, 'Receipt Saved', f'Receipt saved to: {path}')

        except Exception as e:
            show_error(self, f'Failed to print receipt: {e}')

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

                show_success(self, f"Stock received successfully!\n\nBatch ID: {batch['id']}\nQuantity: {data['quantity']} units\nExpiry Date: {data['expiry_date']}\nCost Price: ₦{data['cost_price']}\nRetail Price: ₦{batch.get('retail_price', 'N/A')}\nStock Alerts: Min={data.get('min_stock', 0)}, Max={data.get('max_stock', 9999)}\nStore: {data['store_id']}")

                # Refresh inventory table
                self.refresh_inventory_table()

        except Exception as e:
            show_error(self, f"Failed to receive stock: {str(e)}")

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
            show_error(self, f"Failed to refresh inventory: {str(e)}")

    def printer_test(self) -> None:
        """Send a small test print using the configured thermal printer."""
        try:
            from datetime import datetime

            config = load_printer_config()
            if not config.get('enabled', False):
                show_message(self, 'Printer Test', 'Printer is disabled. Saving to file (fallback).')
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
            if res.get("status") == "printed":
                show_success(self, "Test printed to device successfully!")
            else:
                path = res.get("path")
                show_message(self, 'Printer Test', f'Test saved to file: {path}\n\n(Printer may be disabled or unavailable.)')
        except Exception as e:
            show_error(self, f'Printer test failed: {e}')

    def reprint_last_receipt(self) -> None:
        """Re-generate and print (or save) the most recent sale receipt using configured printer."""
        try:
            # Local imports to avoid top-level dependencies
            from .database import sales as sales_table, sale_items as sale_items_table, product_batches, products
            from .config import get_printer_device_info
            from sqlalchemy import select
            from .thermal_printer import ThermalPrinter, format_receipt

            session = get_session()
            # Fetch most recent sale
            stmt = select(sales_table).order_by(sales_table.c.created_at.desc())
            row = session.execute(stmt).fetchone()
            if not row:
                show_message(self, 'Reprint', 'No sales found to reprint.')
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
            if res.get("status") == "printed":
                show_message(self, 'Reprint', 'Receipt sent to printer.')
            else:
                show_message(self, 'Reprint', f'Receipt saved to: {res.get("path")}')

        except Exception as e:
            show_error(self, f'Failed to reprint receipt: {e}')

    def expire_batches_action(self) -> None:
        """UI action to expire batches within given days for selected store."""
        try:
            days = int(self.expiry_days_input.value())
            store_text = self.expiry_store_input.text().strip()
            if store_text:
                try:
                    store_id = int(store_text)
                except ValueError:
                    show_error(self, "Input Error", "Store ID must be an integer")
                    return
            else:
                store = self.store_service.get_primary_store()
                if not store:
                    show_error(self, "Store Error", "No primary store configured")
                    return
                store_id = store["id"]

            inv_service = InventoryService(self.session)
            # Use current user id if available, otherwise 0
            user_id = getattr(self.user_session, "user_id", 0)
            expired_count = inv_service.expire_batches_within_days(store_id, days, user_id)
            show_message(self, "Expiry Result", f"Expired {expired_count} batches")
            inv_service.session.close()
        except Exception as e:
            show_error(self, f"Failed to expire batches: {str(e)}")

    def generate_report(self) -> None:
        """Generate selected report."""
        report_type = self.report_type.currentText()
        show_message(self, "Report", f"Generated {report_type} report (demo)")

    def open_printer_settings(self) -> None:
        """Open printer settings dialog."""
        dialog = PrinterSettingsDialog(self)
        dialog.exec_()

    def logout(self) -> None:
        """Logout user."""
        self.auth_service.logout(self.user_session.session_id)
        self.close()

    # ===== STOCK TAB METHODS =====

    def quick_add_stock(self) -> None:
        """Quick add stock functionality."""
        show_message(self, "Quick Add Stock", "Quick add stock dialog would open here.")

    def load_stock_table(self) -> None:
        """Load stock data into table."""
        try:
            # Mock data for now
            stock_data = [
                ["Paracetamol 500mg", "PARA500", 150, 25.50, 35.00, "Good"],
                ["Amoxicillin 250mg", "AMOX250", 75, 45.00, 60.00, "Low"],
                ["Ibuprofen 200mg", "IBU200", 200, 15.00, 22.00, "Good"],
            ]

            self.stock_table.setRowCount(len(stock_data))
            for i, item in enumerate(stock_data):
                for j, value in enumerate(item):
                    table_item = QTableWidgetItem(str(value))
                    if j == 5 and value == "Low":  # Highlight low stock
                        table_item.setBackground(Qt.yellow)
                        table_item.setForeground(Qt.black)
                    self.stock_table.setItem(i, j, table_item)
        except Exception as e:
            show_error(self, f"Failed to load stock data: {str(e)}")

    # ===== PRODUCTS TAB METHODS =====

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
        bulk_group = QGroupBox("Bulk Pricing (Optional)")
        bulk_group.setStyleSheet(Styles.group_box())
        bulk_layout = QHBoxLayout()
        bulk_price_input = QDoubleSpinBox()
        bulk_price_input.setMinimum(0)
        bulk_price_input.setMaximum(999999.99)
        bulk_price_input.setDecimals(2)
        bulk_layout.addWidget(QLabel("Price (₦):"))
        bulk_layout.addWidget(bulk_price_input)

        bulk_quantity_input = QSpinBox()
        bulk_quantity_input.setMinimum(1)
        bulk_quantity_input.setMaximum(100000)
        bulk_quantity_input.setValue(10)
        bulk_layout.addWidget(QLabel("Min Qty:"))
        bulk_layout.addWidget(bulk_quantity_input)
        bulk_group.setLayout(bulk_layout)
        layout.addWidget(bulk_group)

        # Wholesale Price Section
        wholesale_group = QGroupBox("Wholesale Pricing (Optional)")
        wholesale_group.setStyleSheet(Styles.group_box())
        wholesale_layout = QHBoxLayout()
        wholesale_price_input = QDoubleSpinBox()
        wholesale_price_input.setMinimum(0)
        wholesale_price_input.setMaximum(999999.99)
        wholesale_price_input.setDecimals(2)
        wholesale_layout.addWidget(QLabel("Price (₦):"))
        wholesale_layout.addWidget(wholesale_price_input)

        wholesale_quantity_input = QSpinBox()
        wholesale_quantity_input.setMinimum(1)
        wholesale_quantity_input.setMaximum(100000)
        wholesale_quantity_input.setValue(50)
        wholesale_layout.addWidget(QLabel("Min Qty:"))
        wholesale_layout.addWidget(wholesale_quantity_input)
        wholesale_group.setLayout(wholesale_layout)
        layout.addWidget(wholesale_group)

        layout.addSpacing(10)

        # ===== SECTION 4: Stock Alerts =====
        layout.addWidget(QLabel("<b>Stock Alerts</b>"))
        layout.addWidget(self._create_separator())

        alert_layout = QHBoxLayout()
        min_stock_input = QSpinBox()
        min_stock_input.setMinimum(0)
        min_stock_input.setMaximum(100000)
        min_stock_input.setValue(10)
        alert_layout.addWidget(QLabel("Min Stock:"))
        alert_layout.addWidget(min_stock_input)

        max_stock_input = QSpinBox()
        max_stock_input.setMinimum(1)
        max_stock_input.setMaximum(1000000)
        max_stock_input.setValue(500)
        alert_layout.addWidget(QLabel("Max Stock:"))
        alert_layout.addWidget(max_stock_input)

        reorder_input = QSpinBox()
        reorder_input.setMinimum(0)
        reorder_input.setMaximum(100000)
        alert_layout.addWidget(QLabel("Reorder Level:"))
        alert_layout.addWidget(reorder_input)
        layout.addLayout(alert_layout)

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
                    show_error(dialog, "Product name is required")
                    return
                if not sku_input.text().strip():
                    show_error(dialog, "SKU is required")
                    return
                if not nafdac_input.text().strip():
                    show_error(dialog, "NAFDAC number is required")
                    return
                if min_stock_input.value() > max_stock_input.value():
                    show_error(dialog, "Min stock cannot exceed max stock")
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
                    bulk_quantity=bulk_quantity_input.value() if bulk_price_input.value() > 0 else None,
                    wholesale_price=Decimal(str(wholesale_price_input.value())) if wholesale_price_input.value() > 0 else None,
                    wholesale_quantity=wholesale_quantity_input.value() if wholesale_price_input.value() > 0 else None,
                    min_stock=min_stock_input.value(),
                    max_stock=max_stock_input.value(),
                    reorder_level=reorder_input.value() if reorder_input.value() > 0 else None,
                )
                show_success(dialog, f"Product created: {product['name']}\n\nRetail: ₦{product['retail_price']}\nBulk: ₦{product['bulk_price']}\nWholesale: ₦{product['wholesale_price']}\nStock Alerts: {product['min_stock']}-{product['max_stock']}")
                self.load_products_table()
                dialog.accept()
            except Exception as e:
                show_error(dialog, f"Failed to create product: {str(e)}")

        create_btn = StyledButton("Create Product", "success")
        create_btn.clicked.connect(create_product)
        button_layout.addWidget(create_btn)

        cancel_btn = StyledButton("Cancel", "danger")
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
