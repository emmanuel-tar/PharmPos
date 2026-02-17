"""
PharmaPOS NG - Category Service Wrapper
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from .base_service import BaseService


class CategoryService(BaseService):
    """Service for managing product categories."""

    def __init__(self, session: Optional[Session] = None):
        super().__init__(session)

    def create_category(self, name: str, description: str = "") -> dict:
        """Create a new category."""
        from desktop_app.models import CategoryService as ModelCategoryService
        model_service = ModelCategoryService(self.session)
        return model_service.create_category(name, description)

    def get_category(self, category_id: int) -> Optional[dict]:
        """Get category by ID."""
        from desktop_app.models import CategoryService as ModelCategoryService
        model_service = ModelCategoryService(self.session)
        return model_service.get_category(category_id)

    def get_all_categories(self) -> List[dict]:
        """Get all categories."""
        from desktop_app.models import CategoryService as ModelCategoryService
        model_service = ModelCategoryService(self.session)
        return model_service.get_all_categories()

    def update_category(self, category_id: int, **kwargs) -> bool:
        """Update category."""
        from desktop_app.models import CategoryService as ModelCategoryService
        model_service = ModelCategoryService(self.session)
        return model_service.update_category(category_id, **kwargs)

    def delete_category(self, category_id: int) -> bool:
        """Delete category."""
        from desktop_app.models import CategoryService as ModelCategoryService
        model_service = ModelCategoryService(self.session)
        return model_service.delete_category(category_id)


__all__ = ["CategoryService"]
