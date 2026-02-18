"""
PharmaPOS ERP - Reusable Widgets

Modern, premium UI components for the ERP interface.
Includes shadow effects to replace problematic CSS box-shadow.
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QGraphicsDropShadowEffect, QWidget, QHBoxLayout, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QPixmap, QIcon

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

class ProductCard(ERPCard):
    """Premium product card for POS grid."""
    clicked = pyqtSignal(dict) # Emits product data

    def __init__(self, product_data, parent=None):
        super().__init__(parent)
        self.product_data = product_data
        self.setFixedSize(160, 200)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        self.set_layout(layout)

        # Image Container
        self.image_label = QLabel()
        self.image_label.setFixedSize(140, 100)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(f"background: {Theme.SURFACE_LIGHT}; border-radius: 8px;")
        
        img_path = product_data.get('image_path')
        if img_path and os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            self.image_label.setPixmap(pixmap.scaled(140, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            # Fallback icon or text
            self.image_label.setText("No Image")
            self.image_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; background: {Theme.SURFACE_LIGHT}; border-radius: 8px; font-size: 10px;")
            
        layout.addWidget(self.image_label)

        # Name
        name_label = QLabel(product_data['name'])
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-weight: 600; font-size: 12px;")
        layout.addWidget(name_label)

        # Price
        price_row = QHBoxLayout()
        price = product_data.get('selling_price', 0)
        price_label = QLabel(f"₦{float(price):,.2f}")
        price_label.setStyleSheet(f"color: {Theme.PRIMARY}; font-weight: 800; font-size: 14px;")
        price_row.addWidget(price_label)
        
        # Stock Level
        stock_qty = product_data.get('stock_quantity', 0)
        stock_label = QLabel(f"Qty: {stock_qty}")
        stock_color = Theme.TEXT_MUTED
        if stock_qty <= (product_data.get('min_stock', 0) or 0):
            stock_color = Theme.DANGER
            
        stock_label.setStyleSheet(f"color: {stock_color}; font-size: 11px; font-weight: 600;")
        price_row.addStretch()
        price_row.addWidget(stock_label)
        
        layout.addLayout(price_row)
        
        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.product_data)
        super().mousePressEvent(event)
