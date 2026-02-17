"""
PharmaPOS ERP - Main Window

Primary application shell for the modern ERP.
"""

import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget
)
from PyQt5.QtCore import Qt

from .components.sidebar import Sidebar
from .components.header import Header
from .views.dashboard import DashboardView
from .views.pos import POSView
from .views.procurement import ProcurementView
from .views.product import ProductView
from .views.customers import CustomersView
from .views.reports import ReportsView
from .styles.stylesheets import Styles

from core.services import (
    InventoryService, ProductService, SalesService, 
    AnalyticsService, ReportService, StockTransferService,
    CategoryService, ProcurementService, CustomerService
)
from desktop_app.models import get_session

class MainAppWindow(QMainWindow):
    """Modern ERP shell with sidebar and dynamic content."""
    def __init__(self, auth_service=None, user_session=None):
        super().__init__()
        self.auth_service = auth_service
        self.user_session = user_session
        
        # Initialize Services
        self.session = get_session(None) # TODO: Handle db_path
        self.inventory_service = InventoryService(self.session)
        self.transfer_service = StockTransferService(self.session)
        self.product_service = ProductService(self.session)
        self.category_service = CategoryService(self.session)
        self.sales_service = SalesService(self.session)
        self.analytics_service = AnalyticsService(self.session)
        self.report_service = ReportService(self.session)
        self.procurement_service = ProcurementService(self.session)
        self.customer_service = CustomerService(self.session)

        self.setWindowTitle("PharmaPOS ERP")
        self.resize(1280, 800)
        self.setStyleSheet(Styles.main_window())

        self.setup_ui()

    def setup_ui(self):
        # Central widget and horizontal layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar
        self.sidebar = Sidebar()
        self.sidebar.nav_changed.connect(self.handle_nav_change)
        main_layout.addWidget(self.sidebar)

        # 2. Right Side Content Area
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 2a. Header
        self.header = Header()
        content_layout.addWidget(self.header)

        # 2b. View Stack
        self.view_stack = QStackedWidget()
        
        # Views
        self.dashboard_view = DashboardView(self.analytics_service)
        self.pos_view = POSView(self.sales_service, self.product_service, self.inventory_service, self.category_service, self.customer_service)
        self.procurement_view = ProcurementView(self.inventory_service, self.procurement_service, self.transfer_service, self.product_service)
        self.product_view = ProductView(self.product_service, self.category_service, self.inventory_service, self.analytics_service)
        self.customers_view = CustomersView()
        self.reports_view = ReportsView(self.report_service)
        
        self.view_stack.addWidget(self.dashboard_view)
        self.view_stack.addWidget(self.pos_view)
        self.view_stack.addWidget(self.procurement_view)
        self.view_stack.addWidget(self.product_view)
        self.view_stack.addWidget(self.customers_view)
        self.view_stack.addWidget(self.reports_view)
        
        # TODO: Add other views
        
        content_layout.addWidget(self.view_stack)
        
        main_layout.addWidget(content_container)

    def handle_nav_change(self, view_id):
        """Update header and content based on sidebar selection."""
        if view_id == "logout":
            self.close()
            return

        # Map sidebar IDs to view stack indexes
        view_map = {
            "dashboard": 0,
            "pos": 1,
            "products": 3,
            "procurement": 2,
            "customers": 4,
            "reports": 5,
            # Placeholder for others
        }

        if view_id in view_map:
            self.header.set_title(view_id.capitalize())
            self.view_stack.setCurrentIndex(view_map[view_id])
        
        print(f"Switching to view: {view_id}")

def main():
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainAppWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
