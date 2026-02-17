"""
PharmaPOS ERP - Supplier Form Dialog
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFormLayout, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt
from ..styles.theme import Theme

class SupplierFormDialog(QDialog):
    def __init__(self, supplier_data=None, parent=None):
        super().__init__(parent)
        self.supplier_data = supplier_data # None for Create mode
        self.setWindowTitle("Supplier Details")
        self.resize(450, 400)
        self.setup_ui()
        if self.supplier_data:
            self.populate_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title_text = "Edit Supplier" if self.supplier_data else "Register New Supplier"
        title = QLabel(title_text)
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {Theme.TEXT_MAIN};")
        header_layout.addWidget(title)
        layout.addLayout(header_layout)

        # Form
        form_container = QFormLayout()
        form_container.setSpacing(12)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Supplier / Company Name")
        form_container.addRow("Company Name:", self.name_input)

        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("Phone or Email")
        form_container.addRow("Contact Info:", self.contact_input)

        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Physical Address")
        self.address_input.setMaximumHeight(80)
        form_container.addRow("Address:", self.address_input)

        layout.addLayout(form_container)
        layout.addStretch()

        # Actions
        actions = QHBoxLayout()
        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn = QPushButton("SAVE SUPPLIER")
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                font-weight: bold;
                padding: 10px 20px;
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

    def populate_data(self):
        s = self.supplier_data
        self.name_input.setText(s.get('name', ''))
        self.contact_input.setText(s.get('contact', ''))
        self.address_input.setPlainText(s.get('address', ''))

    def handle_save(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Supplier name is required.")
            return
        self.accept()

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "contact": self.contact_input.text().strip(),
            "address": self.address_input.toPlainText().strip()
        }
