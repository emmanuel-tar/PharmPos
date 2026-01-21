"""
PharmaPOS NG - Quick Stock Addition Module

Provides a simple interface to quickly add stock to existing products.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSpinBox, QDateEdit, QDoubleSpinBox, QLineEdit, QPushButton,
    QMessageBox, QGroupBox, QFormLayout
)
from PyQt5.QtCore import QDate

from desktop_app.logger import get_logger

logger = get_logger(__name__)


class QuickStockAddDialog(QDialog):
    """Simple dialog to quickly add stock to existing products."""
    
    def __init__(self, session, parent=None):
        """Initialize dialog.
        
        Args:
            session: Database session
            parent: Parent widget
        """
        super().__init__(parent)
        self.session = session
        self.result_data = None
        
        self.setWindowTitle("Quick Add Stock")
        self.setGeometry(200, 200, 500, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton#add_btn {
                background-color: #2ecc71;
                color: white;
                border: none;
            }
            QPushButton#add_btn:hover {
                background-color: #27ae60;
            }
            QPushButton#cancel_btn {
                background-color: #95a5a6;
                color: white;
                border: none;
            }
            QPushButton#cancel_btn:hover {
                background-color: #7f8c8d;
            }
        """)
        
        self.setup_ui()
        self.load_products()
        self.load_stores()
    
    def setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Title
        title = QLabel("📦 Quick Add Stock")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; padding: 10px;")
        layout.addWidget(title)
        
        # Product Selection Group
        product_group = QGroupBox("Product Information")
        product_layout = QFormLayout()
        
        self.product_combo = QComboBox()
        self.product_combo.setMinimumWidth(300)
        product_layout.addRow("Select Product:", self.product_combo)
        
        self.store_combo = QComboBox()
        product_layout.addRow("Store:", self.store_combo)
        
        product_group.setLayout(product_layout)
        layout.addWidget(product_group)
        
        # Stock Details Group
        stock_group = QGroupBox("Stock Details")
        stock_layout = QFormLayout()
        
        self.batch_number_input = QLineEdit()
        self.batch_number_input.setPlaceholderText("e.g., BATCH-2024-001")
        stock_layout.addRow("Batch Number:", self.batch_number_input)
        
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 100000)
        self.quantity_input.setValue(100)
        self.quantity_input.setSuffix(" units")
        stock_layout.addRow("Quantity:", self.quantity_input)
        
        self.expiry_date_input = QDateEdit()
        self.expiry_date_input.setDate(QDate.currentDate().addYears(2))
        self.expiry_date_input.setCalendarPopup(True)
        self.expiry_date_input.setDisplayFormat("yyyy-MM-dd")
        stock_layout.addRow("Expiry Date:", self.expiry_date_input)
        
        stock_group.setLayout(stock_layout)
        layout.addWidget(stock_group)
        
        # Pricing Group
        pricing_group = QGroupBox("Pricing")
        pricing_layout = QFormLayout()
        
        self.cost_price_input = QDoubleSpinBox()
        self.cost_price_input.setRange(0, 1000000)
        self.cost_price_input.setDecimals(2)
        self.cost_price_input.setPrefix("₦ ")
        self.cost_price_input.setValue(100.00)
        pricing_layout.addRow("Cost Price:", self.cost_price_input)
        
        self.retail_price_input = QDoubleSpinBox()
        self.retail_price_input.setRange(0, 1000000)
        self.retail_price_input.setDecimals(2)
        self.retail_price_input.setPrefix("₦ ")
        self.retail_price_input.setValue(150.00)
        pricing_layout.addRow("Retail Price:", self.retail_price_input)
        
        pricing_group.setLayout(pricing_layout)
        layout.addWidget(pricing_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        add_btn = QPushButton("✓ Add Stock")
        add_btn.setObjectName("add_btn")
        add_btn.clicked.connect(self.accept_stock)
        button_layout.addWidget(add_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_products(self):
        """Load products into combo box."""
        try:
            from desktop_app.models import ProductService
            
            product_service = ProductService(self.session)
            products = product_service.get_all_products(active_only=True)
            
            self.product_combo.clear()
            for product in products:
                display_text = f"{product['name']} ({product['sku']})"
                self.product_combo.addItem(display_text, product['id'])
            
            logger.info(f"Loaded {len(products)} products")
            
        except Exception as e:
            logger.error(f"Error loading products: {e}", exc_info=True)
            QMessageBox.warning(self, "Error", f"Failed to load products: {str(e)}")
    
    def load_stores(self):
        """Load stores into combo box."""
        try:
            from desktop_app.models import StoreService
            
            store_service = StoreService(self.session)
            stores = store_service.get_all_stores()
            
            self.store_combo.clear()
            for store in stores:
                self.store_combo.addItem(store['name'], store['id'])
            
            logger.info(f"Loaded {len(stores)} stores")
            
        except Exception as e:
            logger.error(f"Error loading stores: {e}", exc_info=True)
            QMessageBox.warning(self, "Error", f"Failed to load stores: {str(e)}")
    
    def accept_stock(self):
        """Validate and accept stock addition."""
        try:
            # Validation
            if self.product_combo.currentIndex() < 0:
                QMessageBox.warning(self, "Validation", "Please select a product")
                return
            
            if not self.batch_number_input.text().strip():
                QMessageBox.warning(self, "Validation", "Please enter a batch number")
                return
            
            if self.quantity_input.value() <= 0:
                QMessageBox.warning(self, "Validation", "Quantity must be greater than 0")
                return
            
            if self.cost_price_input.value() < 0:
                QMessageBox.warning(self, "Validation", "Cost price cannot be negative")
                return
            
            if self.retail_price_input.value() <= 0:
                QMessageBox.warning(self, "Validation", "Retail price must be greater than 0")
                return
            
            # Check expiry date
            expiry_date = self.expiry_date_input.date().toPyDate()
            if expiry_date <= date.today():
                reply = QMessageBox.question(
                    self,
                    "Expiry Warning",
                    "The expiry date is in the past or today. Continue anyway?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # Prepare result data
            self.result_data = {
                'product_id': self.product_combo.currentData(),
                'batch_number': self.batch_number_input.text().strip(),
                'quantity': self.quantity_input.value(),
                'expiry_date': expiry_date,
                'cost_price': Decimal(str(self.cost_price_input.value())),
                'retail_price': Decimal(str(self.retail_price_input.value())),
                'store_id': self.store_combo.currentData(),
            }
            
            logger.info(f"Stock addition validated: {self.result_data}")
            self.accept()
            
        except Exception as e:
            logger.error(f"Error validating stock: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Validation failed: {str(e)}")


__all__ = ['QuickStockAddDialog']
