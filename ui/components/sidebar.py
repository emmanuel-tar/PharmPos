"""
PharmaPOS ERP - Sidebar Component

Navigation sidebar for the ERP application.
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

from ..styles.theme import Theme
from ..styles.stylesheets import Styles

class SidebarItem(QPushButton):
    """Custom button for sidebar navigation."""
    def __init__(self, text, icon_name=None, parent=None):
        super().__init__(text, parent)
        self.setObjectName("SidebarItem")
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setFixedHeight(48)
        if icon_name:
            # Placeholder for icon logic
            pass

class Sidebar(QFrame):
    """Main navigation sidebar."""
    nav_changed = pyqtSignal(str)  # Emits the name of the selected view

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setStyleSheet(Styles.sidebar())
        self.items = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(4)

        # Brand / Logo
        brand_label = QLabel("PHARMAPOS")
        brand_label.setStyleSheet(f"""
            color: {Theme.TEXT_INVERSE};
            font-size: 20px;
            font-weight: 800;
            margin: 0 20px 30px 20px;
            letter-spacing: 1px;
        """)
        layout.addWidget(brand_label)

        # Navigation Items
        self.add_nav_item("Dashboard", "dashboard")
        self.add_nav_item("POS", "pos")
        self.add_nav_item("Products", "products")
        self.add_nav_item("Inventory", "inventory")
        self.add_nav_item("Stock Transfers", "transfers")
        self.add_nav_item("Customers", "customers")
        self.add_nav_item("Reports", "reports")
        
        layout.addStretch()

        # Bottom Items
        self.add_nav_item("Settings", "settings")
        self.add_nav_item("Logout", "logout")

    def add_nav_item(self, text, view_id):
        item = SidebarItem(text)
        item.clicked.connect(lambda: self.on_item_clicked(view_id))
        self.layout().addWidget(item)
        self.items[view_id] = item

    def on_item_clicked(self, view_id):
        # Handle logout separately
        if view_id == "logout":
            self.nav_changed.emit("logout")
            return

        # Uncheck all other items
        for vid, item in self.items.items():
            item.setProperty("active", "false")
            item.setChecked(vid == view_id)
            if vid == view_id:
                item.setProperty("active", "true")
            item.style().unpolish(item)
            item.style().polish(item)
        
        self.nav_changed.emit(view_id)

    def set_active_item(self, view_id):
        if view_id in self.items:
            self.on_item_clicked(view_id)
