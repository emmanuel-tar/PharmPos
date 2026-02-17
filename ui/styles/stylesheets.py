"""
PharmaPOS ERP - Global Stylesheets

Centralized QSS for the new ERP design.
"""

from .theme import Theme

class Styles:
    @staticmethod
    def main_window():
        return f"""
            QMainWindow {{
                background-color: {Theme.SURFACE_MAIN};
            }}
        """

    @staticmethod
    def sidebar():
        return f"""
            QFrame#Sidebar {{
                background-color: {Theme.SURFACE_SIDEBAR};
                border: none;
                min-width: 240px;
                max-width: 240px;
            }}
            QPushButton#SidebarItem {{
                background-color: transparent;
                color: {Theme.TEXT_MUTED};
                text-align: left;
                padding: 12px 20px;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                margin: 2px 10px;
            }}
            QPushButton#SidebarItem:hover {{
                background-color: rgba(255, 255, 255, 0.05);
                color: {Theme.TEXT_INVERSE};
            }}
            QPushButton#SidebarItem[active="true"] {{
                background-color: {Theme.PRIMARY};
                color: {Theme.TEXT_INVERSE};
            }}
        """

    @staticmethod
    def header():
        return f"""
            QFrame#Header {{
                background-color: {Theme.SURFACE_HEADER};
                border-bottom: 1px solid {Theme.BORDER};
                min-height: 64px;
                max-height: 64px;
            }}
            QLabel#HeaderTitle {{
                color: {Theme.TEXT_MAIN};
                font-size: 18px;
                font-weight: bold;
            }}
        """

    @staticmethod
    def card():
        return f"""
            QFrame#Card {{
                background-color: {Theme.SURFACE_CARD};
                border: 1px solid {Theme.BORDER};
                border-radius: 12px;
            }}
        """

    @staticmethod
    def primary_button():
        return f"""
            QPushButton#PrimaryButton {{
                background-color: {Theme.PRIMARY};
                color: {Theme.TEXT_INVERSE};
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton#PrimaryButton:hover {{
                background-color: {Theme.PRIMARY_HOVER};
            }}
            QPushButton#PrimaryButton:pressed {{
                background-color: {Theme.PRIMARY};
                margin-top: 1px;
            }}
        """

    @staticmethod
    def data_table():
        return f"""
            QTableWidget {{
                background-color: {Theme.SURFACE_CARD};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                gridline-color: {Theme.BORDER_LIGHT};
                selection-background-color: {Theme.PRIMARY_LIGHT};
                selection-color: {Theme.PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {Theme.SURFACE_MAIN};
                color: {Theme.TEXT_MUTED};
                padding: 12px;
                border: none;
                border-bottom: 1px solid {Theme.BORDER};
                font-weight: bold;
                text-align: left;
            }}
            QTableWidget::item {{
                padding: 12px;
                border-bottom: 1px solid {Theme.BORDER_LIGHT};
            }}
        """
