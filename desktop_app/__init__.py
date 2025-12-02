"""
PharmaPOS NG - Desktop Application Package

A complete pharmacy billing and inventory management system.
"""

__version__ = "1.0.0"
__author__ = "PharmaPOS Development Team"
__description__ = "Pharmacy Management System - Billing & Inventory"

from desktop_app.database import init_db, get_engine, metadata
from desktop_app.models import (
    StoreService,
    UserService,
    ProductService,
    InventoryService,
    SalesService,
    StockTransferService,
    get_session,
)
from desktop_app.auth import AuthenticationService, UserSession, PasswordManager
from desktop_app.sales import SalesTransaction, PaymentProcessor, ReceiptGenerator
from desktop_app.inventory import BatchManager, StockTransferManager, InventoryAlerts
from desktop_app.reports import SalesReporter, InventoryReporter, AuditReporter
from desktop_app.config import get_config

__all__ = [
    # Version
    "__version__",
    # Database
    "init_db",
    "get_engine",
    "metadata",
    # Services
    "StoreService",
    "UserService",
    "ProductService",
    "InventoryService",
    "SalesService",
    "StockTransferService",
    "get_session",
    # Authentication
    "AuthenticationService",
    "UserSession",
    "PasswordManager",
    # Sales
    "SalesTransaction",
    "PaymentProcessor",
    "ReceiptGenerator",
    # Inventory
    "BatchManager",
    "StockTransferManager",
    "InventoryAlerts",
    # Reports
    "SalesReporter",
    "InventoryReporter",
    "AuditReporter",
    # Config
    "get_config",
]
