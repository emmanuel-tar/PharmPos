"""
PharmaPOS NG - System Settings Dialog

Configuration interface for tax, business info, and compliance settings.
"""

from typing import Dict, Any
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QCheckBox, QPushButton, QTabWidget, QFormLayout, 
    QFrame, QMessageBox, QWidget, QScrollArea, QComboBox
)

from desktop_app.system_settings import SettingsManager
from desktop_app.activity_logger import ActivityLogger
from desktop_app.models import get_session
from desktop_app.config import DB_PATH
from desktop_app.ui import PrinterSettingsDialog  # Reuse existing printer dialog


class SettingsDialog(QDialog):
    """Unified system settings dialog."""
    
    def __init__(self, current_user_session, parent=None):
        super().__init__(parent)
        self.setWindowTitle("System Configuration")
        self.resize(800, 600)
        self.current_user = current_user_session
        
        self.session_db = get_session(DB_PATH)
        self.settings_manager = SettingsManager(self.session_db)
        self.logger_service = ActivityLogger(self.session_db)
        
        self.inputs = {}  # Store input widgets by key
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tabs
        self.tabs.addTab(self.create_business_tab(), "Business Info")
        self.tabs.addTab(self.create_tax_tab(), "Tax & Pricing")
        self.tabs.addTab(self.create_receipt_tab(), "Receipts")
        self.tabs.addTab(self.create_compliance_tab(), "Compliance")
        self.tabs.addTab(self.create_hardware_tab(), "Hardware")
        
        # Action Buttons
        btn_box = QHBoxLayout()
        btn_save = QPushButton("Save All Changes")
        btn_save.clicked.connect(self.save_settings)
        btn_save.setStyleSheet("background-color: #007bff; color: white; padding: 6px 12px; font-weight: bold;")
        
        btn_cancel = QPushButton("Close")
        btn_cancel.clicked.connect(self.reject)
        
        btn_box.addStretch()
        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)

    def create_business_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        self.add_setting_input(layout, "business.name", "Pharmacy Name")
        self.add_setting_input(layout, "business.address", "Address")
        self.add_setting_input(layout, "business.phone", "Phone Number")
        self.add_setting_input(layout, "business.email", "Email")
        self.add_setting_input(layout, "business.registration_number", "Business Reg. No")
        self.add_setting_input(layout, "business.pcn_license", "PCN License No")
        return widget

    def create_tax_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        header = QLabel("Tax Configuration")
        header.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addRow(header)
        
        self.add_setting_input(layout, "tax.vat_enabled", "Enable VAT", "bool")
        self.add_setting_input(layout, "tax.vat_rate", "VAT Rate (%)", "number")
        self.add_setting_input(layout, "tax.tax_inclusive", "Prices are Tax Inclusive", "bool")
        
        return widget

    def create_receipt_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.add_setting_input(layout, "receipt.header", "Receipt Header Text")
        self.add_setting_input(layout, "receipt.footer", "Receipt Footer Text")
        self.add_setting_input(layout, "receipt.show_logo", "Show Logo", "bool")
        self.add_setting_input(layout, "receipt.show_barcode", "Show Footer Barcode", "bool")
        
        return widget

    def create_compliance_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.add_setting_input(layout, "compliance.expiry_alert_days", "Expiry Alert Threshold (Days)", "number")
        self.add_setting_input(layout, "compliance.auto_generate_reports", "Auto-generate Monthly Compliance Reports", "bool")
        self.add_setting_input(layout, "general.activity_log_retention_days", "Activity Log Retention (Days)", "number")
        
        return widget

    def create_hardware_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        btn_printer = QPushButton("Configure Printer Settings")
        btn_printer.clicked.connect(self.open_printer_settings)
        layout.addWidget(btn_printer)
        
        desc = QLabel("Configure thermal printer connection, paper size, and specialized print commands from the dedicated printer dialog.")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addStretch()
        
        return widget

    def add_setting_input(self, layout, key, label, type="string"):
        if type == "bool":
            inp = QCheckBox()
        else:
            inp = QLineEdit()
        
        layout.addRow(label + ":", inp)
        self.inputs[key] = {"widget": inp, "type": type}

    def load_settings(self):
        settings = self.settings_manager.get_all()
        settings_map = {s['key']: s['parsed_value'] for s in settings}
        
        for key, input_data in self.inputs.items():
            val = settings_map.get(key)
            widget = input_data["widget"]
            
            if input_data["type"] == "bool":
                widget.setChecked(bool(val))
            else:
                widget.setText(str(val) if val is not None else "")

    def save_settings(self):
        try:
            changed_keys = []
            for key, input_data in self.inputs.items():
                widget = input_data["widget"]
                if input_data["type"] == "bool":
                    val = widget.isChecked()
                else:
                    val = widget.text()
                
                # Check formatting for numbers
                if input_data["type"] == "number":
                    try:
                        float(val)  # Validate
                    except ValueError:
                        QMessageBox.warning(self, "Validation Error", f"Invalid number format for {key}")
                        return
                
                # Retrieve old value to check if changed (optimization)
                old_val = self.settings_manager.get(key)
                
                # Loose comparison for string inputs
                if str(val) != str(old_val):
                     if self.settings_manager.set(key, val, user_id=self.current_user.user_id):
                         changed_keys.append(key)

            if changed_keys:
                self.logger_service.log_activity(
                    user_id=self.current_user.user_id,
                    username=self.current_user.username,
                    action="update_settings",
                    details={"changed_settings": changed_keys}
                )
                QMessageBox.information(self, "Success", "Settings saved successfully.")
                self.accept()
            else:
                QMessageBox.information(self, "Info", "No changes detected.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def open_printer_settings(self):
        dialog = PrinterSettingsDialog(parent=self)
        dialog.exec_()
    
    def closeEvent(self, event):
        self.session_db.close()
        super().closeEvent(event)
