"""
PharmaPOS NG - Core SQLite Database Schema (SQLAlchemy Core)

This module defines the core schema supporting multi-store operations,
batch-based pharmaceutical inventory tracking (FEFO), and proper foreign key
relationships with indexes for performance.

Usage:
    from desktop_app.database import init_db
    init_db()  # creates pharmapos.db with all tables and indexes
"""

from __future__ import annotations

import os
from typing import Optional

from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Date,
    DateTime,
    Numeric,
    ForeignKey,
    Index,
    MetaData,
    create_engine,
    event,
    func,
    text,
)


# --- Configuration -----------------------------------------------------------
DEFAULT_DB_FILENAME = "pharmapos.db"


def _db_url(db_path: Optional[str]) -> str:
    path = db_path or DEFAULT_DB_FILENAME
    # ensure directory exists if path includes folders
    directory = os.path.dirname(os.path.abspath(path))
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    return f"sqlite:///{path}"


# Global metadata for the schema
metadata = MetaData()


# --- Tables ------------------------------------------------------------------
# stores
stores = Table(
    "stores",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False, unique=True),
    Column("address", Text),
    Column("is_primary", Boolean, server_default=text("0"), nullable=False),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    ),
)

# Ensure only one primary store via partial unique index on is_primary = 1
Index(
    "idx_stores_only_one_primary",
    stores.c.is_primary,
    unique=True,
    sqlite_where=(stores.c.is_primary == True),  # type: ignore[comparison-overlap]
)


# users
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String, nullable=False, unique=True),
    Column("password_hash", String, nullable=False),
    Column("role", String, nullable=False),  # 'admin', 'manager', 'cashier'
    Column(
        "store_id",
        Integer,
        ForeignKey("stores.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    ),
    Column("is_active", Boolean, server_default=text("1"), nullable=False),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    ),
)


# products (master catalog)
products = Table(
    "products",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("generic_name", String),
    Column("sku", String, nullable=False, unique=True),
    Column("barcode", String, unique=True),
    Column("nafdac_number", String, nullable=False),
    Column("cost_price", Numeric(10, 2), nullable=False),
    Column("selling_price", Numeric(10, 2), nullable=False),
    Column("description", Text),
    Column("is_active", Boolean, server_default=text("1"), nullable=False),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    ),
)


# product_batches (critical for FEFO)
product_batches = Table(
    "product_batches",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "product_id",
        Integer,
        ForeignKey("products.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    ),
    Column(
        "store_id",
        Integer,
        ForeignKey("stores.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    ),
    Column("batch_number", String, nullable=False),
    Column("expiry_date", Date, nullable=False),
    Column("quantity", Integer, server_default=text("0"), nullable=False),
    Column("cost_price", Numeric(10, 2)),
    Column("received_date", DateTime, server_default=func.now(), nullable=False),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    ),
    # Optional: avoid duplicate batches per store/product
    # sqlalchemy.UniqueConstraint("product_id", "store_id", "batch_number", name="uq_batch_per_store_product"),
)


# sales
sales = Table(
    "sales",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("receipt_number", String, nullable=False, unique=True),
    Column("total_amount", Numeric(10, 2), nullable=False),
    Column("amount_paid", Numeric(10, 2), nullable=False),
    Column("payment_method", String, nullable=False),  # 'cash', 'card', 'transfer'
    Column("change_amount", Numeric(10, 2), server_default=text("0"), nullable=False),
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    ),
    Column(
        "store_id",
        Integer,
        ForeignKey("stores.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    ),
    Column("synced_to_cloud", Boolean, server_default=text("0"), nullable=False),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    ),
)


# sale_items
sale_items = Table(
    "sale_items",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "sale_id",
        Integer,
        ForeignKey("sales.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    ),
    Column(
        "product_batch_id",
        Integer,
        ForeignKey("product_batches.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    ),
    Column("quantity", Integer, nullable=False),
    Column("unit_price", Numeric(10, 2), nullable=False),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
)


# stock_transfers
stock_transfers = Table(
    "stock_transfers",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "product_id",
        Integer,
        ForeignKey("products.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    ),
    Column("batch_number", String, nullable=False),
    Column("quantity", Integer, nullable=False),
    Column(
        "from_store_id",
        Integer,
        ForeignKey("stores.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    ),
    Column(
        "to_store_id",
        Integer,
        ForeignKey("stores.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    ),
    Column("status", String, server_default=text("'pending'"), nullable=False),
    Column("transfer_date", DateTime, server_default=func.now(), nullable=False),
    Column("received_date", DateTime),
    Column("synced_to_cloud", Boolean, server_default=text("0"), nullable=False),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    ),
)


# inventory_audit (traceability)
inventory_audit = Table(
    "inventory_audit",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "product_batch_id",
        Integer,
        ForeignKey("product_batches.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    ),
    Column("previous_quantity", Integer, nullable=False),
    Column("new_quantity", Integer, nullable=False),
    Column("change_type", String, nullable=False),  # 'sale', 'transfer_out', 'transfer_in', 'adjustment', 'receipt'
    Column("reference_id", Integer),  # link to sale_id, transfer_id, etc.
    Column("notes", Text),
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    ),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
)


# --- New/Additive Tables for Inventory Features ------------------------------
suppliers = Table(
    "suppliers",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("contact", String),
    Column("address", Text),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
)

purchase_receipts = Table(
    "purchase_receipts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "supplier_id",
        Integer,
        ForeignKey("suppliers.id", ondelete="SET NULL", onupdate="CASCADE"),
    ),
    Column("store_id", Integer, ForeignKey("stores.id", ondelete="RESTRICT")),
    Column("receipt_number", String, nullable=False, unique=True),
    Column("total_amount", Numeric(10, 2), server_default=text("0")),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
)

purchase_receipt_items = Table(
    "purchase_receipt_items",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("receipt_id", Integer, ForeignKey("purchase_receipts.id", ondelete="CASCADE")),
    Column("product_id", Integer, ForeignKey("products.id", ondelete="RESTRICT")),
    Column("batch_number", String, nullable=False),
    Column("expiry_date", Date),
    Column("quantity", Integer, server_default=text("0")),
    Column("cost_price", Numeric(10, 2)),
)

stock_reservations = Table(
    "stock_reservations",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("product_id", Integer, ForeignKey("products.id", ondelete="RESTRICT")),
    Column("store_id", Integer, ForeignKey("stores.id", ondelete="RESTRICT")),
    Column("quantity", Integer, nullable=False),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="SET NULL")),
    Column("reserved_until", DateTime),
    Column("status", String, server_default=text("'active'")),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
)


# --- Required Indexes --------------------------------------------------------
Index(
    "idx_product_batches_store_expiry",
    product_batches.c.store_id,
    product_batches.c.expiry_date,
)
Index(
    "idx_product_batches_product_store",
    product_batches.c.product_id,
    product_batches.c.store_id,
)
Index("idx_sales_store_date", sales.c.store_id, sales.c.created_at)
Index("idx_sales_receipt", sales.c.receipt_number, unique=True)
Index("idx_products_sku_barcode", products.c.sku, products.c.barcode)


# --- Engine / Initialization -------------------------------------------------
def get_engine(db_path: Optional[str] = None):
    """Create or return a cached SQLite engine with foreign keys enabled.

    Engines are cached per DB path to allow controlled disposal (required
    on Windows to release file locks). Use `dispose_engine(db_path)` to
    free resources when done.
    """
    # Simple cache to reuse engines for the same DB path
    global _ENGINE_CACHE
    try:
        _ENGINE_CACHE
    except NameError:
        _ENGINE_CACHE = {}

    url = _db_url(db_path)
    if url in _ENGINE_CACHE:
        return _ENGINE_CACHE[url]

    engine = create_engine(url, future=True)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    _ENGINE_CACHE[url] = engine
    return engine


def dispose_engine(db_path: Optional[str] = None) -> None:
    """Dispose the cached engine for the given DB path (or all engines
    if db_path is None). This releases file handles on Windows.
    """
    global _ENGINE_CACHE
    try:
        _ENGINE_CACHE
    except NameError:
        _ENGINE_CACHE = {}

    if db_path is None:
        # Dispose all
        for eng in list(_ENGINE_CACHE.values()):
            try:
                eng.dispose()
            except Exception:
                pass
        _ENGINE_CACHE.clear()
        return

    url = _db_url(db_path)
    eng = _ENGINE_CACHE.pop(url, None)
    if eng:
        try:
            eng.dispose()
        except Exception:
            pass


def dispose_all_engines() -> None:
    """Convenience: dispose all cached engines."""
    dispose_engine(None)


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize the database by creating all tables and indexes.

    Args:
        db_path: Optional path to the SQLite database file. Defaults to 'pharmapos.db'.
    """
    engine = get_engine(db_path)
    metadata.create_all(engine)
    
    # Create default users if they don't exist
    _create_default_users(engine, db_path)
    
    print(f"Database initialized at: {engine.url}")


def _create_default_users(engine, db_path: Optional[str] = None) -> None:
    """Create default demo users if database is empty."""
    try:
        from desktop_app.auth import PasswordManager
        
        with engine.connect() as conn:
            # Check if users already exist
            user_count = conn.execute(
                text("SELECT COUNT(*) FROM users")
            ).scalar()
            
            if user_count == 0:
                # Create default store first
                conn.execute(
                    text("""
                        INSERT INTO stores (name, address, is_primary)
                        VALUES ('Main Pharmacy', 'Lagos, Nigeria', 1)
                    """)
                )
                conn.commit()
                
                # Get store ID
                store_id = conn.execute(
                    text("SELECT id FROM stores WHERE is_primary = 1")
                ).scalar()
                
                # Create default users
                admin_hash = PasswordManager.hash_password("admin123")
                conn.execute(
                    text("""
                        INSERT INTO users (username, password_hash, role, store_id, is_active)
                        VALUES (:username, :password_hash, :role, :store_id, 1)
                    """),
                    {
                        "username": "admin",
                        "password_hash": admin_hash,
                        "role": "admin",
                        "store_id": store_id,
                    }
                )
                
                manager_hash = PasswordManager.hash_password("manager123")
                conn.execute(
                    text("""
                        INSERT INTO users (username, password_hash, role, store_id, is_active)
                        VALUES (:username, :password_hash, :role, :store_id, 1)
                    """),
                    {
                        "username": "manager1",
                        "password_hash": manager_hash,
                        "role": "manager",
                        "store_id": store_id,
                    }
                )
                
                cashier_hash = PasswordManager.hash_password("cashier123")
                conn.execute(
                    text("""
                        INSERT INTO users (username, password_hash, role, store_id, is_active)
                        VALUES (:username, :password_hash, :role, :store_id, 1)
                    """),
                    {
                        "username": "cashier1",
                        "password_hash": cashier_hash,
                        "role": "cashier",
                        "store_id": store_id,
                    }
                )
                
                conn.commit()
    except Exception:
        # Silently fail if users already exist or on any error
        pass


__all__ = [
    "metadata",
    "get_engine",
    "init_db",
    "stores",
    "users",
    "products",
    "product_batches",
    "sales",
    "sale_items",
    "stock_transfers",
    "inventory_audit",
]