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

        for product
