"""
PharmaPOS NG - Configuration Settings

Centralized configuration for the application.
"""

from pathlib import Path
from decimal import Decimal
from typing import Final

# --- File Paths ---
PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent
DATABASE_PATH: Final[Path] = PROJECT_ROOT / "pharmapos.db"
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

VALID_PAYMENT_METHODS: Final[list[str]] = [
    PAYMENT_CASH,
    PAYMENT_CARD,
    PAYMENT_TRANSFER,
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
    }


__all__ = [
    "PROJECT_ROOT",
    "DATABASE_PATH",
    "SESSION_TIMEOUT_MINUTES",
    "PASSWORD_MIN_LENGTH",
    "VALID_ROLES",
    "VALID_PAYMENT_METHODS",
    "EXPIRY_WARNING_DAYS",
    "LOW_STOCK_THRESHOLD",
    "CURRENCY_SYMBOL",
    "get_config",
]
