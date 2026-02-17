"""
PharmaPOS ERP - Payment Dialog
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from decimal import Decimal
from ..styles.theme import Theme

class PaymentDialog(QDialog):
    def __init__(self, cart, sales_service, user_id=1, store_id=1, parent=None):
        super().__init__(parent)
        self.cart = cart
        self.sales_service = sales_service
        self.user_id = user_id
        self.store_id = store_id
        self.total_amount = Decimal(str(sum(item['price'] * item['quantity'] for item in cart)))
        
        self.setWindowTitle("Close Bill - Payment")
        self.resize(400, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Summary Header
        header = QLabel(f"TOTAL PAYABLE: ₦{self.total_amount:,.2f}")
        header.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {Theme.SUCCESS};")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Payment Method
        layout.addWidget(QLabel("Payment Method:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems(["Cash", "Card", "Bank Transfer"])
        self.method_combo.currentIndexChanged.connect(self.update_fields)
        layout.addWidget(self.method_combo)

        # Amount Paid (Cash focus)
        self.amount_paid_lbl = QLabel("Amount Paid:")
        layout.addWidget(self.amount_paid_lbl)
        self.amount_paid_input = QLineEdit()
        self.amount_paid_input.setPlaceholderText("0.00")
        self.amount_paid_input.setText(str(self.total_amount))
        self.amount_paid_input.textChanged.connect(self.calculate_change)
        layout.addWidget(self.amount_paid_input)

        # Change Display
        self.change_frame = QFrame()
        self.change_frame.setStyleSheet(f"background-color: {Theme.SURFACE_MAIN}; border-radius: 8px; padding: 10px;")
        change_layout = QVBoxLayout(self.change_frame)
        self.change_label = QLabel("CHANGE: ₦0.00")
        self.change_label.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {Theme.TEXT_MAIN};")
        change_layout.addWidget(self.change_label)
        layout.addWidget(self.change_frame)

        # Reference Field (Hidden for Cash)
        self.ref_lbl = QLabel("Payment Reference / Confirmation Code:")
        self.ref_lbl.hide()
        layout.addWidget(self.ref_lbl)
        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("Enter transaction ID...")
        self.ref_input.hide()
        layout.addWidget(self.ref_input)

        layout.addStretch()

        # Action Buttons
        btns = QHBoxLayout()
        cancel_btn = QPushButton("CANCEL")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)
        
        self.close_bill_btn = QPushButton("CLOSE BILL")
        self.close_bill_btn.clicked.connect(self.handle_finalize)
        self.close_bill_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.SUCCESS};
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 800;
            }}
        """)
        btns.addWidget(self.close_bill_btn)
        layout.addLayout(btns)

    def update_fields(self):
        method = self.method_combo.currentText().lower()
        if method == "cash":
            self.amount_paid_lbl.show()
            self.amount_paid_input.show()
            self.change_frame.show()
            self.ref_lbl.hide()
            self.ref_input.hide()
        else:
            self.amount_paid_lbl.hide()
            self.amount_paid_input.hide()
            self.change_frame.hide()
            self.ref_lbl.show()
            self.ref_input.show()

    def calculate_change(self):
        try:
            paid = Decimal(self.amount_paid_input.text() or "0")
            change = paid - self.total_amount
            if change < 0:
                self.change_label.setText("INSUFFICIENT")
                self.change_label.setStyleSheet("color: red; font-size: 16px; font-weight: 700;")
            else:
                self.change_label.setText(f"CHANGE: ₦{change:,.2f}")
                self.change_label.setStyleSheet(f"color: {Theme.TEXT_MAIN}; font-size: 16px; font-weight: 700;")
        except:
            self.change_label.setText("INVALID")

    def handle_finalize(self):
        method = self.method_combo.currentText().lower()
        amount_paid = Decimal(self.amount_paid_input.text() or "0")
        reference = self.ref_input.text()

        if method == "cash" and amount_paid < self.total_amount:
            QMessageBox.warning(self, "Insufficient Payment", "Amount paid must be equal or greater than the total.")
            return

        # Prepare cart logic for finalized sale
        final_items = []
        for item in self.cart:
            final_items.append({
                'batch_id': item['batch_id'],
                'quantity': item['quantity'],
                'unit_price': item['price']
            })

        success, msg, sale_data = self.sales_service.finalize_sale(
            user_id=self.user_id,
            store_id=self.store_id,
            cart=final_items,
            payment_method=method,
            amount_paid=amount_paid if method == "cash" else self.total_amount,
            payment_reference=reference
        )

        if success:
            QMessageBox.information(self, "Success", f"Sale Completed! Receipt #: {sale_data['receipt_number']}")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", msg)
