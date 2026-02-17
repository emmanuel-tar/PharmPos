"""
PharmaPOS ERP - Procurement & Inventory View

A comprehensive suite for managing the supply chain:
Suppliers, Purchase Orders, Receiving, and Stock Inventory.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QHeaderView, QPushButton, QSpacerItem, QSizePolicy,
    QFrame, QLineEdit, QTableWidgetItem, QTabWidget, QMessageBox
)
from PyQt5.QtCore import Qt

from ..components.widgets import ERPCard, MetricCard
from ..styles.theme import Theme
from ..dialogs.receive_po import ReceivePurchaseOrderDialog
from ..dialogs.supplier_form import SupplierFormDialog
from ..dialogs.purchase_order_form import PurchaseOrderFormDialog
from ..dialogs.receive_stock import ReceiveStockDialog


class ProcurementView(QWidget):
    """Integrated Procurement and Inventory Management interface."""
    
    def __init__(self, inventory_service=None, procurement_service=None, transfer_service=None, product_service=None, parent=None):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.procurement_service = procurement_service
        self.transfer_service = transfer_service
        self.product_service = product_service
        self.store_id = 1  # Placeholder
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 1. Header
        header_layout = QHBoxLayout()
        headline = QLabel("Procurement & Supply Chain")
        headline.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 20px; font-weight: 700;")
        header_layout.addWidget(headline)
        
        header_layout.addStretch()
        
        # Global Quick Actions
        self.new_po_btn = QPushButton("+ NEW PURCHASE ORDER")
        self.new_po_btn.clicked.connect(self.handle_create_po)
        self.new_po_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY}; 
                color: white; 
                padding: 10px 18px; 
                border-radius: 6px; 
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Theme.PRIMARY_HOVER};
            }}
        """)
        header_layout.addWidget(self.new_po_btn)
        
        layout.addLayout(header_layout)

        # 2. Main Tabbed Interface
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {Theme.BORDER}; border-radius: 8px; background: white; }}
            QTabBar::tab {{ padding: 12px 24px; font-weight: 600; color: {Theme.TEXT_MUTED}; }}
            QTabBar::tab:selected {{ color: {Theme.PRIMARY}; border-bottom: 2px solid {Theme.PRIMARY}; }}
        """)

        # --- Tab 1: Stock Inventory ---
        self.inventory_tab = QWidget()
        self.setup_inventory_tab()
        self.tabs.addTab(self.inventory_tab, "Live Inventory")

        # --- Tab 2: Suppliers ---
        self.suppliers_tab = QWidget()
        self.setup_suppliers_tab()
        self.tabs.addTab(self.suppliers_tab, "Suppliers")

        # --- Tab 3: Purchase Orders ---
        self.po_tab = QWidget()
        self.setup_po_tab()
        self.tabs.addTab(self.po_tab, "Purchase Orders")

        layout.addWidget(self.tabs)

    def setup_inventory_tab(self):
        layout = QVBoxLayout(self.inventory_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Metrics Row
        metrics_layout = QHBoxLayout()
        self.total_value_card = MetricCard("Inventory Value", "₦0.00", "Live stock cost", Theme.INFO)
        self.expiring_card = MetricCard("Critical Expiries", "0", "Within 30 days", Theme.DANGER)
        self.low_stock_card = MetricCard("Low Stock Items", "0", "Below reorder level", Theme.WARNING)
        
        metrics_layout.addWidget(self.total_value_card)
        metrics_layout.addWidget(self.expiring_card)
        metrics_layout.addWidget(self.low_stock_card)
        layout.addLayout(metrics_layout)

        # Controls
        ctrl_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search inventory...")
        self.search_input.textChanged.connect(self.refresh_inventory_table)
        self.search_input.setStyleSheet(f"padding: 10px; border: 1px solid {Theme.BORDER}; border-radius: 6px;")
        ctrl_layout.addWidget(self.search_input)
        
        self.receive_btn = QPushButton("RECEIVE STOCK")
        self.receive_btn.clicked.connect(self.handle_receive_stock)
        self.receive_btn.setStyleSheet(f"background-color: {Theme.SUCCESS}; color: white; padding: 10px 18px; border-radius: 6px; font-weight: bold;")
        ctrl_layout.addWidget(self.receive_btn)
        
        layout.addLayout(ctrl_layout)

        # Table
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(7)
        self.inventory_table.setHorizontalHeaderLabels(["Product", "Batch #", "Expiry", "Stock", "Location", "Cost", "Value"])
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inventory_table.verticalHeader().setVisible(False)
        layout.addWidget(self.inventory_table)
        
        self.refresh_inventory_status()
        self.refresh_inventory_table()

    def setup_suppliers_tab(self):
        layout = QVBoxLayout(self.suppliers_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QHBoxLayout()
        headline = QLabel("Registered Suppliers")
        headline.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Theme.TEXT_MAIN};")
        header.addWidget(headline)
        header.addStretch()
        self.add_supplier_btn = QPushButton("+ REGISTER SUPPLIER")
        self.add_supplier_btn.clicked.connect(self.handle_add_supplier)
        self.add_supplier_btn.setStyleSheet(f"background-color: {Theme.PRIMARY}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        header.addWidget(self.add_supplier_btn)
        layout.addLayout(header)

        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(4)
        self.suppliers_table.setHorizontalHeaderLabels(["Name", "Contact info", "Address", "Actions"])
        self.suppliers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.suppliers_table.verticalHeader().setVisible(False)
        layout.addWidget(self.suppliers_table)
        
        self.refresh_suppliers_table()

    def setup_po_tab(self):
        layout = QVBoxLayout(self.po_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QHBoxLayout()
        headline = QLabel("Purchase Order History")
        headline.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Theme.TEXT_MAIN};")
        header.addWidget(headline)
        header.addStretch()
        self.create_po_btn_tab = QPushButton("CREATE ORDER")
        self.create_po_btn_tab.clicked.connect(self.handle_create_po)
        self.create_po_btn_tab.setStyleSheet(f"background-color: {Theme.INFO}; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        header.addWidget(self.create_po_btn_tab)
        layout.addLayout(header)

        self.po_table = QTableWidget()
        self.po_table.setColumnCount(6)
        self.po_table.setHorizontalHeaderLabels(["PO #", "Supplier", "Total Amount", "Status", "Date", "Actions"])
        self.po_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.po_table.verticalHeader().setVisible(False)
        layout.addWidget(self.po_table)
        
        self.refresh_po_table()

    # --- Data Refreshes ---

    def refresh_inventory_status(self):
        if not self.inventory_service: return
        status = self.inventory_service.get_stock_status(self.store_id)
        expiring = self.inventory_service.get_expiring_items(self.store_id)
        self.expiring_card.update_value(str(len(expiring)))
        self.low_stock_card.update_value(str(status.get('low_stock_count', 0)))

    def refresh_inventory_table(self):
        if not self.inventory_service: return
        query = self.search_input.text().lower()
        batches = self.inventory_service.get_batches_by_store(self.store_id)
        if query:
            batches = [b for b in batches if query in b.get('product_name', '').lower() or query in b.get('batch_number', '').lower()]
        
        self.inventory_table.setRowCount(len(batches))
        for i, b in enumerate(batches):
            self.inventory_table.setItem(i, 0, QTableWidgetItem(b.get('product_name', 'Unknown')))
            self.inventory_table.setItem(i, 1, QTableWidgetItem(b.get('batch_number', 'N/A')))
            self.inventory_table.setItem(i, 2, QTableWidgetItem(str(b.get('expiry_date', 'N/A'))))
            qty = b.get('quantity') or 0
            cost = b.get('cost_price') or 0
            value = float(qty) * float(cost)
            self.inventory_table.setItem(i, 3, QTableWidgetItem(str(qty)))
            self.inventory_table.setItem(i, 4, QTableWidgetItem(b.get('warehouse_location', 'N/A')))
            self.inventory_table.setItem(i, 5, QTableWidgetItem(f"₦{float(cost):,.2f}"))
            self.inventory_table.setItem(i, 6, QTableWidgetItem(f"₦{value:,.2f}"))

    def refresh_suppliers_table(self):
        if not self.procurement_service: return
        suppliers_list = self.procurement_service.get_all_suppliers()
        self.suppliers_table.setRowCount(len(suppliers_list))
        for i, s in enumerate(suppliers_list):
            self.suppliers_table.setItem(i, 0, QTableWidgetItem(s['name']))
            self.suppliers_table.setItem(i, 1, QTableWidgetItem(s.get('contact', '')))
            self.suppliers_table.setItem(i, 2, QTableWidgetItem(s.get('address', '')))
            
            # Action Buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 4, 4, 4)
            
            edit_btn = QPushButton("EDIT")
            edit_btn.setFixedWidth(60)
            edit_btn.setStyleSheet(f"background-color: {Theme.PRIMARY_LIGHT}; color: {Theme.PRIMARY}; border-radius: 4px; font-size: 10px; height: 24px;")
            edit_btn.clicked.connect(lambda checked, sup=s: self.handle_edit_supplier(sup))
            action_layout.addWidget(edit_btn)
            
            self.suppliers_table.setCellWidget(i, 3, action_widget)

    def refresh_po_table(self):
        if not self.procurement_service: return
        pos = self.procurement_service.get_purchase_orders(self.store_id)
        self.po_table.setRowCount(len(pos))
        for i, po in enumerate(pos):
            self.po_table.setItem(i, 0, QTableWidgetItem(po['po_number']))
            self.po_table.setItem(i, 1, QTableWidgetItem(po.get('supplier_name', 'Unknown')))
            self.po_table.setItem(i, 2, QTableWidgetItem(f"₦{float(po.get('total_expected_amount', 0)):,.2f}"))
            self.po_table.setItem(i, 3, QTableWidgetItem(po['status'].upper()))
            self.po_table.setItem(i, 4, QTableWidgetItem(str(po.get('created_at'))[:10]))

            # Action Buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 4, 4, 4)
            
            status = po['status'].lower()
            if status not in ['received', 'cancelled']:
                rcv_btn = QPushButton("RECEIVE")
                rcv_btn.setFixedWidth(70)
                rcv_btn.setStyleSheet(f"background-color: {Theme.SUCCESS}; color: white; border-radius: 4px; font-size: 10px; font-weight: bold; height: 24px;")
                rcv_btn.clicked.connect(lambda checked, p=po: self.handle_receive_po(p))
                action_layout.addWidget(rcv_btn)
            
            self.po_table.setCellWidget(i, 5, action_widget)

    # --- Event Handlers ---

    def handle_receive_stock(self):
        # Generic receiving
        dialog = ReceiveStockDialog(1, "Sample Product", self) # Placeholder
        if dialog.exec_():
            pass

    def handle_add_supplier(self):
        dialog = SupplierFormDialog(parent=self)
        if dialog.exec_():
            data = dialog.get_data()
            try:
                self.procurement_service.create_supplier(**data)
                self.refresh_suppliers_table()
                QMessageBox.information(self, "Success", "Supplier registered successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to register supplier: {str(e)}")

    def handle_edit_supplier(self, supplier):
        dialog = SupplierFormDialog(supplier_data=supplier, parent=self)
        if dialog.exec_():
            data = dialog.get_data()
            try:
                self.procurement_service.update_supplier(supplier['id'], **data)
                self.refresh_suppliers_table()
                QMessageBox.information(self, "Success", "Supplier updated successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update supplier: {str(e)}")

    def handle_create_po(self):
        if not self.procurement_service or not self.product_service: return
        
        suppliers = self.procurement_service.get_all_suppliers()
        if not suppliers:
            QMessageBox.warning(self, "No Suppliers", "Please register at least one supplier before creating a purchase order.")
            self.tabs.setCurrentIndex(1)
            return

        dialog = PurchaseOrderFormDialog(self.procurement_service, self.product_service, parent=self)
        if dialog.exec_():
            data = dialog.get_data()
            try:
                self.procurement_service.create_purchase_order(
                    supplier_id=data['supplier_id'],
                    store_id=self.store_id,
                    user_id=1,
                    items=data['items'],
                    expected_delivery_date=data['expected_delivery_date'],
                    notes=data['notes']
                )
                self.refresh_po_table()
                QMessageBox.information(self, "Success", "Purchase Order created successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create purchase order: {str(e)}")

    def handle_receive_po(self, po):
        po_details = self.procurement_service.get_purchase_order_details(po['id'])
        if not po_details or not po_details.get('items'):
            QMessageBox.warning(self, "Error", "Could not load PO items.")
            return

        dialog = ReceivePurchaseOrderDialog(self.procurement_service, po['id'], po['po_number'], po_details['items'], self)
        if dialog.exec_():
            receipts = dialog.get_data()
            try:
                self.procurement_service.receive_goods(po['id'], 1, receipts)
                self.refresh_po_table()
                self.refresh_inventory_table()
                self.refresh_inventory_status()
                QMessageBox.information(self, "Success", "Goods received and inventory updated!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to receive goods: {str(e)}")
