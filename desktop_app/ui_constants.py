"""
PharmaPOS UI Constants and Styling

This module contains all UI-related constants, colors, fonts, and styling
to ensure consistency across the application.
"""

from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt

# Color Scheme
class Colors:
    """Application color palette."""
    PRIMARY = "#2c3e50"      # Dark blue-gray
    PRIMARY_LIGHT = "#34495e"
    PRIMARY_DARK = "#1a252f"

    SECONDARY = "#3498db"    # Blue
    SECONDARY_LIGHT = "#5dade2"
    SECONDARY_DARK = "#2980b9"

    SUCCESS = "#27ae60"      # Green
    SUCCESS_LIGHT = "#58d68d"
    SUCCESS_DARK = "#1e8449"

    WARNING = "#f39c12"      # Orange
    WARNING_LIGHT = "#f7dc6f"
    WARNING_DARK = "#d68910"

    DANGER = "#e74c3c"       # Red
    DANGER_LIGHT = "#ec7063"
    DANGER_DARK = "#cb4335"

    INFO = "#17a2b8"         # Teal
    INFO_LIGHT = "#48c9b0"
    INFO_DARK = "#117a65"

    LIGHT = "#ecf0f1"        # Light gray
    LIGHT_MEDIUM = "#bdc3c7"
    DARK = "#2c3e50"         # Dark gray
    DARK_LIGHT = "#34495e"

    WHITE = "#ffffff"
    BLACK = "#000000"

# Fonts
class Fonts:
    """Application font definitions."""
    TITLE = QFont("Segoe UI", 18, QFont.Bold)
    SUBTITLE = QFont("Segoe UI", 14, QFont.Bold)
    BODY = QFont("Segoe UI", 10)
    BODY_BOLD = QFont("Segoe UI", 10, QFont.Bold)
    SMALL = QFont("Segoe UI", 9)
    SMALL_BOLD = QFont("Segoe UI", 9, QFont.Bold)
    MONOSPACE = QFont("Consolas", 10)

# Dimensions
class Dimensions:
    """Standard UI dimensions."""
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 700
    DIALOG_WIDTH = 600
    DIALOG_HEIGHT = 500
    BUTTON_HEIGHT = 35
    INPUT_HEIGHT = 32
    ICON_SIZE = 24
    SPACING_SMALL = 5
    SPACING_MEDIUM = 10
    SPACING_LARGE = 15
    MARGIN_SMALL = 10
    MARGIN_MEDIUM = 20
    MARGIN_LARGE = 30

# Stylesheets
class Styles:
    """Predefined stylesheets for consistent UI."""

    @staticmethod
    def button_primary():
        return f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: {Colors.WHITE};
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_LIGHT};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRIMARY_DARK};
            }}
        """

    @staticmethod
    def button_success():
        return f"""
            QPushButton {{
                background-color: {Colors.SUCCESS};
                color: {Colors.WHITE};
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {Colors.SUCCESS_LIGHT};
            }}
            QPushButton:pressed {{
                background-color: {Colors.SUCCESS_DARK};
            }}
        """

    @staticmethod
    def button_danger():
        return f"""
            QPushButton {{
                background-color: {Colors.DANGER};
                color: {Colors.WHITE};
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {Colors.DANGER_LIGHT};
            }}
            QPushButton:pressed {{
                background-color: {Colors.DANGER_DARK};
            }}
        """

    @staticmethod
    def input_field():
        return f"""
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                border: 1px solid {Colors.LIGHT_MEDIUM};
                border-radius: 4px;
                padding: 6px;
                font-size: 10px;
                background-color: {Colors.WHITE};
            }}
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
                border-color: {Colors.SECONDARY};
                outline: none;
            }}
        """

    @staticmethod
    def card():
        return f"""
            QFrame {{
                background-color: {Colors.WHITE};
                border: 1px solid {Colors.LIGHT_MEDIUM};
                border-radius: 8px;
                padding: 15px;
            }}
        """

    @staticmethod
    def table():
        return f"""
            QTableWidget {{
                border: 1px solid {Colors.LIGHT_MEDIUM};
                border-radius: 5px;
                background-color: {Colors.WHITE};
                gridline-color: {Colors.LIGHT_MEDIUM};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {Colors.LIGHT};
            }}
            QHeaderView::section {{
                background-color: {Colors.PRIMARY};
                color: {Colors.WHITE};
                font-weight: bold;
                padding: 10px;
                border: none;
            }}
        """

    @staticmethod
    def tab_widget():
        return f"""
            QTabWidget::pane {{
                border: 1px solid {Colors.LIGHT_MEDIUM};
                border-radius: 5px;
                background-color: {Colors.WHITE};
            }}
            QTabBar::tab {{
                background-color: {Colors.LIGHT};
                color: {Colors.DARK};
                padding: 10px 20px;
                margin-right: 2px;
                border-radius: 5px 5px 0 0;
            }}
            QTabBar::tab:selected {{
                background-color: {Colors.PRIMARY};
                color: {Colors.WHITE};
            }}
            QTabBar::tab:hover {{
                background-color: {Colors.LIGHT_MEDIUM};
            }}
        """

    @staticmethod
    def group_box():
        return f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {Colors.LIGHT_MEDIUM};
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: {Colors.PRIMARY};
            }}
        """

# Keyboard Shortcuts
class Shortcuts:
    """Application keyboard shortcuts."""
    COMPLETE_SALE = "Ctrl+S"
    CLEAR_CART = "Ctrl+C"
    FOCUS_SEARCH = "Ctrl+F"
    FOCUS_SCANNER = "Ctrl+L"
    TRANSACTION_HISTORY = "Ctrl+H"
    SAVE = "Ctrl+S"
    NEW_ITEM = "Ctrl+N"
    DELETE_ITEM = "Delete"

# Messages
class Messages:
    """Standard user messages."""
    CONFIRM_LOGOUT = "Are you sure you want to logout?"
    CONFIRM_DELETE = "Are you sure you want to delete this item?"
    CONFIRM_CLEAR_CART = "Are you sure you want to clear the entire cart?"
    SAVE_SUCCESS = "Data saved successfully."
    SAVE_ERROR = "Failed to save data."
    LOAD_ERROR = "Failed to load data."
    NETWORK_ERROR = "Network connection error."
    INVALID_INPUT = "Please check your input and try again."
    NO_SELECTION = "Please select an item first."
    INSUFFICIENT_STOCK = "Insufficient stock for the selected item."
    PAYMENT_REQUIRED = "Please enter payment amount."
    INVALID_PAYMENT = "Invalid payment amount."

# Icons (placeholder paths - update with actual icon files)
class Icons:
    """Icon paths for UI elements."""
    ADD = ":/icons/add.png"
    EDIT = ":/icons/edit.png"
    DELETE = ":/icons/delete.png"
    SAVE = ":/icons/save.png"
    CANCEL = ":/icons/cancel.png"
    SEARCH = ":/icons/search.png"
    REFRESH = ":/icons/refresh.png"
    SETTINGS = ":/icons/settings.png"
    USER = ":/icons/user.png"
    CART = ":/icons/cart.png"
    PRODUCT = ":/icons/product.png"
    REPORT = ":/icons/report.png"
    PRINTER = ":/icons/printer.png"
    LOGOUT = ":/icons/logout.png"
