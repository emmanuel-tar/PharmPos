"""
PharmaPOS NG - User Management Dialog

Admin interface for managing users, roles, and viewing activity logs.
"""

from typing import Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QComboBox, QMessageBox, QTabWidget, QFormLayout,
    QHeaderView, QCheckBox
)
from PyQt5.QtCore import Qt

from desktop_app.models import UserService, get_session
from desktop_app.activity_logger import ActivityLogger
from desktop_app.config import DB_PATH


class UserManagementDialog(QDialog):
    """Dialog for managing users and viewing audit logs."""
    
    def __init__(self, current_user_session, parent=None):
        super().__init__(parent)
        self.current_user = current_user_session
        self.setWindowTitle("User Management & Audit")
        self.resize(900, 600)
        
        # Services
        self.session_db = get_session(DB_PATH)
        self.user_service = UserService(self.session_db)
        self.logger_service = ActivityLogger(self.session_db)
        
        self.setup_ui()
        self.load_users()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: Users List
        self.tab_users = QWidget()
        self.setup_users_tab()
        self.tabs.addTab(self.tab_users, "Manage Users")
        
        # Tab 2: Activity Logs
        self.tab_logs = QWidget()
        self.setup_logs_tab()
        self.tabs.addTab(self.tab_logs, "Activity Logs")
        
        # Close button
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)

    def setup_users_tab(self):
        layout = QVBoxLayout(self.tab_users)
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.btn_add = QPushButton("Add New User")
        self.btn_add.clicked.connect(self.add_user)
        self.btn_edit = QPushButton("Edit Selected")
        self.btn_edit.clicked.connect(self.edit_user)
        self.btn_deactivate = QPushButton("Deactivate/Activate")
        self.btn_deactivate.clicked.connect(self.toggle_user_status)
        
        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_deactivate)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Users Table
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(5)
        self.user_table.setHorizontalHeaderLabels(["ID", "Username", "Role", "Store ID", "Status"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.user_table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.user_table)

    def setup_logs_tab(self):
        layout = QVBoxLayout(self.tab_logs)
        
        # Filters
        filter_layout = QHBoxLayout()
        self.cb_log_user = QComboBox()
        self.cb_log_user.addItem("All Users", None)
        
        self.btn_refresh_logs = QPushButton("Refresh Logs")
        self.btn_refresh_logs.clicked.connect(self.load_logs)
        
        filter_layout.addWidget(QLabel("Filter User:"))
        filter_layout.addWidget(self.cb_log_user)
        filter_layout.addWidget(self.btn_refresh_logs)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Logs Table
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(5)
        self.log_table.setHorizontalHeaderLabels(["Time", "User", "Action", "Entity", "Details"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        layout.addWidget(self.log_table)

    def load_users(self):
        self.user_table.setRowCount(0)
        users = self.user_service.get_all_users()
        
        # Populate filter combo in logs tab
        self.cb_log_user.clear()
        self.cb_log_user.addItem("All Users", None)
        
        for row, user in enumerate(users):
            self.user_table.insertRow(row)
            self.user_table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
            self.user_table.setItem(row, 1, QTableWidgetItem(user['username']))
            self.user_table.setItem(row, 2, QTableWidgetItem(user['role']))
            self.user_table.setItem(row, 3, QTableWidgetItem(str(user['store_id'] or '-')))
            status = "Active" if user['is_active'] else "Inactive"
            self.user_table.setItem(row, 4, QTableWidgetItem(status))
            
            self.cb_log_user.addItem(user['username'], user['id'])

    def add_user(self):
        dialog = UserFormDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                # Assuming AuthenticationService logic is handled here or via wrapper
                # For direct db access (simplified):
                from desktop_app.auth import PasswordManager
                hashed_pw = PasswordManager.hash_password(data['password'])
                
                self.user_service.create_user(
                    username=data['username'],
                    password_hash=hashed_pw,
                    role=data['role'],
                    store_id=data['store_id']
                )
                
                self.logger_service.log_activity(
                    user_id=self.current_user.user_id,
                    username=self.current_user.username,
                    action="user_create",
                    entity_type="user",
                    details={"created_username": data['username'], "role": data['role']}
                )
                
                self.load_users()
                QMessageBox.information(self, "Success", "User created successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def edit_user(self):
        selected = self.user_table.selectedItems()
        if not selected:
            return
            
        user_id = int(self.user_table.item(selected[0].row(), 0).text())
        user = self.user_service.get_user(user_id)
        
        dialog = UserFormDialog(user, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            updates = {
                "role": data['role'],
                "store_id": data['store_id']
            }
            if data['password']:
                 from desktop_app.auth import PasswordManager
                 updates["password_hash"] = PasswordManager.hash_password(data['password'])
            
            self.user_service.update_user(user_id, **updates)
            
            self.logger_service.log_activity(
                user_id=self.current_user.user_id,
                username=self.current_user.username,
                action="user_update",
                entity_type="user",
                entity_id=user_id,
                details={"updates": list(updates.keys())}
            )
            
            self.load_users()

    def toggle_user_status(self):
        selected = self.user_table.selectedItems()
        if not selected:
            return
            
        user_id = int(self.user_table.item(selected[0].row(), 0).text())
        current_status = self.user_table.item(selected[0].row(), 4).text()
        
        new_active = current_status != "Active"
        self.user_service.update_user(user_id, is_active=new_active)
        
        self.logger_service.log_activity(
            user_id=self.current_user.user_id,
            username=self.current_user.username,
            action="user_status_change",
            entity_type="user",
            entity_id=user_id,
            details={"new_active_status": new_active}
        )
        
        self.load_users()

    def load_logs(self):
        user_id = self.cb_log_user.currentData()
        logs = self.logger_service.get_user_activities(user_id=user_id, limit=100)
        
        self.log_table.setRowCount(0)
        for row, log in enumerate(logs):
            self.log_table.insertRow(row)
            self.log_table.setItem(row, 0, QTableWidgetItem(str(log['created_at'])))
            self.log_table.setItem(row, 1, QTableWidgetItem(log['username']))
            self.log_table.setItem(row, 2, QTableWidgetItem(log['action']))
            self.log_table.setItem(row, 3, QTableWidgetItem(f"{log['entity_type']}:{log['entity_id']}" if log['entity_id'] else ""))
            self.log_table.setItem(row, 4, QTableWidgetItem(str(log['details']) if log['details'] else ""))

    def closeEvent(self, event):
        self.session_db.close()
        super().closeEvent(event)


class UserFormDialog(QDialog):
    """Form to add/edit user."""
    
    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User Details" if user_data else "Add New User")
        
        layout = QFormLayout(self)
        
        self.txt_username = QLineEdit()
        if user_data:
            self.txt_username.setText(user_data['username'])
            self.txt_username.setReadOnly(True)
        
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.Password)
        self.txt_password.setPlaceholderText("Leave blank to keep current" if user_data else "Required")
        
        self.cb_role = QComboBox()
        self.cb_role.addItems(["cashier", "manager", "admin", "pharmacist"])
        if user_data:
            self.cb_role.setCurrentText(user_data['role'])
            
        self.txt_store_id = QLineEdit() # Could be combo in full version
        if user_data and user_data['store_id']:
            self.txt_store_id.setText(str(user_data['store_id']))
            
        layout.addRow("Username:", self.txt_username)
        layout.addRow("Password:", self.txt_password)
        layout.addRow("Role:", self.cb_role)
        layout.addRow("Store ID (Optional):", self.txt_store_id)
        
        btn_box = QHBoxLayout()
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_cancel)
        layout.addRow(btn_box)
        
    def get_data(self):
        store_val = self.txt_store_id.text().strip()
        return {
            "username": self.txt_username.text(),
            "password": self.txt_password.text(),
            "role": self.cb_role.currentText(),
            "store_id": int(store_val) if store_val.isdigit() else None
        }
