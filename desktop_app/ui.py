"""
PharmaPOS NG - Desktop Application (PyQt5)

Main entry point for the pharmacy billing and inventory desktop application.
"""

import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
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
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon, QFont

from desktop_app.auth import AuthenticationService, UserSession
from desktop_app.models import (
    StoreService,
    UserService,
    ProductService,
    InventoryService,
    get_session,
)
from desktop_app.sales import SalesTransaction
from desktop_app.inventory import BatchManager, InventoryAlerts
from desktop_app.reports import SalesReporter, InventoryReporter


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
        """Create sales transaction tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Process Sale"))

        # Cart table
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(4)
        self.cart_table.setHorizontalHeaderLabels(["Batch ID", "Product ID", "Quantity", "Unit Price"])
        layout.addWidget(self.cart_table)

        # Add item section
        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel("Batch ID:"))
        self.batch_id_input = QLineEdit()
        add_layout.addWidget(self.batch_id_input)

        add_layout.addWidget(QLabel("Quantity:"))
        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(1)
        add_layout.addWidget(self.quantity_input)

        add_btn = QPushButton("Add to Cart")
        add_btn.clicked.connect(self.add_to_cart)
        add_layout.addWidget(add_btn)
        layout.addLayout(add_layout)

        # Payment section
        payment_layout = QHBoxLayout()
        payment_layout.addWidget(QLabel("Payment Method:"))
        self.payment_method = QComboBox()
        self.payment_method.addItems(["cash", "card", "transfer"])
        payment_layout.addWidget(self.payment_method)

        payment_layout.addWidget(QLabel("Amount Paid:"))
        self.amount_paid_input = QDoubleSpinBox()
        self.amount_paid_input.setMinimum(0)
        payment_layout.addWidget(self.amount_paid_input)

        complete_btn = QPushButton("Complete Sale")
        complete_btn.clicked.connect(self.complete_sale)
        payment_layout.addWidget(complete_btn)
        layout.addLayout(payment_layout)

        self.sales_status = QLabel()
        layout.addWidget(self.sales_status)

        widget.setLayout(layout)
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

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(6)
        self.products_table.setHorizontalHeaderLabels(
            ["ID", "Name", "SKU", "Cost Price", "Selling Price", "Status"]
        )
        layout.addWidget(self.products_table)

        widget.setLayout(layout)
        return widget

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

    def add_to_cart(self) -> None:
        """Add item to sales cart."""
        QMessageBox.information(self, "Cart", "Item added to cart (demo)")

    def complete_sale(self) -> None:
        """Complete sale transaction."""
        QMessageBox.information(self, "Sale", "Sale completed (demo)")

    def receive_stock(self) -> None:
        """Receive stock into inventory."""
        QMessageBox.information(self, "Stock", "Stock received (demo)")

    def generate_report(self) -> None:
        """Generate selected report."""
        report_type = self.report_type.currentText()
        QMessageBox.information(self, "Report", f"Generated {report_type} report (demo)")

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
