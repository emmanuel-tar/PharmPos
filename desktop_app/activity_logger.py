"""
PharmaPOS NG - Activity Logger

Tracks user activities and maintains audit trail for compliance and accountability.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import Session

from desktop_app.database import activity_logs
from desktop_app.logger import get_logger

logger = get_logger(__name__)


class ActivityLogger:
    """Service for logging and retrieving user activities."""

    def __init__(self, session: Session):
        """Initialize activity logger.
        
        Args:
            session: Database session
        """
        self.session = session

    def log_activity(
        self,
        user_id: Optional[int],
        username: str,
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        store_id: Optional[int] = None,
    ) -> int:
        """Log a user activity.
        
        Args:
            user_id: User ID (can be None for system actions)
            username: Username for historical record
            action: Action performed (e.g., 'login', 'sale', 'stock_add')
            entity_type: Type of entity affected (e.g., 'sale', 'product', 'user')
            entity_id: ID of affected entity
            details: Additional details as dictionary (will be JSON encoded)
            ip_address: IP address of user
            store_id: Store where action occurred
            
        Returns:
            ID of created activity log entry
        """
        try:
            details_json = json.dumps(details) if details else None
            
            stmt = activity_logs.insert().values(
                user_id=user_id,
                username=username,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details_json,
                ip_address=ip_address,
                store_id=store_id,
            )
            
            result = self.session.execute(stmt)
            self.session.commit()
            
            return result.inserted_primary_key[0]
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
            self.session.rollback()
            return 0

    def get_user_activities(
        self,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        store_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Retrieve user activities with filters.
        
        Args:
            user_id: Filter by user ID
            username: Filter by username
            action: Filter by action type
            entity_type: Filter by entity type
            store_id: Filter by store
            start_date: Filter activities after this date
            end_date: Filter activities before this date
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of activity log entries
        """
        try:
            stmt = select(activity_logs).order_by(desc(activity_logs.c.created_at))
            
            # Apply filters
            conditions = []
            if user_id is not None:
                conditions.append(activity_logs.c.user_id == user_id)
            if username:
                conditions.append(activity_logs.c.username == username)
            if action:
                conditions.append(activity_logs.c.action == action)
            if entity_type:
                conditions.append(activity_logs.c.entity_type == entity_type)
            if store_id is not None:
                conditions.append(activity_logs.c.store_id == store_id)
            if start_date:
                conditions.append(activity_logs.c.created_at >= start_date)
            if end_date:
                conditions.append(activity_logs.c.created_at <= end_date)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.limit(limit).offset(offset)
            
            result = self.session.execute(stmt)
            rows = result.fetchall()
            
            activities = []
            for row in rows:
                activity = dict(row._mapping)
                # Parse JSON details if present
                if activity.get('details'):
                    try:
                        activity['details'] = json.loads(activity['details'])
                    except json.JSONDecodeError:
                        pass
                activities.append(activity)
            
            return activities
        except Exception as e:
            logger.error(f"Failed to retrieve activities: {e}")
            return []

    def get_activity_summary(
        self,
        user_id: Optional[int] = None,
        store_id: Optional[int] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get activity summary statistics.
        
        Args:
            user_id: Filter by user ID
            store_id: Filter by store
            days: Number of days to analyze
            
        Returns:
            Dictionary with activity statistics
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            activities = self.get_user_activities(
                user_id=user_id,
                store_id=store_id,
                start_date=start_date,
                limit=10000,  # Get all for summary
            )
            
            # Count by action type
            action_counts = {}
            for activity in activities:
                action = activity['action']
                action_counts[action] = action_counts.get(action, 0) + 1
            
            # Count by entity type
            entity_counts = {}
            for activity in activities:
                entity_type = activity.get('entity_type')
                if entity_type:
                    entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            
            return {
                'total_activities': len(activities),
                'action_counts': action_counts,
                'entity_counts': entity_counts,
                'period_days': days,
                'start_date': start_date.isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get activity summary: {e}")
            return {
                'total_activities': 0,
                'action_counts': {},
                'entity_counts': {},
                'period_days': days,
            }

    def cleanup_old_logs(self, retention_days: int = 365) -> int:
        """Delete activity logs older than retention period.
        
        Args:
            retention_days: Number of days to retain logs
            
        Returns:
            Number of deleted records
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            stmt = activity_logs.delete().where(
                activity_logs.c.created_at < cutoff_date
            )
            
            result = self.session.execute(stmt)
            self.session.commit()
            
            deleted_count = result.rowcount
            logger.info(f"Deleted {deleted_count} old activity logs")
            
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            self.session.rollback()
            return 0


__all__ = ['ActivityLogger']
