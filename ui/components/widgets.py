"""
PharmaPOS ERP - Reusable Widgets

Modern, premium UI components for the ERP interface.
Includes shadow effects to replace problematic CSS box-shadow.
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QGraphicsDropShadowEffect, QWidget, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from ..styles.theme import Theme

class ERPCard(QFrame):
    """Modern card component with a real shadow effect."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        # Base styling is in stylesheets.py, but we add shadow here
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(4)
        self.shadow.setColor(QColor(0, 0, 0, 40)) # 15% opacity black
        self.setGraphicsEffect(self.shadow)
        
        # Don't create layout here; let subclasses or users create it to avoid QLayout warnings
        self.content_layout = None

    def set_layout(self, layout):
        """Helper to set layout and margins once."""
        layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(layout)
        self.content_layout = layout
        return layout

class MetricCard(ERPCard):
    """Specialized card for displaying key metrics/KPIs."""
    def __init__(self, title, value, subtext="", status_color=None, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(200)
        self.set_layout(QVBoxLayout())
        
        # Title
        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet(f"""
            color: {Theme.TEXT_MUTED};
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
        """)
        self.content_layout.addWidget(self.title_label)
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"""
            color: {Theme.TEXT_MAIN};
            font-size: 24px;
            font-weight: 800;
            margin: 4px 0;
        """)
        self.content_layout.addWidget(self.value_label)
        
        # Subtext / Trend
        if subtext:
            self.subtext_label = QLabel(subtext)
            color = status_color if status_color else Theme.TEXT_MUTED
            self.subtext_label.setStyleSheet(f"""
                color: {color};
                font-size: 12px;
                font-weight: 500;
            """)
            self.content_layout.addWidget(self.subtext_label)

    def update_value(self, value, subtext=None):
        self.value_label.setText(value)
        if subtext:
            self.subtext_label.setText(subtext)
