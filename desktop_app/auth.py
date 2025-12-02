"""
PharmaPOS NG - Authentication & Session Management

This module handles user authentication, password hashing, and session management.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from desktop_app.models import UserService, get_session


# --- Password Hashing --------------------------------------------------------
class PasswordManager:
    """Manages password hashing and verification."""

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> str:
        """Hash a password using PBKDF2."""
        if salt is None:
            salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
        )
        return f"{salt}${hash_obj.hex()}"

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        try:
            salt, hash_hex = password_hash.split("$")
            new_hash = PasswordManager.hash_password(password, salt)
            return new_hash == password_hash
        except (ValueError, AttributeError):
            return False


# --- User Session -----------------------------------------------------------
class UserSession:
    """Represents an authenticated user session."""

    def __init__(
        self,
        user_id: int,
        username: str,
        role: str,
        store_id: Optional[int] = None,
        session_id: str = None,
    ):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.store_id = store_id
        self.session_id = session_id or secrets.token_urlsafe(32)
        self.created_at = datetime.now()
        self.last_activity = datetime.now()

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now()

    def is_valid(self, timeout_minutes: int = 60) -> bool:
        """Check if session is still valid."""
        elapsed = datetime.now() - self.last_activity
        return elapsed < timedelta(minutes=timeout_minutes)

    def has_permission(self, required_role: str) -> bool:
        """Check if user has required role."""
        role_hierarchy = {
            "admin": 3,
            "manager": 2,
            "cashier": 1,
        }
        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        return user_level >= required_level

    def to_dict(self) -> dict:
        """Serialize session to dictionary."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "store_id": self.store_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
        }


# --- Authentication Service -------------------------------------------------
class AuthenticationService:
    """Service for user authentication and session management."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.sessions: dict[str, UserSession] = {}  # In-memory session store

    def register_user(
        self,
        username: str,
        password: str,
        role: str = "cashier",
        store_id: Optional[int] = None,
    ) -> bool:
        """Register a new user."""
        session = get_session(self.db_path)
        user_service = UserService(session)

        # Check if username already exists
        if user_service.get_user_by_username(username):
            return False

        # Hash password and create user
        password_hash = PasswordManager.hash_password(password)
        try:
            user_service.create_user(
                username=username,
                password_hash=password_hash,
                role=role,
                store_id=store_id,
            )
            return True
        except Exception:
            return False
        finally:
            session.close()

    def login(self, username: str, password: str) -> Optional[UserSession]:
        """Authenticate user and create session."""
        session = get_session(self.db_path)
        user_service = UserService(session)

        try:
            user = user_service.get_user_by_username(username)
            if not user:
                return None

            if not user["is_active"]:
                return None

            if not PasswordManager.verify_password(password, user["password_hash"]):
                return None

            # Create session
            user_session = UserSession(
                user_id=user["id"],
                username=user["username"],
                role=user["role"],
                store_id=user["store_id"],
            )
            self.sessions[user_session.session_id] = user_session
            return user_session
        finally:
            session.close()

    def logout(self, session_id: str) -> bool:
        """End user session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Retrieve active session."""
        if session_id not in self.sessions:
            return None

        user_session = self.sessions[session_id]
        if not user_session.is_valid():
            del self.sessions[session_id]
            return None

        user_session.update_activity()
        return user_session

    def validate_session(self, session_id: str) -> bool:
        """Check if session is valid."""
        return self.get_session(session_id) is not None

    def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> bool:
        """Change user password."""
        session = get_session(self.db_path)
        user_service = UserService(session)

        try:
            user = user_service.get_user(user_id)
            if not user:
                return False

            if not PasswordManager.verify_password(old_password, user["password_hash"]):
                return False

            new_hash = PasswordManager.hash_password(new_password)
            user_service.update_user(user_id, password_hash=new_hash)
            return True
        finally:
            session.close()

    def cleanup_expired_sessions(self, timeout_minutes: int = 60) -> int:
        """Remove expired sessions. Returns count of removed sessions."""
        expired = [
            sid
            for sid, session in self.sessions.items()
            if not session.is_valid(timeout_minutes)
        ]
        for sid in expired:
            del self.sessions[sid]
        return len(expired)


__all__ = [
    "PasswordManager",
    "UserSession",
    "AuthenticationService",
]
