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
from desktop_app.product_manager import ProductImportExporter


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
        self.products_table.setColumnCount(7)
        self.products_table.setHorizontalHeaderLabels(
            ["ID", "Name", "SKU", "Generic Name", "Cost Price", "Selling Price", "Status"]
        )
        self.products_table.setColumnWidth(1, 150)
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
                self.products_table.setItem(i, 3, QTableWidgetItem(product.get("generic_name", "")))
                self.products_table.setItem(i, 4, QTableWidgetItem(f"₦{product['cost_price']}"))
                self.products_table.setItem(i, 5, QTableWidgetItem(f"₦{product['selling_price']}"))
                status = "Active" if product.get("is_active") else "Inactive"
                self.products_table.setItem(i, 6, QTableWidgetItem(status))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products: {str(e)}")

    def show_create_product_dialog(self) -> None:
        """Show dialog to create a new product."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Product")
        dialog.setGeometry(200, 200, 500, 400)

        layout = QVBoxLayout()

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

        # Cost Price
        layout.addWidget(QLabel("Cost Price:"))
        cost_input = QDoubleSpinBox()
        cost_input.setMinimum(0)
        cost_input.setMaximum(999999.99)
        cost_input.setDecimals(2)
        layout.addWidget(cost_input)

        # Selling Price
        layout.addWidget(QLabel("Selling Price:"))
        selling_input = QDoubleSpinBox()
        selling_input.setMinimum(0)
        selling_input.setMaximum(999999.99)
        selling_input.setDecimals(2)
        layout.addWidget(selling_input)

        # Description
        layout.addWidget(QLabel("Description (Optional):"))
        description_input = QTextEdit()
        description_input.setMaximumHeight(80)
        layout.addWidget(description_input)

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

                product = self.product_service.create_product(
                    name=name_input.text().strip(),
                    sku=sku_input.text().strip(),
                    cost_price=Decimal(str(cost_input.value())),
                    selling_price=Decimal(str(selling_input.value())),
                    nafdac_number=nafdac_input.text().strip(),
                    generic_name=generic_input.text().strip(),
                    barcode=barcode_input.text().strip(),
                    description=description_input.toPlainText().strip(),
                )
                QMessageBox.information(dialog, "Success", f"Product created: {product['name']}")
                self.load_products_table()
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to create product: {str(e)}")

        create_btn = QPushButton("Create")
        create_btn.clicked.connect(create_product)
        button_layout.addWidget(create_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        dialog.setLayout(layout)
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

    def add_to_cart(self) -> None:
        """Add item to sales cart."""
        QMessageBox.information(self, "Cart", "Item added to cart (demo)")

    def complete_sale(self) -> None:
        """Complete sale transaction."""
        QMessageBox.information(self, "Sale", "Sale completed (demo)")

    def receive_stock(self) -> None:
        """Receive stock into inventory."""
        QMessageBox.information(self, "Stock", "Stock received (demo)")

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
