# Inventory Feature Specification

This document defines the initial inventory feature set for PharmPos.

## Goals
- Support batch-level stock tracking (FEFO) for pharmaceutical products.
- Support receiving (GRN), reservations for sales, transfers between stores, write-offs, and reconciliations.
- Maintain audit trail for all stock mutations.

## Core Concepts
- Product: master catalog item (table: `products`).
- Product Batch: physical stock unit with `batch_number`, `expiry_date`, `quantity`, `store_id` (table: `product_batches`).
- FEFO: selection algorithm that chooses batches ordered by `expiry_date` ascending.
- Inventory Audit: logs every mutation to `product_batches` (table: `inventory_audit`).
- Reservation: short-lived hold on quantity for pending sales (table: `stock_reservations`).

## New Tables (summary)
- `suppliers`: id, name, contact, address, created_at
- `purchase_receipts`: id, supplier_id, store_id, receipt_number, total_amount, created_at
- `purchase_receipt_items`: id, receipt_id, product_id, batch_number, quantity, cost_price, expiry_date
- `stock_reservations`: id, product_id, store_id, quantity, user_id, reserved_until, status, created_at

These are additive tables and will be created by `metadata.create_all(engine)` in the current bootstrap.

## API Signatures (high-level)
- receive_stock(product_id, store_id, batch_number, quantity, expiry_date, cost_price, user_id) -> batch dict
- allocate_stock_for_sale(product_id, store_id, quantity) -> List[{batch_id, qty_allocated}]
- reserve_stock(product_id, store_id, quantity, user_id, ttl_seconds) -> reservation_id
- release_reservation(reservation_id, user_id) -> bool
- adjust_stock(batch_id, delta, user_id, reason) -> bool
- writeoff_batch(batch_id, quantity, user_id, reason) -> bool
- transfer_stock(product_id, batch_number, quantity, from_store_id, to_store_id, user_id) -> transfer_id
- reconcile_inventory(store_id, physical_counts: List[{product_id, counted_qty}], user_id) -> report

## Audit Requirements
- Each mutation must insert into `inventory_audit` with product_batch_id, previous_quantity, new_quantity, change_type, reference_id, notes, user_id.

## Transactions & Concurrency
- Use database transactions for multi-step operations (allocation + sale commit).
- On SQLite, ensure `BEGIN` / commit orchestration is done at session level. For production, add row-level locking or optimistic checks in RDBMS that support it.

## UX Notes
- Receiving UI should validate expiry and batch numbers.
- Allocation failures should return partial allocations and a clear message to create backorders.

## Migration Plan
1. Add new tables (`suppliers`, `purchase_receipts`, `purchase_receipt_items`, `stock_reservations`).
2. Seed demo suppliers and adapt `init_db()` to be idempotent.
3. Add tests for `allocate_stock_for_sale()` and reservation flows.

---
Generated: Automated change — implement basic schema and service APIs next.
