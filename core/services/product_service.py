"""
PharmaPOS NG - Product Service

This module manages the product catalog, pricing, and stock levels.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from .base_service import BaseService


class ProductService(BaseService):
    """Service for managing products in the catalog."""

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize product service.
        
        Args:
            session: SQLAlchemy database session
        """
        super().__init__(session)

    def create_product(
        self,
        name: str,
        sku: str,
        cost_price: Decimal,
        selling_price: Decimal,
        nafdac_number: str,
        category: str = None,
        warehouse_location: str = None,
        generic_name: str = "",
        barcode: str = "",
        description: str = "",
        retail_price: Decimal = None,
        bulk_price: Decimal = None,
        bulk_quantity: int = None,
        wholesale_price: Decimal = None,
        wholesale_quantity: int = None,
        min_stock: int = 0,
        max_stock: int = 9999,
        reorder_level: int = None,
    ) -> dict:
        """
        Create a new product with pricing tiers and stock alerts.
        """
        from desktop_app.models import ProductService as ModelProductService
        
        model_service = ModelProductService(self.session)
        return model_service.create_product(
            name=name,
            sku=sku,
            cost_price=cost_price,
            selling_price=selling_price,
            nafdac_number=nafdac_number,
            category=category,
            warehouse_location=warehouse_location,
            generic_name=generic_name,
            barcode=barcode,
            description=description,
            retail_price=retail_price,
            bulk_price=bulk_price,
            bulk_quantity=bulk_quantity,
            wholesale_price=wholesale_price,
            wholesale_quantity=wholesale_quantity,
            min_stock=min_stock,
            max_stock=max_stock,
            reorder_level=reorder_level,
        )

    def get_product(self, product_id: int) -> Optional[dict]:
        """Get product by ID."""
        from desktop_app.models import ProductService as ModelProductService
        
        model_service = ModelProductService(self.session)
        return model_service.get_product(product_id)

    def get_product_by_sku(self, sku: str) -> Optional[dict]:
        """Get product by SKU."""
        from desktop_app.models import ProductService as ModelProductService
        
        model_service = ModelProductService(self.session)
        return model_service.get_product_by_sku(sku)

    def get_product_by_barcode(self, barcode: str) -> Optional[dict]:
        """Get product by barcode."""
        from desktop_app.models import ProductService as ModelProductService
        
        model_service = ModelProductService(self.session)
        return model_service.get_product_by_barcode(barcode)

    def get_all_products(self, active_only: bool = True, category: str = None) -> List[dict]:
        """Get all products, optionally filtered by category."""
        from desktop_app.models import ProductService as ModelProductService
        
        model_service = ModelProductService(self.session)
        return model_service.get_all_products(active_only, category)

    def update_product(self, product_id: int, **kwargs) -> bool:
        """Update product details."""
        from desktop_app.models import ProductService as ModelProductService
        
        model_service = ModelProductService(self.session)
        return model_service.update_product(product_id, **kwargs)

    def deactivate_product(self, product_id: int) -> bool:
        """Deactivate a product."""
        from desktop_app.models import ProductService as ModelProductService
        
        model_service = ModelProductService(self.session)
        return model_service.deactivate_product(product_id)


__all__ = ["ProductService"]
