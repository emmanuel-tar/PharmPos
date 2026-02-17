"""
PharmaPOS ERP - Header Component

Top header bar for global search and user profile.
"""

from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from ..styles.theme import Theme
from ..styles.stylesheets import Styles

class Header(QFrame):
    """Top header bar component."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Header")
        self.setStyleSheet(Styles.header())
        self.setup_ui()

    def set_title(self, title):
        self.title_label.setText(title)

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(20)

        # Title
        self.title_label = QLabel("Dashboard")
        self.title_label.setObjectName("HeaderTitle")
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Global Search
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Global Search (Ctrl+K)...")
        self.search_bar.setFixedWidth(300)
        self.search_bar.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Theme.SURFACE_MAIN};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                color: {Theme.TEXT_MAIN};
            }}
            QLineEdit:focus {{
                border-color: {Theme.PRIMARY};
                background-color: {Theme.SURFACE_CARD};
            }}
        """)
        layout.addWidget(self.search_bar)

        # Notification & Profile placeholders
        notif_btn = QPushButton("🔔")
        notif_btn.setFlat(True)
        notif_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(notif_btn)

        profile_btn = QPushButton("U")
        profile_btn.setFixedSize(32, 32)
        profile_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY_LIGHT};
                color: {Theme.PRIMARY};
                border-radius: 16px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(profile_btn)

        user_name = QLabel("John Doe")
        user_name.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-weight: 500;")
        layout.addWidget(user_name)
