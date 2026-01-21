"""
PharmaPOS NG - Compliance Dashboard

Regulatory reports and alerts interface (NAFDAC, PCN).
"""

from datetime import datetime, timedelta
import csv
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QTabWidget, QHeaderView, QDateEdit, QComboBox, QMessageBox, 
    QFileDialog, QWidget
)
from PyQt5.QtCore import Qt, QDate

from desktop_app.compliance_reports import ComplianceService
from desktop_app.activity_logger import ActivityLogger
from desktop_app.models import get_session, StoreService
from desktop_app.config import DB_PATH


class ComplianceDashboard(QDialog):
    """Dashboard for compliance reports and alerts."""
    
    def __init__(self, current_user_session, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Compliance & Reporting")
        self.resize(1000, 700)
        self.current_user = current_user_session
        
        self.session_db = get_session(DB_PATH)
        self.compliance_service = ComplianceService(self.session_db)
        self.store_service = StoreService(self.session_db)
        self.logger_service = ActivityLogger(self.session_db)
        
        self.setup_ui()
        self.load_alerts()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tabs
        self.tabs.addTab(self.create_nafdac_tab(), "NAFDAC Report")
        self.tabs.addTab(self.create_pcn_tab(), "PCN Report")
        self.tabs.addTab(self.create_alerts_tab(), "Compliance Alerts")
        
        self.tabs.currentChanged.connect(self.on_tab_change)
        
        # Close
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)

    def create_nafdac_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controls
        controls = QHBoxLayout()
        
        self.date_start_nafdac = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_start_nafdac.setCalendarPopup(True)
        self.date_end_nafdac = QDateEdit(QDate.currentDate())
        self.date_end_nafdac.setCalendarPopup(True)
        
        btn_gen = QPushButton("Generate Report")
        btn_gen.clicked.connect(self.generate_nafdac)
        
        btn_export = QPushButton("Export CSV")
        btn_export.clicked.connect(lambda: self.export_table(self.table_nafdac))
        
        controls.addWidget(QLabel("From:"))
        controls.addWidget(self.date_start_nafdac)
        controls.addWidget(QLabel("To:"))
        controls.addWidget(self.date_end_nafdac)
        controls.addWidget(btn_gen)
        controls.addWidget(btn_export)
        controls.addStretch()
        
        layout.addLayout(controls)
        
        # Table
        self.table_nafdac = QTableWidget()
        self.table_nafdac.setColumnCount(6)
        self.table_nafdac.setHorizontalHeaderLabels([
            "Product Name", "Generic Name", "NAFDAC No", "Batch No", "Expiry", "Qty Sold"
        ])
        self.table_nafdac.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_nafdac)
        
        return widget

    def create_pcn_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controls
        controls = QHBoxLayout()
        
        self.date_start_pcn = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_start_pcn.setCalendarPopup(True)
        self.date_end_pcn = QDateEdit(QDate.currentDate())
        self.date_end_pcn.setCalendarPopup(True)
        
        btn_gen = QPushButton("Generate Report")
        btn_gen.clicked.connect(self.generate_pcn)
        
        controls.addWidget(QLabel("From:"))
        controls.addWidget(self.date_start_pcn)
        controls.addWidget(QLabel("To:"))
        controls.addWidget(self.date_end_pcn)
        controls.addWidget(btn_gen)
        controls.addStretch()
        
        layout.addLayout(controls)
        
        # Display Area (PCN report is summary based)
        self.lbl_pcn_summary = QLabel("Select dates and generate report.")
        self.lbl_pcn_summary.setAlignment(Qt.AlignTop)
        self.lbl_pcn_summary.setStyleSheet("font-family: monospace; padding: 10px; background: white;")
        layout.addWidget(self.lbl_pcn_summary, stretch=1)
        
        return widget

    def create_alerts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        controls = QHBoxLayout()
        btn_refresh = QPushButton("Refresh Alerts")
        btn_refresh.clicked.connect(self.load_alerts)
        
        btn_resolve = QPushButton("Mark Resolved")
        btn_resolve.clicked.connect(self.resolve_alert)
        
        controls.addWidget(btn_refresh)
        controls.addWidget(btn_resolve)
        controls.addStretch()
        layout.addLayout(controls)
        
        self.table_alerts = QTableWidget()
        self.table_alerts.setColumnCount(5)
        self.table_alerts.setHorizontalHeaderLabels(["ID", "Type", "Severity", "Title", "Message"])
        self.table_alerts.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_alerts.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_alerts.setSelectionMode(QTableWidget.SingleSelection)
        self.table_alerts.setColumnHidden(0, True) # Hide ID
        
        layout.addWidget(self.table_alerts)
        
        return widget

    def generate_nafdac(self):
        try:
            start = self.date_start_nafdac.date().toPyDate()
            # End of day for end date
            end = datetime.combine(self.date_end_nafdac.date().toPyDate(), datetime.max.time())
            start_dt = datetime.combine(start, datetime.min.time())
            
            data = self.compliance_service.generate_nafdac_report(start_dt, end)
            
            self.table_nafdac.setRowCount(0)
            for row, item in enumerate(data):
                self.table_nafdac.insertRow(row)
                self.table_nafdac.setItem(row, 0, QTableWidgetItem(item.get('product_name', '')))
                self.table_nafdac.setItem(row, 1, QTableWidgetItem(item.get('generic_name', '')))
                self.table_nafdac.setItem(row, 2, QTableWidgetItem(item.get('nafdac_number', '')))
                self.table_nafdac.setItem(row, 3, QTableWidgetItem(item.get('batch_number', '')))
                self.table_nafdac.setItem(row, 4, QTableWidgetItem(str(item.get('expiry_date', ''))))
                self.table_nafdac.setItem(row, 5, QTableWidgetItem(str(item.get('quantity_sold', 0))))

            self.logger_service.log_activity(
                user_id=self.current_user.user_id,
                username=self.current_user.username,
                action="report_nafdac",
                details={"start": str(start), "end": str(end), "rows": len(data)}
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {e}")

    def generate_pcn(self):
        try:
            start = self.date_start_pcn.date().toPyDate()
            end = datetime.combine(self.date_end_pcn.date().toPyDate(), datetime.max.time())
            start_dt = datetime.combine(start, datetime.min.time())
            
            report = self.compliance_service.generate_pcn_report(start_dt, end)
            
            text = f"""PHARMACISTS COUNCIL OF NIGERIA - OPERATIONAL REPORT
Period: {report.get('period_start')} to {report.get('period_end')}
Generated: {report.get('generated_at')}

--- SALES SUMMARY ---
Total Transactions: {report['sales_metrics'].get('total_transactions', 0)}
Total Revenue: ₦{report['sales_metrics'].get('total_revenue', 0):,.2f}

--- ETHICAL/POISON DRUG SALES ---
"""
            for item in report.get('ethical_drug_sales', []):
                text += f"- {item['category']}: {item['units_sold']} units\n"
                
            text += "\n--- STAFFING LOG ---\n(Refer to Activity Logs for detailed staff duty roster)"
            
            self.lbl_pcn_summary.setText(text)
            
            self.logger_service.log_activity(
                user_id=self.current_user.user_id,
                username=self.current_user.username,
                action="report_pcn",
                details={"period": f"{start} to {end}"}
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {e}")

    def load_alerts(self):
        try:
            # Trigger check first
            self.compliance_service.check_and_create_expiry_alerts()
            
            alerts = self.compliance_service.get_active_alerts()
            self.table_alerts.setRowCount(0)
            
            for row, alert in enumerate(alerts):
                self.table_alerts.insertRow(row)
                self.table_alerts.setItem(row, 0, QTableWidgetItem(str(alert['id'])))
                self.table_alerts.setItem(row, 1, QTableWidgetItem(alert['alert_type']))
                
                sev_item = QTableWidgetItem(alert['severity'].upper())
                if alert['severity'] == 'critical':
                    sev_item.setBackground(Qt.red)
                    sev_item.setForeground(Qt.white)
                elif alert['severity'] == 'high':
                    sev_item.setBackground(Qt.yellow)
                    sev_item.setForeground(Qt.black)
                    
                self.table_alerts.setItem(row, 2, sev_item)
                self.table_alerts.setItem(row, 3, QTableWidgetItem(alert['title']))
                self.table_alerts.setItem(row, 4, QTableWidgetItem(alert['message']))
        except Exception as e:
            pass # Keep silent refresh

    def resolve_alert(self):
        selected = self.table_alerts.selectedItems()
        if not selected:
            return
            
        row = selected[0].row()
        alert_id = int(self.table_alerts.item(row, 0).text())
        
        if self.compliance_service.resolve_alert(alert_id, self.current_user.user_id):
            self.load_alerts()
            QMessageBox.information(self, "Success", "Alert resolved.")

    def export_table(self, table):
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # Headers
                    headers = []
                    for c in range(table.columnCount()):
                        headers.append(table.horizontalHeaderItem(c).text())
                    writer.writerow(headers)
                    
                    # Rows
                    for r in range(table.rowCount()):
                        row_data = []
                        for c in range(table.columnCount()):
                            item = table.item(r, c)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)
                
                QMessageBox.information(self, "Success", f"Exported to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {e}")

    def on_tab_change(self, index):
        if index == 2: # Alerts tab
            self.load_alerts()

    def closeEvent(self, event):
        self.session_db.close()
        super().closeEvent(event)
