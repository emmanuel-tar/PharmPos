"""
PharmaPOS NG - Dashboard Widgets

Reusable UI widgets for the main dashboard.
"""

import sys
from typing import List, Dict, Any, Optional
from decimal import Decimal

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QPushButton, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette

# Use Matplotlib for charts
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates


class KPICard(QFrame):
    """Card to display a Key Performance Indicator."""
    
    def __init__(self, title: str, value: str, subtext: str = "", color: str = "#007BFF", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet(f"""
            KPICard {{
                background-color: white;
                border-radius: 8px;
                border-left: 5px solid {color};
            }}
            QLabel {{ border: none; }}
        """)
        
        layout = QVBoxLayout(self)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("color: #666; font-size: 14px; font-weight: bold;")
        
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        
        self.lbl_subtext = QLabel(subtext)
        self.lbl_subtext.setStyleSheet("color: #999; font-size: 12px;")
        
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)
        layout.addWidget(self.lbl_subtext)
        layout.addStretch()

    def update_value(self, value: str, subtext: str = ""):
        self.lbl_value.setText(value)
        if subtext:
            self.lbl_subtext.setText(subtext)


class SalesTrendChart(QWidget):
    """Matplotlib chart showing sales trend."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        self.figure = Figure(figsize=(5, 3), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Sales Trend (Last 7 Days)", fontsize=10)
        self.figure.tight_layout()

    def plot_data(self, dates: List[str], values: List[float]):
        self.ax.clear()
        
        if not dates or not values:
            self.ax.text(0.5, 0.5, "No Data", ha='center', va='center')
        else:
            self.ax.plot(dates, values, marker='o', linestyle='-', color='#007BFF')
            self.ax.fill_between(dates, values, alpha=0.3, color='#007BFF')
            
            # Formatting
            self.ax.set_title("Sales Trend (Last 7 Days)", fontsize=10)
            self.ax.grid(True, linestyle='--', alpha=0.7)
            
            # Rotate date labels
            self.figure.autofmt_xdate()
        
        self.canvas.draw()


class ProfitMarginWidget(QWidget):
    """Widget displaying profit vs cost breakdown."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        self.figure = Figure(figsize=(4, 3), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Profit Analysis (30 Days)", fontsize=10)

    def plot_data(self, revenue: float, cost: float, profit: float):
        self.ax.clear()
        
        if revenue == 0:
            self.ax.text(0.5, 0.5, "No Sales Data", ha='center', va='center')
        else:
            # Pie chart: Cost vs Profit
            labels = ['Cost', 'Profit']
            # Avoid negative wedges if loss
            if profit < 0:
                sizes = [revenue, 0] # Show full cost as revenue consumed? keeping simple
                self.ax.text(0.5, 0.5, "Net Loss", ha='center', va='center', color='red')
            else:
                sizes = [cost, profit]
                colors = ['#dc3545', '#28a745'] # Red for cost, Green for profit
                
                self.ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
                self.ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
            
            self.ax.set_title(f"Margin: {((profit/revenue)*100):.1f}%", fontsize=10)
            
        self.canvas.draw()


class InventoryAlertWidget(QFrame):
    """Widget showing critical inventory alerts."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("background-color: white; border-radius: 8px;")
        
        layout = QVBoxLayout(self)
        
        header = QLabel("⚠️ Critical Stock Alerts")
        header.setStyleSheet("font-weight: bold; color: #dc3545; font-size: 14px;")
        layout.addWidget(header)
        
        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)
        layout.addStretch()
        
    def update_alerts(self, low_stock: List[Dict], expiring: List[Dict]):
        # Clear existing
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not low_stock and not expiring:
            self.content_layout.addWidget(QLabel("No critical alerts."))
            return
            
        # Add expiring first (critical)
        for item in expiring[:3]: # Show top 3
            lbl = QLabel(f"EXPIRED SOON: {item['product_name']} ({item['days_until_expiry']} days)")
            lbl.setStyleSheet("color: #dc3545; font-weight: bold;")
            self.content_layout.addWidget(lbl)
            
        # Add low stock
        for item in low_stock[:3]:
            lbl = QLabel(f"LOW STOCK: {item['product_name']} ({item['current_stock']} left)")
            lbl.setStyleSheet("color: #ffc107; font-weight: bold;")
            self.content_layout.addWidget(lbl)
