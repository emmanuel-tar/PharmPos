"""
PharmaPOS NG - Store Service

This module manages store settings and branches.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from .base_service import BaseService


class StoreService(BaseService):
    """Service for managing stores."""

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize store service.
        """
        super().__init__(session)

    def create_store(self, name: str, address: str = "", is_primary: bool = False) -> dict:
        """Create a new store."""
        from desktop_app.models import StoreService as ModelStoreService
        
        model_service = ModelStoreService(self.session)
        return model_service.create_store(name, address, is_primary)

    def get_store(self, store_id: int) -> Optional[dict]:
        """Get store by ID."""
        from desktop_app.models import StoreService as ModelStoreService
        
        model_service = ModelStoreService(self.session)
        return model_service.get_store(store_id)

    def get_all_stores(self) -> List[dict]:
        """Get all stores."""
        from desktop_app.models import StoreService as ModelStoreService
        
        model_service = ModelStoreService(self.session)
        return model_service.get_all_stores()

    def get_primary_store(self) -> Optional[dict]:
        """Get the primary store."""
        from desktop_app.models import StoreService as ModelStoreService
        
        model_service = ModelStoreService(self.session)
        return model_service.get_primary_store()

    def update_store(self, store_id: int, **kwargs) -> bool:
        """Update store details."""
        from desktop_app.models import StoreService as ModelStoreService
        
        model_service = ModelStoreService(self.session)
        return model_service.update_store(store_id, **kwargs)

    def delete_store(self, store_id: int) -> bool:
        """Delete store."""
        from desktop_app.models import StoreService as ModelStoreService
        
        model_service = ModelStoreService(self.session)
        return model_service.delete_store(store_id)


__all__ = ["StoreService"]
