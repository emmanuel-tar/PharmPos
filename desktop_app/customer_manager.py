"""
PharmaPOS NG - Customer Management Module

Handles customer database, purchase history, and loyalty points.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
import uuid

from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session

from desktop_app.database import get_engine, metadata
from desktop_app.logger import get_logger, log_database_operation

logger = get_logger(__name__)


class CustomerService:
    """Service for managing customers."""
    
    def __init__(self, session: Session):
        """Initialize customer service.
        
        Args:
            session: Database session
        """
        self.session = session
        logger.debug("CustomerService initialized")
    
    def create_customer(
        self,
        name: str,
        phone: str,
        email: Optional[str] = None,
        address: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new customer.
        
        Args:
            name: Customer name
            phone: Phone number
            email: Email address (optional)
            address: Physical address (optional)
            user_id: User creating the customer
            
        Returns:
            Customer dictionary
        """
        try:
            from desktop_app.database import customers
            
            stmt = customers.insert().values(
                name=name,
                phone=phone,
                email=email,
                address=address,
                loyalty_points=0,
                total_purchases=Decimal("0"),
                sync_id=str(uuid.uuid4()),
            )
            
            result = self.session.execute(stmt)
            self.session.commit()
            
            customer_id = result.inserted_primary_key[0]
            
            log_database_operation("INSERT", "customers", customer_id, str(user_id) if user_id else "")
            logger.info(f"Customer created: {name} (ID: {customer_id})")
            
            return {
                "id": customer_id,
                "name": name,
                "phone": phone,
                "email": email,
                "address": address,
                "loyalty_points": 0,
                "total_purchases": Decimal("0"),
            }
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating customer: {e}", exc_info=True)
            raise
    
    def get_customer(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """Get customer by ID.
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Customer dictionary or None
        """
        try:
            from desktop_app.database import customers
            
            stmt = select(customers).where(customers.c.id == customer_id)
            result = self.session.execute(stmt).fetchone()
            
            return dict(result._mapping) if result else None
            
        except Exception as e:
            logger.error(f"Error getting customer {customer_id}: {e}", exc_info=True)
            return None
    
    def get_customer_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get customer by phone number.
        
        Args:
            phone: Phone number
            
        Returns:
            Customer dictionary or None
        """
        try:
            from desktop_app.database import customers
            
            stmt = select(customers).where(customers.c.phone == phone)
            result = self.session.execute(stmt).fetchone()
            
            return dict(result._mapping) if result else None
            
        except Exception as e:
            logger.error(f"Error getting customer by phone {phone}: {e}", exc_info=True)
            return None
    
    def search_customers(self, query: str) -> List[Dict[str, Any]]:
        """Search customers by name or phone.
        
        Args:
            query: Search query
            
        Returns:
            List of matching customers
        """
        try:
            from desktop_app.database import customers
            
            search_pattern = f"%{query}%"
            stmt = select(customers).where(
                or_(
                    customers.c.name.like(search_pattern),
                    customers.c.phone.like(search_pattern),
                    customers.c.email.like(search_pattern) if query else False
                )
            ).limit(50)
            
            results = self.session.execute(stmt).fetchall()
            return [dict(row._mapping) for row in results]
            
        except Exception as e:
            logger.error(f"Error searching customers: {e}", exc_info=True)
            return []
    
    def get_all_customers(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all customers.
        
        Args:
            active_only: Only return active customers
            
        Returns:
            List of customers
        """
        try:
            from desktop_app.database import customers
            
            stmt = select(customers)
            if active_only:
                stmt = stmt.where(customers.c.is_active == True)
            
            stmt = stmt.order_by(customers.c.name)
            results = self.session.execute(stmt).fetchall()
            
            return [dict(row._mapping) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting all customers: {e}", exc_info=True)
            return []
    
    def update_customer(
        self,
        customer_id: int,
        user_id: Optional[int] = None,
        **kwargs
    ) -> bool:
        """Update customer details.
        
        Args:
            customer_id: Customer ID
            user_id: User making the update
            **kwargs: Fields to update
            
        Returns:
            True if successful
        """
        try:
            from desktop_app.database import customers
            
            stmt = customers.update().where(customers.c.id == customer_id).values(**kwargs)
            self.session.execute(stmt)
            self.session.commit()
            
            log_database_operation("UPDATE", "customers", customer_id, str(user_id) if user_id else "")
            logger.info(f"Customer {customer_id} updated")
            
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating customer {customer_id}: {e}", exc_info=True)
            return False
    
    def add_loyalty_points(
        self,
        customer_id: int,
        points: int,
        reason: str = "purchase"
    ) -> bool:
        """Add loyalty points to customer.
        
        Args:
            customer_id: Customer ID
            points: Points to add
            reason: Reason for points
            
        Returns:
            True if successful
        """
        try:
            from desktop_app.database import customers
            
            customer = self.get_customer(customer_id)
            if not customer:
                return False
            
            new_points = customer.get('loyalty_points', 0) + points
            
            stmt = customers.update().where(
                customers.c.id == customer_id
            ).values(loyalty_points=new_points)
            
            self.session.execute(stmt)
            self.session.commit()
            
            logger.info(f"Added {points} loyalty points to customer {customer_id} ({reason})")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding loyalty points: {e}", exc_info=True)
            return False
    
    def record_purchase(
        self,
        customer_id: int,
        amount: Decimal,
        sale_id: int
    ) -> bool:
        """Record a purchase for customer.
        
        Args:
            customer_id: Customer ID
            amount: Purchase amount
            sale_id: Sale ID
            
        Returns:
            True if successful
        """
        try:
            from desktop_app.database import customers
            
            customer = self.get_customer(customer_id)
            if not customer:
                return False
            
            # Update total purchases
            new_total = customer.get('total_purchases', Decimal("0")) + amount
            
            # Award loyalty points (1 point per 100 currency units)
            points_earned = int(amount / 100)
            new_points = customer.get('loyalty_points', 0) + points_earned
            
            stmt = customers.update().where(
                customers.c.id == customer_id
            ).values(
                total_purchases=new_total,
                loyalty_points=new_points,
                last_purchase_date=datetime.now()
            )
            
            self.session.execute(stmt)
            self.session.commit()
            
            logger.info(f"Recorded purchase for customer {customer_id}: {amount} (earned {points_earned} points)")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error recording purchase: {e}", exc_info=True)
            return False
    
    def get_customer_purchase_history(
        self,
        customer_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get customer's purchase history.
        
        Args:
            customer_id: Customer ID
            limit: Maximum number of records
            
        Returns:
            List of sales
        """
        try:
            from desktop_app.database import sales
            
            stmt = select(sales).where(
                sales.c.customer_id == customer_id
            ).order_by(
                sales.c.created_at.desc()
            ).limit(limit)
            
            results = self.session.execute(stmt).fetchall()
            return [dict(row._mapping) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting purchase history: {e}", exc_info=True)
            return []
    
    def deactivate_customer(self, customer_id: int, user_id: Optional[int] = None) -> bool:
        """Deactivate a customer.
        
        Args:
            customer_id: Customer ID
            user_id: User performing the action
            
        Returns:
            True if successful
        """
        return self.update_customer(customer_id, user_id, is_active=False)


__all__ = ['CustomerService']
