"""
PharmaPOS NG - Procurement Service

This module handles supplier management, purchase orders, and receiving.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from .base_service import BaseService


class ProcurementService(BaseService):
    """Manages suppliers and purchase operations."""

    def __init__(self, session: Optional[Session] = None):
        super().__init__(session)

    # --- Supplier Management ---
    
    def create_supplier(self, name: str, phone: str = "", contact: str = "", address: str = "") -> Dict[str, Any]:
        from desktop_app.models import SupplierService
        service = SupplierService(self.session)
        return service.create_supplier(name, phone, contact, address)

    def get_supplier(self, supplier_id: int) -> Optional[Dict[str, Any]]:
        from desktop_app.models import SupplierService
        service = SupplierService(self.session)
        return service.get_supplier(supplier_id)

    def get_all_suppliers(self) -> List[Dict[str, Any]]:
        from desktop_app.models import SupplierService
        service = SupplierService(self.session)
        return service.get_all_suppliers()

    def update_supplier(self, supplier_id: int, **kwargs) -> bool:
        from desktop_app.models import SupplierService
        service = SupplierService(self.session)
        return service.update_supplier(supplier_id, **kwargs)

    def delete_supplier(self, supplier_id: int) -> bool:
        from desktop_app.models import SupplierService
        service = SupplierService(self.session)
        return service.delete_supplier(supplier_id)

    # --- Purchase Orders ---

    def create_purchase_order(
        self,
        supplier_id: int,
        store_id: int,
        user_id: int,
        items: List[Dict[str, Any]],
        expected_delivery_date: Optional[date] = None,
        notes: str = "",
        status: str = "draft",
    ) -> Dict[str, Any]:
        from desktop_app.models import PurchaseOrderService
        service = PurchaseOrderService(self.session)
        return service.create_purchase_order(
            supplier_id, store_id, user_id, items, expected_delivery_date, notes, status
        )

    def get_purchase_orders(self, store_id: int, status: str = None) -> List[Dict[str, Any]]:
        from desktop_app.models import PurchaseOrderService
        service = PurchaseOrderService(self.session)
        return service.get_purchase_orders_by_status(store_id, status)

    def get_purchase_order_details(self, po_id: int) -> Dict[str, Any]:
        from desktop_app.models import PurchaseOrderService
        service = PurchaseOrderService(self.session)
        po = service.get_purchase_order(po_id)
        if po:
            po['items'] = service.get_po_items(po_id)
        return po

    def approve_purchase_order(self, po_id: int, approver_id: int) -> bool:
        from desktop_app.models import PurchaseOrderService
        service = PurchaseOrderService(self.session)
        return service.approve_purchase_order(po_id, approver_id)

    def receive_goods(self, po_id: int, user_id: int, receipts: List[Dict[str, Any]]) -> Dict[str, Any]:
        from desktop_app.models import PurchaseOrderService
        service = PurchaseOrderService(self.session)
        return service.receive_goods(po_id, user_id, receipts)
