"""
PharmaPOS ERP - Product Catalog View

Comprehensive product management interface.
Manage pricing tiers, NAFDAC info, and SKU master data.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QHeaderView, QPushButton, QSpacerItem, QSizePolicy,
    QFrame, QLineEdit, QTableWidgetItem, QMessageBox, QMenu
)
from PyQt5.QtCore import Qt

from ..components.widgets import ERPCard
from ..styles.theme import Theme
from ..dialogs.product_form import ProductFormDialog
from ..dialogs.category_manager import CategoryManagerDialog
from ..dialogs.item_history import ItemHistoryDialog

class ProductView(QWidget):
    """Modern product catalog management interface."""
    def __init__(self, product_service, category_service, inventory_service, parent=None):
        super().__init__(parent)
        self.product_service = product_service
        self.category_service = category_service
        self.inventory_service = inventory_service
        self.setup_ui()
        self.refresh_table()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # 1. Headline & Actions
        header_layout = QHBoxLayout()
        headline = QLabel("Product Catalog")
        headline.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 20px; font-weight: 700;")
        header_layout.addWidget(headline)
        
        header_layout.addStretch()
        
        self.add_product_btn = QPushButton("+ NEW PRODUCT")
        self.add_product_btn.clicked.connect(self.handle_add_product)
        self.add_product_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {Theme.PRIMARY_HOVER}; }}
        """)
        header_layout.addWidget(self.add_product_btn)
        
        self.category_btn = QPushButton("CATEGORIES")
        self.category_btn.clicked.connect(self.handle_manage_categories)
        self.category_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.SURFACE_CARD};
                color: {Theme.TEXT_MAIN};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {Theme.SURFACE_MAIN}; }}
        """)
        header_layout.addWidget(self.category_btn)
        
        self.import_btn = QPushButton("IMPORT / EXPORT")
        self.import_btn.setMenu(self.create_import_export_menu())
        self.import_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.SURFACE_CARD};
                color: {Theme.TEXT_MAIN};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
            }}
            QPushButton::menu-indicator {{ image: none; }}
            QPushButton:hover {{ background-color: {Theme.SURFACE_MAIN}; }}
        """)
        header_layout.addWidget(self.import_btn)
        
        layout.addLayout(header_layout)

        # 2. Search & Filter Bar
        filter_card = ERPCard()
        filter_layout = filter_card.set_layout(QHBoxLayout())
        filter_card.setFixedHeight(70)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search products by name, SKU, or Barcode...")
        self.search_input.textChanged.connect(self.refresh_table)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                background-color: {Theme.SURFACE_MAIN};
            }}
        """)
        filter_layout.addWidget(self.search_input)
        
        layout.addWidget(filter_card)

        # 3. Product Table Card
        table_card = ERPCard()
        table_layout = table_card.set_layout(QVBoxLayout())
        
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(6)
        self.product_table.setHorizontalHeaderLabels(["Name", "SKU", "Category", "Retail Price", "Wholesale", "Actions"])
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.product_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.product_table.verticalHeader().setVisible(False)
        self.product_table.setStyleSheet("border: none; background: transparent;")
        
        # Context Menu
        self.product_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.product_table.customContextMenuRequested.connect(self.show_context_menu)
        
        table_layout.addWidget(self.product_table)
        layout.addWidget(table_card)
        layout.addStretch()

    def refresh_table(self):
        query = self.search_input.text().lower()
        products = self.product_service.get_all_products(active_only=True)
        
        # Filter locally for instant search
        if query:
            products = [p for p in products if query in p['name'].lower() or query in p['sku'].lower() or (p['barcode'] and query in p['barcode'].lower())]
            
        self.product_table.setRowCount(len(products))
        for i, p in enumerate(products):
            self.product_table.setItem(i, 0, QTableWidgetItem(p['name']))
            self.product_table.setItem(i, 1, QTableWidgetItem(p['sku']))
            self.product_table.setItem(i, 2, QTableWidgetItem(p.get('category', 'Uncategorized')))
            self.product_table.setItem(i, 3, QTableWidgetItem(f"₦{p.get('retail_price', p.get('selling_price', 0)):,.2f}"))
            self.product_table.setItem(i, 4, QTableWidgetItem(f"₦{p.get('wholesale_price', 0):,.2f}"))
            
            # Action Buttons cell
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(8)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setFixedWidth(50)
            edit_btn.setStyleSheet(f"color: {Theme.PRIMARY}; border: none; font-weight: bold;")
            edit_btn.clicked.connect(lambda checked, prod=p: self.handle_edit_product(prod))
            
            hist_btn = QPushButton("Log")
            hist_btn.setFixedWidth(50)
            hist_btn.setStyleSheet(f"color: {Theme.INFO}; border: none; font-weight: bold;")
            hist_btn.clicked.connect(lambda checked, prod=p: self.handle_view_history(prod))

            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(hist_btn)
            btn_layout.addStretch()
            
            self.product_table.setCellWidget(i, 5, btn_widget)

    def show_context_menu(self, pos):
        item = self.product_table.itemAt(pos)
        if not item: return
        
        row = item.row()
        sku = self.product_table.item(row, 1).text()
        product = self.product_service.get_product_by_sku(sku)
        
        menu = QMenu(self)
        edit_action = menu.addAction("Edit Details")
        log_action = menu.addAction("View Movement History")
        menu.addSeparator()
        archive_action = menu.addAction("Archive Product")
        archive_action.setIconText("Archiving preserves sales history")
        
        action = menu.exec_(self.product_table.viewport().mapToGlobal(pos))
        
        if action == edit_action:
            self.handle_edit_product(product)
        elif action == log_action:
            self.handle_view_history(product)
        elif action == archive_action:
            self.handle_archive_product(product)

    def handle_add_product(self):
        dialog = ProductFormDialog(self.category_service, parent=self)
        if dialog.exec_():
            data = dialog.get_data()
            try:
                self.product_service.create_product(**data)
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create product: {str(e)}")

    def handle_edit_product(self, product):
        dialog = ProductFormDialog(self.category_service, product_data=product, parent=self)
        if dialog.exec_():
            data = dialog.get_data()
            try:
                self.product_service.update_product(product['id'], **data)
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update product: {str(e)}")

    def handle_view_history(self, product):
        dialog = ItemHistoryDialog(product['id'], product['name'], self.inventory_service, self)
        dialog.exec_()

    def handle_manage_categories(self):
        dialog = CategoryManagerDialog(self.category_service, self)
        dialog.exec_()

    def create_import_export_menu(self):
        menu = QMenu(self)
        export_csv = menu.addAction("Export to CSV")
        export_excel = menu.addAction("Export to Excel")
        menu.addSeparator()
        import_csv = menu.addAction("Import from CSV")
        import_excel = menu.addAction("Import from Excel")
        
        export_csv.triggered.connect(lambda: self.handle_export("csv"))
        export_excel.triggered.connect(lambda: self.handle_export("excel"))
        import_csv.triggered.connect(lambda: self.handle_import("csv"))
        import_excel.triggered.connect(lambda: self.handle_import("excel"))
        return menu

    def handle_export(self, format_type):
        from PyQt5.QtWidgets import QFileDialog
        from core.utils.import_helper import ImportExportHelper
        
        path, _ = QFileDialog.getSaveFileName(self, "Export Products", "", 
                                               "CSV Files (*.csv)" if format_type == "csv" else "Excel Files (*.xlsx)")
        if not path: return
        
        try:
            products = self.product_service.get_all_products(active_only=True)
            if format_type == "csv":
                ImportExportHelper.export_to_csv(products, path)
            else:
                ImportExportHelper.export_to_excel(products, path)
            QMessageBox.information(self, "Success", f"Products exported successfully to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")

    def handle_import(self, format_type):
        from PyQt5.QtWidgets import QFileDialog
        from core.utils.import_helper import ImportExportHelper
        
        path, _ = QFileDialog.getOpenFileName(self, "Import Products", "", 
                                               "CSV Files (*.csv)" if format_type == "csv" else "Excel Files (*.xlsx)")
        if not path: return
        
        try:
            if format_type == "csv":
                items = ImportExportHelper.parse_csv(path)
            else:
                items = ImportExportHelper.parse_excel(path)
            
            # Simple bulk internal processing
            count = 0
            errors = []
            for item in items:
                try:
                    # Clean data: converting types as needed
                    # This is a simplified bulk import
                    self.product_service.create_product(
                        name=item.get('name'),
                        sku=item.get('sku'),
                        cost_price=Decimal(str(item.get('cost_price', 0))),
                        selling_price=Decimal(str(item.get('selling_price', item.get('retail_price', 0)))),
                        category=item.get('category'),
                        barcode=item.get('barcode'),
                        nafdac_number=item.get('nafdac_number')
                    )
                    count += 1
                except Exception as ex:
                    errors.append(f"Row {item.get('name', 'Unknown')}: {str(ex)}")
            
            msg = f"Imported {count} products."
            if errors:
                msg += f"\n\nErrors encountered:\n" + "\n".join(errors[:5])
                if len(errors) > 5: msg += f"\n...and {len(errors)-5} more."
            
            QMessageBox.information(self, "Import Complete", msg)
            self.refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {str(e)}")

    def handle_archive_product(self, product):
        reply = QMessageBox.question(self, "Confirm Archive", 
                                     f"Are you sure you want to archive '{product['name']}'?\nIt will no longer appear in POS or Inventory.",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.product_service.deactivate_product(product['id'])
            self.refresh_table()
