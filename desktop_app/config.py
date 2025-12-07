"""
PharmaPOS NG - Configuration Settings

Centralized configuration for the application.
"""

import json
import os
from pathlib import Path
from decimal import Decimal
from typing import Final, Optional, Dict, Any

# --- File Paths ---
PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent
DATABASE_PATH: Final[Path] = PROJECT_ROOT / "pharmapos.db"
DB_PATH = DATABASE_PATH
LOGS_DIR: Final[Path] = PROJECT_ROOT / "logs"

# --- Database ---
DEFAULT_DB_FILENAME: Final[str] = "pharmapos.db"
SQLITE_PRAGMA_FOREIGN_KEYS: Final[bool] = True

# --- Authentication ---
SESSION_TIMEOUT_MINUTES: Final[int] = 60
PASSWORD_MIN_LENGTH: Final[int] = 6
PBKDF2_ITERATIONS: Final[int] = 100000

# --- User Roles ---
ROLE_ADMIN: Final[str] = "admin"
ROLE_MANAGER: Final[str] = "manager"
ROLE_CASHIER: Final[str] = "cashier"

VALID_ROLES: Final[list[str]] = [ROLE_ADMIN, ROLE_MANAGER, ROLE_CASHIER]

ROLE_HIERARCHY: Final[dict[str, int]] = {
    ROLE_ADMIN: 3,
    ROLE_MANAGER: 2,
    ROLE_CASHIER: 1,
}

# --- Payment Methods ---
PAYMENT_CASH: Final[str] = "cash"
PAYMENT_CARD: Final[str] = "card"
PAYMENT_TRANSFER: Final[str] = "transfer"
PAYMENT_PAYSTACK: Final[str] = "paystack"
PAYMENT_FLUTTERWAVE: Final[str] = "flutterwave"

VALID_PAYMENT_METHODS: Final[list[str]] = [
    PAYMENT_CASH,
    PAYMENT_CARD,
    PAYMENT_CARD,
    PAYMENT_TRANSFER,
    PAYMENT_PAYSTACK,
    PAYMENT_FLUTTERWAVE,
]

# --- Stock Transfer Status ---
TRANSFER_PENDING: Final[str] = "pending"
TRANSFER_RECEIVED: Final[str] = "received"

VALID_TRANSFER_STATUS: Final[list[str]] = [TRANSFER_PENDING, TRANSFER_RECEIVED]

# --- Inventory Change Types ---
CHANGE_SALE: Final[str] = "sale"
CHANGE_TRANSFER_OUT: Final[str] = "transfer_out"
CHANGE_TRANSFER_IN: Final[str] = "transfer_in"
CHANGE_ADJUSTMENT: Final[str] = "adjustment"
CHANGE_RECEIPT: Final[str] = "receipt"

VALID_CHANGE_TYPES: Final[list[str]] = [
    CHANGE_SALE,
    CHANGE_TRANSFER_OUT,
    CHANGE_TRANSFER_IN,
    CHANGE_ADJUSTMENT,
    CHANGE_RECEIPT,
]

# --- Alert Configuration ---
EXPIRY_WARNING_DAYS: Final[int] = 30
LOW_STOCK_THRESHOLD: Final[int] = 10

# --- Receipt Configuration ---
RECEIPT_PRINTER_WIDTH: Final[int] = 50
RECEIPT_LINE_SEPARATOR: Final[str] = "=" * RECEIPT_PRINTER_WIDTH

# --- Pricing ---
CURRENCY_SYMBOL: Final[str] = "₦"
DECIMAL_PLACES: Final[int] = 2

# --- UI Configuration ---
WINDOW_WIDTH: Final[int] = 1200
WINDOW_HEIGHT: Final[int] = 700
TABLE_ROW_HEIGHT: Final[int] = 30
FONT_SIZE_NORMAL: Final[int] = 10
FONT_SIZE_TITLE: Final[int] = 12

# --- Validation Rules ---
MIN_SELLING_PRICE: Final[Decimal] = Decimal("0.01")
MAX_INVENTORY_QTY: Final[int] = 999999
MIN_INVENTORY_QTY: Final[int] = 0

# --- Business Rules ---
ALLOW_NEGATIVE_INVENTORY: Final[bool] = False
AUTO_GENERATE_RECEIPT_NUMBER: Final[bool] = True
REQUIRE_BATCH_NUMBER: Final[bool] = True


def get_config() -> dict:
    """Get all configuration as dictionary."""
    return {
        "database": {
            "path": str(DATABASE_PATH),
            "default_filename": DEFAULT_DB_FILENAME,
            "pragma_foreign_keys": SQLITE_PRAGMA_FOREIGN_KEYS,
        },
        "auth": {
            "session_timeout_minutes": SESSION_TIMEOUT_MINUTES,
            "password_min_length": PASSWORD_MIN_LENGTH,
            "pbkdf2_iterations": PBKDF2_ITERATIONS,
        },
        "roles": {
            "valid": VALID_ROLES,
            "hierarchy": ROLE_HIERARCHY,
        },
        "payment": {
            "methods": VALID_PAYMENT_METHODS,
        },
        "alerts": {
            "expiry_warning_days": EXPIRY_WARNING_DAYS,
            "low_stock_threshold": LOW_STOCK_THRESHOLD,
        },
        "ui": {
            "window_width": WINDOW_WIDTH,
            "window_height": WINDOW_HEIGHT,
            "font_size_normal": FONT_SIZE_NORMAL,
            "font_size_title": FONT_SIZE_TITLE,
        },
        "ui": {
            "window_width": WINDOW_WIDTH,
            "window_height": WINDOW_HEIGHT,
            "font_size_normal": FONT_SIZE_NORMAL,
            "font_size_title": FONT_SIZE_TITLE,
        },
        "payment_gateways": {
            "paystack": {
                "public_key": os.environ.get("PAYSTACK_PUBLIC_KEY", "pk_test_..."),
                "secret_key": os.environ.get("PAYSTACK_SECRET_KEY", "sk_test_..."),
            },
            "flutterwave": {
                "public_key": os.environ.get("FLW_PUBLIC_KEY", "FLWPUBK_TEST-..."),
                "secret_key": os.environ.get("FLW_SECRET_KEY", "FLWSECK_TEST-..."),
            }
        }
    }


# --- Printer Configuration (Persistent) ---
CONFIG_FILE: Final[str] = str(PROJECT_ROOT / "config.json")


def load_printer_config() -> Dict[str, Any]:
    """Load printer configuration from config.json, or return defaults."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("printer", _default_printer_config())
        except Exception as e:
            print(f"Warning: Failed to load printer config: {e}")
    
    return _default_printer_config()


def save_printer_config(printer_config: Dict[str, Any]) -> bool:
    """Save printer configuration to config.json."""
    try:
        # Load existing config or create new
        full_config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                full_config = json.load(f)
        
        full_config["printer"] = printer_config
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(full_config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving printer config: {e}")
        return False


def _default_printer_config() -> Dict[str, Any]:
    """Return default printer configuration."""
    return {
        "enabled": False,
        "type": "FILE",  # FILE, USB, SERIAL, NETWORK, SYSTEM
        "usb": {
            "vendor_id": "0x04b8",
            "product_id": "0x0202",
        },
        "serial": {
            "port": "/dev/ttyUSB0",
            "baudrate": 9600,
        },
        "network": {
            "host": "192.168.1.100",
            "port": 9100,
        },
        "system": {
            "name": "",
        },
    }


def get_printer_backend() -> Optional[str]:
    """Get the configured printer backend type (or None if disabled)."""
    config = load_printer_config()
    if not config.get("enabled"):
        return None
    return config.get("type", "FILE")


def get_printer_device_info(printer_type: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Get device-specific printer info based on configured backend.

    Args:
        printer_type: Optional printer type override (USB/SERIAL/NETWORK/FILE/SYSTEM)
        config: Optional config dict to use (if not provided, load from file)

    Returns:
        dict of backend-specific parameters or None
    """
    if config is None:
        config = load_printer_config()

    backend = (printer_type or config.get("type", "FILE"))

    if backend == "USB":
        return config.get("usb", {})
    elif backend == "SERIAL":
        return config.get("serial", {})
    elif backend == "NETWORK":
        return config.get("network", {})
    elif backend == "SYSTEM":
        return config.get("system", {})

    return None


__all__ = [
    "PROJECT_ROOT",
    "DATABASE_PATH",
    "DB_PATH",
    "SESSION_TIMEOUT_MINUTES",
    "PASSWORD_MIN_LENGTH",
    "VALID_ROLES",
    "VALID_PAYMENT_METHODS",
    "EXPIRY_WARNING_DAYS",
    "LOW_STOCK_THRESHOLD",
    "CURRENCY_SYMBOL",
    "get_config",
    "load_printer_config",
    "save_printer_config",
    "get_printer_backend",
    "get_printer_device_info",
]
