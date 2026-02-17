"""
PharmaPOS ERP - Product Form Dialog
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QDoubleSpinBox, QSpinBox,
    QTabWidget, QWidget, QFormLayout, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt
from decimal import Decimal
from ..styles.theme import Theme

class ProductFormDialog(QDialog):
    def __init__(self, category_service, product_data=None, analytics_service=None, parent=None):
        super().__init__(parent)
        self.category_service = category_service
        self.analytics_service = analytics_service
        self.product_data = product_data # None for Create mode
        self.setWindowTitle("Product Details")
        self.resize(620, 750)
        self.setup_ui()
        self.load_categories()
        if self.product_data:
            self.populate_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header with Alert Badge
        header_layout = QHBoxLayout()
        title_text = "Edit Product" if self.product_data else "Create New Product"
        title = QLabel(title_text)
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {Theme.TEXT_MAIN};")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.alert_badge = QLabel("NEEDS REORDER")
        self.alert_badge.setVisible(False)
        self.alert_badge.setStyleSheet(f"""
            background-color: {Theme.DANGER};
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        """)
        header_layout.addWidget(self.alert_badge)
        layout.addLayout(header_layout)

        self.tabs = QTabWidget()
        
        # Tab 1: General Info
        self.info_tab = QWidget()
        info_layout = QFormLayout(self.info_tab)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Full Product Name")
        info_layout.addRow("Product Name:", self.name_input)

        self.sku_input = QLineEdit()
        self.sku_input.setPlaceholderText("Unique SKU / Code")
        info_layout.addRow("SKU / Code:", self.sku_input)

        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Barcode (Scan or Type)")
        info_layout.addRow("Barcode:", self.barcode_input)

        self.category_combo = QComboBox()
        info_layout.addRow("Category:", self.category_combo)

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("e.g. Aisle 4, Shelf B")
        info_layout.addRow("Warehouse Location:", self.location_input)

        self.nafdac_input = QLineEdit()
        self.nafdac_input.setPlaceholderText("NAFDAC Reg No.")
        info_layout.addRow("NAFDAC #:", self.nafdac_input)

        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(80)
        info_layout.addRow("Description:", self.desc_input)
        
        self.tabs.addTab(self.info_tab, "General Info")

        # Tab 2: Pricing Tiers
        self.pricing_tab = QWidget()
        pricing_layout = QFormLayout(self.pricing_tab)

        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0, 10000000)
        self.cost_spin.setPrefix("₦")
        pricing_layout.addRow("Cost Price:", self.cost_spin)

        self.retail_spin = QDoubleSpinBox()
        self.retail_spin.setRange(0, 10000000)
        self.retail_spin.setPrefix("₦")
        pricing_layout.addRow("Retail Price:", self.retail_spin)

        self.wholesale_spin = QDoubleSpinBox()
        self.wholesale_spin.setRange(0, 10000000)
        self.wholesale_spin.setPrefix("₦")
        pricing_layout.addRow("Wholesale Price:", self.wholesale_spin)
        
        self.wholesale_qty_spin = QSpinBox()
        self.wholesale_qty_spin.setRange(0, 10000)
        pricing_layout.addRow("Wholesale Threshold:", self.wholesale_qty_spin)

        self.bulk_spin = QDoubleSpinBox()
        self.bulk_spin.setRange(0, 10000000)
        self.bulk_spin.setPrefix("₦")
        pricing_layout.addRow("Bulk Price:", self.bulk_spin)

        self.bulk_qty_spin = QSpinBox()
        self.bulk_qty_spin.setRange(0, 10000)
        pricing_layout.addRow("Bulk Threshold:", self.bulk_qty_spin)

        self.tabs.addTab(self.pricing_tab, "Pricing Tiers")

        # Tab 3: Stock Control
        self.stock_tab = QWidget()
        stock_layout = QFormLayout(self.stock_tab)

        self.min_stock_spin = QSpinBox()
        self.min_stock_spin.setRange(0, 10000)
        stock_layout.addRow("Safety Stock (Min):", self.min_stock_spin)

        self.max_stock_spin = QSpinBox()
        self.max_stock_spin.setRange(0, 1000000)
        self.max_stock_spin.setValue(9999)
        stock_layout.addRow("Target Stock (Max):", self.max_stock_spin)

        self.reorder_spin = QSpinBox()
        self.reorder_spin.setRange(0, 10000)
        stock_layout.addRow("Reorder Level:", self.reorder_spin)

        self.tabs.addTab(self.stock_tab, "Stock Control")

        # Tab 4: Forecast & Trends
        self.forecast_tab = QWidget()
        forecast_layout = QVBoxLayout(self.forecast_tab)
        forecast_layout.setSpacing(10)
        
        if self.product_data:
            stats_container = QWidget()
            stats_layout = QFormLayout(stats_container)
            
            self.avg_sales_label = QLabel("Loading...")
            self.stock_longevity_label = QLabel("Loading...")
            self.stockout_date_label = QLabel("Loading...")
            self.total_sold_label = QLabel("Loading...")
            
            stats_layout.addRow("Avg Daily Sales (30d):", self.avg_sales_label)
            stats_layout.addRow("Total Sold (30d):", self.total_sold_label)
            stats_layout.addRow("Estimated Longevity:", self.stock_longevity_label)
            stats_layout.addRow("Forecasted Stock-out:", self.stockout_date_label)
            
            forecast_layout.addWidget(stats_container)
            
            tips_card = QWidget()
            tips_card.setStyleSheet(f"background-color: {Theme.INFO_LIGHT}; border-radius: 8px; padding: 12px;")
            tips_layout = QVBoxLayout(tips_card)
            tips_header = QLabel("Forecasting Insight")
            tips_header.setStyleSheet(f"font-weight: bold; color: {Theme.INFO};")
            self.insight_text = QLabel("Historical data is being used to predict your replenishment needs.")
            self.insight_text.setWordWrap(True)
            self.insight_text.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_MAIN};")
            
            tips_layout.addWidget(tips_header)
            tips_layout.addWidget(self.insight_text)
            forecast_layout.addWidget(tips_card)
        else:
            no_data = QLabel("Insights will be available once the product is created and has sales history.")
            no_data.setWordWrap(True)
            no_data.setAlignment(Qt.AlignCenter)
            no_data.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-style: italic;")
            forecast_layout.addStretch()
            forecast_layout.addWidget(no_data)
            forecast_layout.addStretch()

        self.tabs.addTab(self.forecast_tab, "Forecast & Trends")

        layout.addWidget(self.tabs)

        # Bottom Actions
        actions = QHBoxLayout()
        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn = QPushButton("SAVE PRODUCT")
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                font-weight: bold;
                padding: 12px 24px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {Theme.PRIMARY_HOVER};
            }}
        """)
        self.save_btn.clicked.connect(self.handle_save)
        
        actions.addStretch()
        actions.addWidget(self.cancel_btn)
        actions.addWidget(self.save_btn)
        layout.addLayout(actions)

    def load_categories(self):
        self.category_combo.clear()
        self.category_combo.addItem("-- Select Category --", None)
        categories = self.category_service.get_all_categories()
        for cat in categories:
            self.category_combo.addItem(cat['name'], cat['name'])

    def populate_data(self):
        p = self.product_data
        self.name_input.setText(p.get('name', ''))
        self.sku_input.setText(p.get('sku', ''))
        self.barcode_input.setText(p.get('barcode', ''))
        self.location_input.setText(p.get('warehouse_location', ''))
        self.nafdac_input.setText(p.get('nafdac_number', ''))
        self.desc_input.setPlainText(p.get('description', ''))
        
        # Select category
        index = self.category_combo.findData(p.get('category'))
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
            
        self.cost_spin.setValue(float(p.get('cost_price', 0)))
        self.retail_spin.setValue(float(p.get('retail_price') or p.get('selling_price', 0)))
        self.wholesale_spin.setValue(float(p.get('wholesale_price', 0) or 0))
        self.wholesale_qty_spin.setValue(p.get('wholesale_quantity', 0) or 0)
        self.bulk_spin.setValue(float(p.get('bulk_price', 0) or 0))
        self.bulk_qty_spin.setValue(p.get('bulk_quantity', 0) or 0)
        
        self.min_stock_spin.setValue(p.get('min_stock', 0))
        self.max_stock_spin.setValue(p.get('max_stock', 9999))
        self.reorder_level = p.get('reorder_level', 0) or 0
        self.reorder_spin.setValue(self.reorder_level)
        
        # Update Forecast
        if self.analytics_service and p.get('id'):
            forecast = self.analytics_service.get_product_forecast(p['id'])
            self.avg_sales_label.setText(f"{forecast['avg_daily_sales']} units / day")
            self.total_sold_label.setText(f"{forecast['total_sold_period']} units")
            self.stock_longevity_label.setText(forecast['days_remaining'])
            self.stockout_date_label.setText(forecast['forecast_stockout_date'])
            
            # Smart Badge & Insight
            total_stock = forecast['current_stock']
            if total_stock <= self.reorder_level:
                self.alert_badge.setVisible(True)
                self.insight_text.setText("Warning: Stock is below reorder level. Replenish soon to avoid stockouts.")
            elif forecast['avg_daily_sales'] > 0 and total_stock / forecast['avg_daily_sales'] < 7:
                 self.insight_text.setText("Critical: Item is selling fast! Predicted stockout in less than 7 days.")

    def get_data(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
            "sku": self.sku_input.text().strip(),
            "barcode": self.barcode_input.text().strip(),
            "category": self.category_combo.currentData(),
            "warehouse_location": self.location_input.text().strip(),
            "nafdac_number": self.nafdac_input.text().strip(),
            "description": self.desc_input.toPlainText().strip(),
            "cost_price": Decimal(str(self.cost_spin.value())),
            "selling_price": Decimal(str(self.retail_spin.value())),
            "retail_price": Decimal(str(self.retail_spin.value())),
            "wholesale_price": Decimal(str(self.wholesale_spin.value())),
            "wholesale_quantity": self.wholesale_qty_spin.value(),
            "bulk_price": Decimal(str(self.bulk_spin.value())),
            "bulk_quantity": self.bulk_qty_spin.value(),
            "min_stock": self.min_stock_spin.value(),
            "max_stock": self.max_stock_spin.value(),
            "reorder_level": self.reorder_spin.value(),
        }

    def handle_save(self):
        data = self.get_data()
        if not data["name"] or not data["sku"]:
            QMessageBox.warning(self, "Validation Error", "Product Name and SKU are required.")
            return
        self.accept()
