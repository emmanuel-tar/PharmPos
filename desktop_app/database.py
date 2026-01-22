import os
import uuid
from datetime import datetime, date
from typing import Optional, List

from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    Text,
    Numeric,
    func,
    text,
    Index,
    event,
)
from sqlalchemy.orm import sessionmaker, scoped_session

from desktop_app.config import DB_PATH

# Global metadata
metadata = MetaData()

# Helper for DB URL
def _db_url(db_path: Optional[str] = None) -> str:
    path = db_path or DB_PATH
    return f"sqlite:///{path}"


# --- Core Tables -------------------------------------------------------------

# stores (branches)
stores = Table(
    "stores",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("address", Text),
    Column("phone", String),
    Column("email", String),
    Column("is_primary", Boolean, server_default=text("0"), nullable=False),
    Column("is_active", Boolean, server_default=text("1"), nullable=False),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    ),
    # Sync columns
    Column("sync_id", String, unique=True, nullable=True),
    Column("sync_status", String, server_default=text("'pending'"), nullable=False),
    Column("last_synced_at", DateTime, nullable=True),
    Column("is_deleted", Boolean, server_default=text("0"), nullable=False),
)

# Unique constraint for primary store (only one primary store allowed ideally, 
# but SQLite partial indexes are tricky in older versions, so we enforce in logic or simple unique if possible.
# For now, we'll just index is_primary for quick lookup)
Index("idx_stores_is_primary", stores.c.is_primary)


# users (staff)
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
    # Sync columns
    Column("sync_id", String, unique=True, nullable=True),
    Column("sync_status", String, server_default=text("'pending'"), nullable=False),
    Column("last_synced_at", DateTime, nullable=True),
    Column("is_deleted", Boolean, server_default=text("0"), nullable=False),
)


# products (master catalog)
products = Table(
    "products",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("sku", String, unique=True, nullable=False),
    Column("barcode", String, unique=True, nullable=True),
    Column("description", Text),
    Column("category", String),
    Column("generic_name", String),
    Column("cost_price", Numeric(10, 2), nullable=False),
    Column("selling_price", Numeric(10, 2), nullable=False), # Base selling price
    Column("retail_price", Numeric(10, 2)), # Override
    Column("wholesale_price", Numeric(10, 2)),
    Column("wholesale_quantity", Integer),
    Column("bulk_price", Numeric(10, 2)),
    Column("bulk_quantity", Integer),
    Column("min_stock", Integer, server_default=text("0")),
    Column("max_stock", Integer, server_default=text("9999")),
    Column("reorder_level", Integer),
    Column("nafdac_number", String),
    Column("is_active", Boolean, server_default=text("1"), nullable=False),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    ),
    # Sync columns
    Column("sync_id", String, unique=True, nullable=True),
    Column("sync_status", String, server_default=text("'pending'"), nullable=False),
    Column("last_synced_at", DateTime, nullable=True),
    Column("is_deleted", Boolean, server_default=text("0"), nullable=False),
)

# product_batches (inventory per store/batch)
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
    Column("quantity", Integer, server_default=text("0"), nullable=False),
    Column("expiry_date", Date),
    Column("cost_price", Numeric(10, 2)), # Batch specific cost
    Column("retail_price", Numeric(10, 2)), # Batch specific price override
    Column("wholesale_price", Numeric(10, 2)),
    Column("wholesale_quantity", Integer),
    Column("bulk_price", Numeric(10, 2)),
    Column("bulk_quantity", Integer),
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
    # Sync columns
    Column("sync_id", String, unique=True, nullable=True),
    Column("sync_status", String, server_default=text("'pending'"), nullable=False),
    Column("last_synced_at", DateTime, nullable=True),
    Column("is_deleted", Boolean, server_default=text("0"), nullable=False),
)


# sales
sales = Table(
    "sales",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("receipt_number", String, nullable=False, unique=True),
    Column("total_amount", Numeric(10, 2), nullable=False),
    Column("amount_paid", Numeric(10, 2), nullable=False),
    Column("payment_method", String, nullable=False),  # 'cash', 'card', 'transfer', 'paystack', 'flutterwave'
    Column("payment_reference", String, nullable=True),
    Column("gateway_response", Text, nullable=True),
    Column("change_amount", Numeric(10, 2), server_default=text("0"), nullable=False),
    Column(
        "customer_id",
        Integer,
        ForeignKey("customers.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    ),
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
    # Sync columns
    Column("sync_id", String, unique=True, nullable=True),
    Column("sync_status", String, server_default=text("'pending'"), nullable=False),
    Column("last_synced_at", DateTime, nullable=True),
    Column("is_deleted", Boolean, server_default=text("0"), nullable=False),
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
    # Sync columns
    Column("sync_id", String, unique=True, nullable=True),
    Column("sync_status", String, server_default=text("'pending'"), nullable=False),
    Column("last_synced_at", DateTime, nullable=True),
    Column("is_deleted", Boolean, server_default=text("0"), nullable=False),
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
    # Sync columns
    Column("sync_id", String, unique=True, nullable=True),
    Column("sync_status", String, server_default=text("'pending'"), nullable=False),
    Column("last_synced_at", DateTime, nullable=True),
    Column("is_deleted", Boolean, server_default=text("0"), nullable=False),
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
    Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    ),
    # Sync columns
    Column("sync_id", String, unique=True, nullable=True),
    Column("sync_status", String, server_default=text("'pending'"), nullable=False),
    Column("last_synced_at", DateTime, nullable=True),
    Column("is_deleted", Boolean, server_default=text("0"), nullable=False),
)


# purchase_orders
purchase_orders = Table(
    "purchase_orders",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("po_number", String, nullable=False, unique=True),
    Column(
        "supplier_id",
        Integer,
        ForeignKey("suppliers.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    ),
    Column(
        "store_id",
        Integer,
        ForeignKey("stores.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    ),
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    ),
    Column("total_expected_amount", Numeric(10, 2), server_default=text("0")),
    Column("status", String, server_default=text("'draft'"), nullable=False),  # 'draft', 'approved', 'ordered', 'received', 'cancelled'
    Column("expected_delivery_date", Date),
    Column("actual_delivery_date", Date),
    Column("notes", Text),
    Column("approved_by", Integer, ForeignKey("users.id", ondelete="SET NULL")),
    Column("approved_at", DateTime),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    ),
    # Sync columns
    Column("sync_id", String, unique=True, nullable=True),
    Column("sync_status", String, server_default=text("'pending'"), nullable=False),
    Column("last_synced_at", DateTime, nullable=True),
    Column("is_deleted", Boolean, server_default=text("0"), nullable=False),
)

# purchase_order_items
purchase_order_items = Table(
    "purchase_order_items",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "purchase_order_id",
        Integer,
        ForeignKey("purchase_orders.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    ),
    Column(
        "product_id",
        Integer,
        ForeignKey("products.id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    ),
    Column("quantity_ordered", Integer, nullable=False),
    Column("quantity_received", Integer, server_default=text("0")),
    Column("expected_cost_price", Numeric(10, 2)),
    Column("notes", Text),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
)

purchase_receipts = Table(
    "purchase_receipts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "purchase_order_id",
        Integer,
        ForeignKey("purchase_orders.id", ondelete="SET NULL", onupdate="CASCADE"),
    ),
    Column(
        "product_id",
        Integer,
        ForeignKey("products.id", ondelete="RESTRICT", onupdate="CASCADE"),
    ),
    Column(
        "batch_id",
        Integer,
        ForeignKey("product_batches.id", ondelete="RESTRICT", onupdate="CASCADE"),
    ),
    Column("received_quantity", Integer, server_default=text("0")),
    Column("actual_cost_price", Numeric(10, 2)),
    Column("received_date", DateTime, server_default=func.now()),
    Column(
        "received_by",
        Integer,
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
    ),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    ),
    # Sync columns
    Column("sync_id", String, unique=True, nullable=True),
    Column("sync_status", String, server_default=text("'pending'"), nullable=False),
    Column("last_synced_at", DateTime, nullable=True),
    Column("is_deleted", Boolean, server_default=text("0"), nullable=False),
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
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
)


stock_reservations = Table(
    "stock_reservations",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("product_batch_id", Integer, ForeignKey("product_batches.id", ondelete="RESTRICT")),
    Column("quantity", Integer, nullable=False),
    Column("reason", String),  # 'pending_sale', 'qa_review', 'hold'
    Column("status", String, server_default=text("'active'")),  # 'active', 'released', 'confirmed'
    Column("user_id", Integer, ForeignKey("users.id", ondelete="SET NULL")),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    ),
    # Sync columns
    Column("sync_id", String, unique=True, nullable=True),
    Column("sync_status", String, server_default=text("'pending'"), nullable=False),
    Column("last_synced_at", DateTime, nullable=True),
    Column("is_deleted", Boolean, server_default=text("0"), nullable=False),
)


# stock_adjustments (manual adjustments, damage, loss, corrections)
stock_adjustments = Table(
    "stock_adjustments",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "product_batch_id",
        Integer,
        ForeignKey("product_batches.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("previous_quantity", Integer, nullable=False),
    Column("new_quantity", Integer, nullable=False),
    Column("reason", String, nullable=False),  # 'damage', 'loss', 'obsolete', 'correction'
    Column("notes", Text),
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("approved_by", Integer, ForeignKey("users.id", ondelete="SET NULL")),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    ),
    # Sync columns
    Column("sync_id", String, unique=True, nullable=True),
    Column("sync_status", String, server_default=text("'pending'"), nullable=False),
    Column("last_synced_at", DateTime, nullable=True),
    Column("is_deleted", Boolean, server_default=text("0"), nullable=False),
)


# backorders (unfulfilled demand)
backorders = Table(
    "backorders",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "product_id",
        Integer,
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "store_id",
        Integer,
        ForeignKey("stores.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("quantity_requested", Integer, nullable=False),
    Column("customer_name", String),
    Column("contact_info", String),
    Column("notes", Text),
    Column("status", String, server_default=text("'pending'")),  # 'pending', 'fulfilled', 'cancelled'
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
    ),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    ),
    # Sync columns
    Column("sync_id", String, unique=True, nullable=True),
    Column("sync_status", String, server_default=text("'pending'"), nullable=False),
    Column("last_synced_at", DateTime, nullable=True),
    Column("is_deleted", Boolean, server_default=text("0"), nullable=False),
)


# customers (customer database)
customers = Table(
    "customers",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("phone", String, nullable=False),
    Column("email", String),
    Column("address", Text),
    Column("loyalty_points", Integer, server_default=text("0"), nullable=False),
    Column("total_purchases", Numeric(10, 2), server_default=text("0"), nullable=False),
    Column("last_purchase_date", DateTime),
    Column("is_active", Boolean, server_default=text("1"), nullable=False),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    ),
    # Sync columns
    Column("sync_id", String, unique=True, nullable=True),
    Column("sync_status", String, server_default=text("'pending'"), nullable=False),
    Column("last_synced_at", DateTime, nullable=True),
    Column("is_deleted", Boolean, server_default=text("0"), nullable=False),
)

Index("idx_customers_phone", customers.c.phone)
Index("idx_customers_name", customers.c.name)


# inventory_reconciliations (stock taking)
inventory_reconciliations = Table(
    "inventory_reconciliations",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "store_id",
        Integer,
        ForeignKey("stores.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("status", String, server_default=text("'in_progress'")),  # 'in_progress', 'completed', 'cancelled'
    Column("started_at", DateTime, server_default=func.now(), nullable=False),
    Column("completed_at", DateTime),
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("notes", Text),
    Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    ),
    # Sync columns
    Column("sync_id", String, unique=True, nullable=True),
    Column("sync_status", String, server_default=text("'pending'"), nullable=False),
    Column("last_synced_at", DateTime, nullable=True),
    Column("is_deleted", Boolean, server_default=text("0"), nullable=False),
)


# reconciliation_items
reconciliation_items = Table(
    "reconciliation_items",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "reconciliation_id",
        Integer,
        ForeignKey("inventory_reconciliations.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "product_batch_id",
        Integer,
        ForeignKey("product_batches.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("system_quantity", Integer, nullable=False),
    Column("counted_quantity", Integer, nullable=False),
    Column("difference", Integer, nullable=False),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    # Sync columns
    Column("sync_id", String, unique=True, nullable=True),
    Column("sync_status", String, server_default=text("'pending'"), nullable=False),
    Column("last_synced_at", DateTime, nullable=True),
    Column("is_deleted", Boolean, server_default=text("0"), nullable=False),
)


# activity_logs (audit trail for user actions)
activity_logs = Table(
    "activity_logs",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    ),
    Column("username", String, nullable=False),  # Denormalized for historical record
    Column("action", String, nullable=False),  # 'login', 'logout', 'sale', 'stock_add', 'user_create', etc.
    Column("entity_type", String),  # 'sale', 'product', 'user', 'stock', etc.
    Column("entity_id", Integer),  # ID of affected entity
    Column("details", Text),  # JSON or text description of the action
    Column("ip_address", String),
    Column("store_id", Integer, ForeignKey("stores.id", ondelete="SET NULL")),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
)

Index("idx_activity_logs_user", activity_logs.c.user_id)
Index("idx_activity_logs_action", activity_logs.c.action)
Index("idx_activity_logs_created", activity_logs.c.created_at)


# system_settings (configuration storage)
system_settings = Table(
    "system_settings",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("key", String, nullable=False, unique=True),
    Column("value", Text),  # JSON or plain text
    Column("category", String),  # 'tax', 'business', 'receipt', 'printer', 'general'
    Column("description", Text),
    Column("data_type", String, server_default=text("'string'")),  # 'string', 'number', 'boolean', 'json'
    Column("updated_by", Integer, ForeignKey("users.id", ondelete="SET NULL")),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    ),
)

Index("idx_settings_key", system_settings.c.key, unique=True)
Index("idx_settings_category", system_settings.c.category)


# compliance_alerts (NAFDAC, PCN, expiry notifications)
compliance_alerts = Table(
    "compliance_alerts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("alert_type", String, nullable=False),  # 'expiry', 'stock_discrepancy', 'nafdac', 'pcn'
    Column("severity", String, server_default=text("'medium'")),  # 'low', 'medium', 'high', 'critical'
    Column("title", String, nullable=False),
    Column("message", Text, nullable=False),
    Column("entity_type", String),  # 'product', 'batch', 'store'
    Column("entity_id", Integer),
    Column("store_id", Integer, ForeignKey("stores.id", ondelete="CASCADE")),
    Column("is_resolved", Boolean, server_default=text("0"), nullable=False),
    Column("resolved_at", DateTime),
    Column("resolved_by", Integer, ForeignKey("users.id", ondelete="SET NULL")),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    ),
)

Index("idx_compliance_alerts_type", compliance_alerts.c.alert_type)
Index("idx_compliance_alerts_severity", compliance_alerts.c.severity)
Index("idx_compliance_alerts_resolved", compliance_alerts.c.is_resolved)


# sync_logs
sync_logs = Table(
    "sync_logs",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("table_name", String, nullable=False),
    Column("record_id", Integer, nullable=False),
    Column("action", String, nullable=False),  # 'insert', 'update', 'delete'
    Column("sync_id", String, nullable=True),
    Column("timestamp", DateTime, server_default=func.now(), nullable=False),
    Column("status", String, nullable=False),  # 'success', 'failed'
    Column("error_message", Text),
    Column("retry_count", Integer, server_default=text("0")),
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
    "dispose_engine",
    "dispose_all_engines",
    "stores",
    "users",
    "products",
    "product_batches",
    "sales",
    "sale_items",
    "stock_transfers",
    "inventory_audit",
    "suppliers",
    "purchase_orders",
    "purchase_order_items",
    "purchase_receipts",
    "purchase_receipt_items",
    "stock_reservations",
    "stock_adjustments",
    "backorders",
    "inventory_reconciliations",
    "reconciliation_items",
    "activity_logs",
    "system_settings",
    "compliance_alerts",
    "sync_logs",
    "customers",
]
