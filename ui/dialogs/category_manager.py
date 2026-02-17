"""
PharmaPOS ERP - Category Manager Dialog
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QHeaderView, QTableWidgetItem,
    QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt
from ..styles.theme import Theme

class CategoryManagerDialog(QDialog):
    def __init__(self, category_service, parent=None):
        super().__init__(parent)
        self.category_service = category_service
        self.setWindowTitle("Manage Categories")
        self.resize(500, 600)
        self.setup_ui()
        self.load_categories()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Product Categories")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {Theme.TEXT_MAIN};")
        layout.addWidget(title)

        # Form to add new category
        form_layout = QVBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Category Name (e.g., Antibiotics)")
        self.name_input.setStyleSheet(f"padding: 8px; border: 1px solid {Theme.BORDER}; border-radius: 4px;")
        form_layout.addWidget(self.name_input)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Description (optional)")
        self.desc_input.setMaximumHeight(80)
        self.desc_input.setStyleSheet(f"padding: 8px; border: 1px solid {Theme.BORDER}; border-radius: 4px;")
        form_layout.addWidget(self.desc_input)

        self.add_btn = QPushButton("ADD CATEGORY")
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: {Theme.PRIMARY_HOVER}; }}
        """)
        self.add_btn.clicked.connect(self.handle_add)
        form_layout.addWidget(self.add_btn)
        
        layout.addLayout(form_layout)

        # List of existing categories
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Name", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 100)
        layout.addWidget(self.table)

    def load_categories(self):
        categories = self.category_service.get_all_categories()
        self.table.setRowCount(len(categories))
        for i, cat in enumerate(categories):
            self.table.setItem(i, 0, QTableWidgetItem(cat['name']))
            
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet(f"color: {Theme.DANGER}; border: none; font-weight: bold;")
            delete_btn.clicked.connect(lambda checked, c=cat: self.handle_delete(c))
            self.table.setCellWidget(i, 1, delete_btn)

    def handle_add(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Category name is required")
            return
        
        try:
            self.category_service.create_category(name, self.desc_input.toPlainText())
            self.name_input.clear()
            self.desc_input.clear()
            self.load_categories()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not create category: {str(e)}")

    def handle_delete(self, category):
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete '{category['name']}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.category_service.delete_category(category['id'])
            self.load_categories()
