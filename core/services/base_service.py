"""
PharmaPOS NG - Base Service

Base class for all business services.
"""

from typing import Optional
from sqlalchemy.orm import Session


class BaseService:
    """Base class for all business logic services."""
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize service with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def close(self) -> None:
        """Close the database session."""
        if self.session:
            try:
                self.session.close()
            except Exception:
                pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


__all__ = ['BaseService']
