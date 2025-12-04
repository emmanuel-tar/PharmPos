# PharmaPOS NG - Comprehensive Inventory Management Specification

**Version**: 1.0  
**Date**: 2025-12-03  
**Status**: Implementation Phase 1 (Core APIs + DB Schema)

---

## Executive Summary

This specification defines a complete, production-ready inventory management system for PharmaPOS NG, a multi-store pharmaceutical POS system. The system enforces **FEFO (First Expire First Out)** discipline, supports batch tracking, stock reservations, inter-store transfers, write-offs, and provides full audit trails. All operations are transactional and logged for compliance and traceability.

---

## Core Business Requirements

1. **FEFO Enforcement**: Pharmaceutical regulations require expired stock to be removed from circulation. Sales must allocate nearest-expiry batches first.
2. **Batch Traceability**: Every unit of stock must be traceable to supplier, batch number, and expiry date for regulatory compliance.
3. **Multi-Store Operations**: Support centralized inventory across multiple pharmacy locations with inter-store transfers.
4. **Stock Safety**: Prevent overselling (no negative quantities), protect expired stock, and flag expiring items.
5. **Audit Trail**: Every inventory transaction must be immutably logged for compliance audits.
6. **Concurrency Safety**: Support simultaneous sales and stock receipts without data corruption.

---

## Core Concepts

### Product & Batch
- **Product**: Master catalog item with SKU, barcode, NAFDAC number, cost/selling prices.
- **Product Batch**: Individual stock lot with batch number, expiry date, quantity, cost price, received date.
- **Stock Reserve**: Temporary hold on quantity for pending sale, QC review, or inter-store transfer.

### FEFO Algorithm
When allocating stock for a sale:
1. Query all batches for the product in the store with `quantity > 0`.
2. Order by `expiry_date ASC` (nearest expiry first).
3. Allocate sequentially from each batch until required quantity is met.
4. If insufficient stock, return partial allocation and suggest backorder.

### Audit Trail
Every inventory mutation creates an immutable `inventory_audit` record with:
- `product_batch_id`, `previous_quantity`, `new_quantity`
- `change_type` (sale, receipt, adjustment, expired, transfer_out, transfer_in, etc.)
- `user_id`, `created_at`, `reference_id` (link to sale, transfer, etc.)
- `notes` (reason for change)

---

## Database Schema

### Existing Tables (Extended)
- **product_batches**: Existing table extended with indexes on `store_id`, `expiry_date`, and `product_id`.

### New Tables

#### `suppliers`
```sql
CREATE TABLE suppliers (
    id INTEGER PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    contact_person VARCHAR,
    email VARCHAR,
    phone VARCHAR,
    address TEXT,
    payment_terms VARCHAR,  -- e.g., 'Net 30', 'COD'
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

#### `purchase_receipts`
Links suppliers to received stock batches:
```sql
CREATE TABLE purchase_receipts (
    id INTEGER PRIMARY KEY,
    supplier_id INTEGER NOT NULL,
    reference_number VARCHAR UNIQUE,  -- supplier invoice/PO number
    store_id INTEGER NOT NULL,
    total_amount NUMERIC(10, 2),
    received_date DATETIME,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (store_id) REFERENCES stores(id)
);
```

#### `stock_reservations`
Temporary holds on batches for pending sales or QC:
```sql
CREATE TABLE stock_reservations (
    id INTEGER PRIMARY KEY,
    product_batch_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    reason VARCHAR,  -- 'pending_sale', 'qa_review', 'hold', etc.
    status VARCHAR DEFAULT 'active' NOT NULL,  -- 'active', 'released', 'confirmed'
    user_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (product_batch_id) REFERENCES product_batches(id) ON DELETE RESTRICT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    UNIQUE (product_batch_id, reason, status)  -- Prevent duplicate active holds
);
```

#### `stock_adjustments`
Manual adjustments (damage, loss, corrections):
```sql
CREATE TABLE stock_adjustments (
    id INTEGER PRIMARY KEY,
    product_batch_id INTEGER NOT NULL,
    previous_quantity INTEGER NOT NULL,
    new_quantity INTEGER NOT NULL,
    reason VARCHAR NOT NULL,  -- 'damage', 'loss', 'obsolete', 'correction', etc.
    notes TEXT,
    user_id INTEGER NOT NULL,
    approved_by INTEGER,  -- Manager/admin approval
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (product_batch_id) REFERENCES product_batches(id) ON DELETE RESTRICT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
);
```

#### `backorders`
Unfulfilled demand that can be fulfilled when stock arrives:
```sql
CREATE TABLE backorders (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    store_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    customer_id INTEGER,
    status VARCHAR DEFAULT 'pending' NOT NULL,  -- 'pending', 'partial', 'fulfilled', 'cancelled'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fulfilled_date DATETIME,
    notes TEXT,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT,
    FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE RESTRICT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
);
```

#### `inventory_reconciliations`
Physical count reconciliation records:
```sql
CREATE TABLE inventory_reconciliations (
    id INTEGER PRIMARY KEY,
    store_id INTEGER NOT NULL,
    reconciliation_date DATETIME NOT NULL,
    total_variance_qty INTEGER,  -- Sum of all variances
    notes TEXT,
    user_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE RESTRICT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
);
```

#### `reconciliation_items`
Detail variances per batch:
```sql
CREATE TABLE reconciliation_items (
    id INTEGER PRIMARY KEY,
    reconciliation_id INTEGER NOT NULL,
    product_batch_id INTEGER NOT NULL,
    system_quantity INTEGER NOT NULL,
    counted_quantity INTEGER NOT NULL,
    variance_quantity INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (reconciliation_id) REFERENCES inventory_reconciliations(id) ON DELETE CASCADE,
    FOREIGN KEY (product_batch_id) REFERENCES product_batches(id) ON DELETE RESTRICT
);
```

### Indexes
```sql
-- For FEFO allocation queries
CREATE INDEX idx_product_batches_store_expiry 
    ON product_batches(store_id, expiry_date) WHERE quantity > 0;

-- For supplier reporting
CREATE INDEX idx_purchase_receipts_supplier_date 
    ON purchase_receipts(supplier_id, received_date);

-- For reconciliation lookups
CREATE INDEX idx_stock_adjustments_batch_date 
    ON stock_adjustments(product_batch_id, created_at);
```

---

## Service Layer APIs

### InventoryService

#### **receive_stock(product_id, store_id, batch_number, quantity, expiry_date, cost_price, supplier_id, reference_number, notes, user_id) → dict**
Record receipt of new stock from a supplier.
```python
# Args
product_id: int
store_id: int
batch_number: str
quantity: int  # Must be > 0
expiry_date: date
cost_price: Decimal
supplier_id: int
reference_number: Optional[str]  # Purchase order or invoice number
notes: Optional[str]
user_id: int

# Returns
{
    'batch_id': int,
    'product_id': int,
    'store_id': int,
    'batch_number': str,
    'quantity': int,
    'expiry_date': date,
    'cost_price': float
}

# Audit Entry
change_type='receipt', reference_id=batch_id
```

#### **allocate_stock_for_sale(product_id, store_id, quantity, user_id, reference_id=None) → dict**
Allocate stock for a sale using FEFO (First Expire First Out).
```python
# Args
product_id: int
store_id: int
quantity: int
user_id: int
reference_id: Optional[int]  # sale_id or backorder_id

# Returns
{
    'allocated_quantity': int,
    'batches': [
        {'batch_id': int, 'quantity': int, 'expiry_date': date},
        ...
    ],
    'partial': bool,  # True if less than requested
    'shortage': int   # Unmet demand
}

# Audit Entries (one per batch)
change_type='allocated', reference_id=reference_id or sale_id
```

#### **reserve_stock(product_batch_id, quantity, reason, user_id) → dict**
Reserve (hold) a quantity on a specific batch.
```python
# Args
product_batch_id: int
quantity: int
reason: str  # 'pending_sale', 'qa_review', 'hold'
user_id: int

# Returns
{'reservation_id': int, 'product_batch_id': int, 'quantity': int, 'reason': str}

# Audit Entry
change_type='reserved', reference_id=reservation_id
```

#### **release_reservation(reservation_id, user_id) → bool**
Release a reservation, returning quantity to available stock.
```python
# Audit Entry
change_type='release', reference_id=reservation_id
```

#### **confirm_reservation(reservation_id, user_id, reference_id=None) → bool**
Confirm a reservation and deduct as sale.
```python
# Args
reservation_id: int
user_id: int
reference_id: Optional[int]  # sale_id

# Audit Entry
change_type='confirm_reserve', reference_id=reference_id
```

#### **adjust_stock(batch_id, quantity_change, reason, user_id, notes="") → bool**
Adjust batch quantity (positive or negative).
```python
# Args
batch_id: int
quantity_change: int  # Positive or negative
reason: str  # 'damage', 'loss', 'correction'
user_id: int
notes: Optional[str]

# Audit Entry
change_type='adjustment', reference_id=adjustment_id
```

#### **writeoff_batch(batch_id, reason, user_id, notes="") → bool**
Write off an entire batch (set quantity to 0).
```python
# Audit Entry
change_type='writeoff', reference_id=adjustment_id
```

#### **expire_batches_within_days(store_id, days, user_id) → int**
Automatically expire batches expiring within N days.
```python
# Returns: count of batches expired

# Audit Entries (one per batch)
change_type='expired'
```

#### **get_expiring_batches(store_id, days=30) → List[dict]**
Retrieve batches expiring within N days (for alerts).
```python
# Returns: [{'batch_id', 'product_id', 'expiry_date', 'quantity', ...}, ...]
```

#### **get_expired_batches(store_id) → List[dict]**
Retrieve already-expired batches still in system.

#### **reconcile_inventory(store_id, counts_data, user_id, notes="") → dict**
Compare physical inventory counts against system records.
```python
# Args
store_id: int
counts_data: List[{'product_id': int, 'batch_id': int, 'counted_qty': int}, ...]
user_id: int
notes: Optional[str]

# Returns
{
    'reconciliation_id': int,
    'total_variance': int,
    'adjustments': [adjustment_ids],
    'variances': [
        {'batch_id', 'system_qty', 'counted_qty', 'variance'},
        ...
    ]
}

# Audit Entries (one per variance)
change_type='reconciliation'
```

#### **get_store_inventory(store_id) → List[dict]**
Get all active batches in store, ordered by expiry date (FEFO).
```python
# Returns: [{'batch_id', 'product_id', 'quantity', 'expiry_date', ...}, ...]
```

#### **get_product_stock(product_id, store_id) → int**
Get total available quantity for a product in a store.

---

### StockTransferService

#### **initiate_transfer(from_store_id, to_store_id, product_id, batch_number, quantity, user_id) → dict**
Create a pending inter-store stock transfer.
```python
# Returns
{'transfer_id': int, 'status': 'pending', 'quantity': int}

# Audit Entry
change_type='transfer_out'
```

#### **receive_transfer(transfer_id, received_quantity, user_id) → bool**
Receive a transfer at destination store.
```python
# Audit Entry
change_type='transfer_in'
```

#### **get_pending_transfers(store_id) → List[dict]**
Get pending transfers awaiting receipt at a store.

---

### BackorderService (Optional)

#### **create_backorder(product_id, store_id, quantity, customer_id, notes, user_id) → dict**
Create a backorder for unfulfilled demand.
```python
# Returns
{'backorder_id': int, 'status': 'pending', 'quantity': int}

# Audit Entry
change_type='backorder_created'
```

#### **fulfill_backorder(backorder_id, fulfilled_quantity, user_id) → bool**
Fulfill (partially or fully) a backorder when stock arrives.
```python
# Updates backorder status to 'partial' or 'fulfilled'

# Audit Entry
change_type='backorder_fulfilled'
```

---

## Transaction & Concurrency Guarantees

### Atomicity
All multi-step operations are wrapped in database transactions:
- **Sale Allocation**: Fetch eligible batches, allocate, create audit entries → all-or-nothing.
- **Transfer**: Deduct from source, add to destination → atomic.
- **Reconciliation**: Create reconciliation record, adjust variances → atomic.

### Isolation
- SQLAlchemy sessions use isolation level appropriate to the database.
- SQLite (development): Deferred transactions minimize lock contention.
- Production DB (PostgreSQL/MySQL): Configure isolation level per deployment requirements.

### Consistency
- All mutations update `inventory_audit` immutably.
- Audit records are never modified; corrections are new entries.
- Foreign key constraints prevent orphaned records.

### Concurrency Control
- **Optimistic**: Validate sufficient quantity at allocation time; fail if insufficient (no retry).
- **Pessimistic** (optional): For high-concurrency, add version field to `product_batches` for optimistic locking or use explicit row locks in production DB.

---

## Business Rules & Constraints

1. **No Negative Stock**: Batches cannot have negative quantities; operations that would violate this constraint fail immediately.
2. **Expiry Immutability**: Batches with `expiry_date < today` are not available for allocation (queries exclude them).
3. **Batch Uniqueness**: Duplicate batch numbers per store/product are prevented (optional UNIQUE constraint).
4. **Supplier Traceability**: All receipts must link to a supplier; orphaned receipts are prevented.
5. **Audit Immutability**: Audit records have no UPDATE/DELETE; corrections are new entries.
6. **Role-Based Approval**: Only managers/admins can approve adjustments > threshold (enforced in UI/API).
7. **Reservation TTL**: Reservations expire after a configurable time or conversion to sale (business rule, not DB-enforced).

---

## Implementation Phases

### Phase 1: Core Functionality (Current)
- [x] DB schema creation (suppliers, purchase_receipts, stock_adjustments, reconciliations, backorders).
- [x] InventoryService APIs: receive_stock, allocate_stock_for_sale, adjust_stock, writeoff_batch, expire_batches_within_days.
- [ ] Basic audit trail logging for all operations.
- [ ] Unit tests for allocation, FEFO ordering, and expiry.

### Phase 2: Advanced Inventory
- [ ] Reservation workflows (reserve, release, confirm).
- [ ] Reconciliation workflow with variance detection.
- [ ] Backorder creation and fulfillment.
- [ ] Inter-store transfer workflow.

### Phase 3: UI & Alerts
- [ ] Receiving form (supplier, batch, expiry, cost).
- [ ] Batch list with FEFO sorting and expiry highlighting.
- [ ] Expiry alerts and auto-expire scheduled job.
- [ ] Adjustment/write-off approval UI.

### Phase 4: Reporting & Analytics
- [ ] Stock valuation report (total inventory cost).
- [ ] Batch aging report (slow movers).
- [ ] Expiry risk report (7-day, 14-day, 30-day warnings).
- [ ] Transfer and adjustment logs.

### Phase 5: Performance & Production Hardening
- [ ] Query optimization and index tuning.
- [ ] Concurrency testing and load testing.
- [ ] Backup/recovery procedures.
- [ ] Migration scripts for existing deployments.

---

## Testing Strategy

### Unit Tests
- `test_fefo_allocation`: Verify batches allocated in expiry order.
- `test_partial_allocation`: Verify shortage flag when insufficient stock.
- `test_writeoff_batch`: Verify quantity set to 0 and audit logged.
- `test_adjust_stock`: Verify positive/negative adjustments.
- `test_reserve_release`: Verify reservation state machine.

### Integration Tests
- `test_receipt_to_sale`: Receive stock → allocate for sale → verify audit trail.
- `test_transfer_workflow`: Initiate transfer → receive transfer → verify both stores' inventory.
- `test_reconciliation`: Physical count → reconcile → verify adjustments created.

### Concurrency Tests
- Simulate 10 concurrent sales on same batch; verify consistency.
- Simulate receipt + sale on same batch; verify FEFO order.

---

## Rollout & Migration

### Pre-Deployment Checks
- [ ] Backup production DB.
- [ ] DB schema migration applied to staging DB; verify no errors.
- [ ] Data migration (seed suppliers, map existing batches).
- [ ] Service APIs tested in staging.
- [ ] Audit trail logging verified.

### Deployment Steps
1. Run DB schema migration on production.
2. Seed default suppliers and demo data.
3. Deploy updated application code (models.py, services).
4. Enable new UI forms (receiving, adjustments).
5. Operator training on new workflows.
6. Monitor audit trail logs for anomalies.

### Rollback Plan
- Restore DB from backup if critical issues arise.
- Disable new inventory UI features, fall back to simple stock entry.

---

## Operator Procedures

### Receiving Stock
1. Open "Receiving" form.
2. Select Supplier.
3. Enter Batch Number, Quantity, Expiry Date, Cost Price.
4. Submit; batch added to system and audit logged.

### Processing Sales
1. Scan/select products in cart.
2. System allocates stock using FEFO (transparent to cashier).
3. Confirm payment; sale committed, inventory deducted, audit logged.

### Adjusting Stock
1. Open "Stock Adjustment" form.
2. Select batch, enter quantity change, reason.
3. Submit for approval (manager/admin).
4. Upon approval, adjustment committed, audit logged.

### Physical Count & Reconciliation
1. Conduct physical count of all batches.
2. Open "Reconciliation" form, enter counts.
3. System compares against system records, generates variance report.
4. Review variances; auto-create adjustments for each.
5. Submit reconciliation; audit logged.

---

## Glossary

- **FEFO**: First Expire First Out; allocation algorithm prioritizing nearest-expiry batches.
- **GRN**: Goods Receipt Note; document accompanying stock receipt.
- **Batch**: Physical inventory lot with batch number and expiry date.
- **Reservation**: Temporary hold on stock quantity without actual deduction.
- **Backorder**: Unfulfilled customer demand to be fulfilled when stock arrives.
- **Write-off**: Permanent removal of expired or damaged stock from inventory.
- **Reconciliation**: Physical count verification against system records.
- **Audit Trail**: Immutable log of all inventory mutations.
- **Transfer**: Inter-store stock movement.

---
Generated: Automated change — implement basic schema and service APIs next.
