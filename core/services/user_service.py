"""
PharmaPOS NG - User Service

This module manages system users and roles.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from .base_service import BaseService


class UserService(BaseService):
    """Service for managing system users."""

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize user service.
        """
        super().__init__(session)

    def create_user(
        self,
        username: str,
        password_hash: str,
        role: str = "cashier",
        store_id: Optional[int] = None,
    ) -> dict:
        """Create a new user."""
        from desktop_app.models import UserService as ModelUserService
        
        model_service = ModelUserService(self.session)
        return model_service.create_user(username, password_hash, role, store_id)

    def get_user(self, user_id: int) -> Optional[dict]:
        """Get user by ID."""
        from desktop_app.models import UserService as ModelUserService
        
        model_service = ModelUserService(self.session)
        return model_service.get_user(user_id)

    def get_user_by_username(self, username: str) -> Optional[dict]:
        """Get user by username."""
        from desktop_app.models import UserService as ModelUserService
        
        model_service = ModelUserService(self.session)
        return model_service.get_user_by_username(username)

    def get_all_users(self) -> List[dict]:
        """Get all active users."""
        from desktop_app.models import UserService as ModelUserService
        
        model_service = ModelUserService(self.session)
        return model_service.get_all_users()

    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user details."""
        from desktop_app.models import UserService as ModelUserService
        
        model_service = ModelUserService(self.session)
        return model_service.update_user(user_id, **kwargs)

    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user."""
        from desktop_app.models import UserService as ModelUserService
        
        model_service = ModelUserService(self.session)
        return model_service.deactivate_user(user_id)


__all__ = ["UserService"]
