"""
PharmaPOS NG - Customer Service
"""

from typing import Optional, List
from .base_service import BaseService

class CustomerService(BaseService):
    """Handles customer data and loyalty points."""

    def get_all_customers(self) -> List[dict]:
        """Fetch all customers from the database."""
        from desktop_app.database import customers
        from sqlalchemy import select
        
        stmt = select(customers).order_by(customers.c.name)
        results = self.session.execute(stmt).fetchall()
        return [dict(row._mapping) for row in results]

    def search_customers(self, query: str) -> List[dict]:
        """Search customers by name or phone."""
        from desktop_app.database import customers
        from sqlalchemy import select, or_
        
        stmt = select(customers).where(
            or_(
                customers.c.name.ilike(f"%{query}%"),
                customers.c.phone.ilike(f"%{query}%")
            )
        )
        results = self.session.execute(stmt).fetchall()
        return [dict(row._mapping) for row in results]

    def create_customer(self, name: str, phone: str, email: Optional[str] = None, address: Optional[str] = None) -> dict:
        """Register a new customer."""
        from desktop_app.database import customers
        import uuid
        
        stmt = customers.insert().values(
            name=name,
            phone=phone,
            email=email,
            address=address,
            sync_id=str(uuid.uuid4())
        )
        result = self.session.execute(stmt)
        self.session.commit()
        
        return {
            "id": result.inserted_primary_key[0],
            "name": name,
            "phone": phone
        }
