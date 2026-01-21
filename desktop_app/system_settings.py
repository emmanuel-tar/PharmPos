"""
PharmaPOS NG - System Settings Manager

Manages system configuration including tax rates, business information, and receipt customization.
"""

from __future__ import annotations

import json
from typing import Optional, Dict, Any, List
from decimal import Decimal
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from desktop_app.database import system_settings
from desktop_app.logger import get_logger

logger = get_logger(__name__)


class SettingsManager:
    """Service for managing system settings."""

    # Default settings
    DEFAULTS = {
        # Tax settings
        'tax.vat_rate': {'value': '7.5', 'category': 'tax', 'data_type': 'number', 'description': 'VAT rate percentage'},
        'tax.vat_enabled': {'value': 'true', 'category': 'tax', 'data_type': 'boolean', 'description': 'Enable VAT calculation'},
        'tax.tax_inclusive': {'value': 'false', 'category': 'tax', 'data_type': 'boolean', 'description': 'Prices include tax'},
        
        # Business information
        'business.name': {'value': 'PharmaPOS NG', 'category': 'business', 'data_type': 'string', 'description': 'Business name'},
        'business.address': {'value': '', 'category': 'business', 'data_type': 'string', 'description': 'Business address'},
        'business.phone': {'value': '', 'category': 'business', 'data_type': 'string', 'description': 'Business phone'},
        'business.email': {'value': '', 'category': 'business', 'data_type': 'string', 'description': 'Business email'},
        'business.registration_number': {'value': '', 'category': 'business', 'data_type': 'string', 'description': 'Business registration number'},
        'business.pcn_license': {'value': '', 'category': 'business', 'data_type': 'string', 'description': 'PCN license number'},
        
        # Receipt customization
        'receipt.header': {'value': 'Thank you for your purchase!', 'category': 'receipt', 'data_type': 'string', 'description': 'Receipt header text'},
        'receipt.footer': {'value': 'Please keep this receipt for your records.', 'category': 'receipt', 'data_type': 'string', 'description': 'Receipt footer text'},
        'receipt.show_logo': {'value': 'true', 'category': 'receipt', 'data_type': 'boolean', 'description': 'Show logo on receipt'},
        'receipt.show_barcode': {'value': 'true', 'category': 'receipt', 'data_type': 'boolean', 'description': 'Show barcode on receipt'},
        
        # Activity log retention
        'general.activity_log_retention_days': {'value': '365', 'category': 'general', 'data_type': 'number', 'description': 'Days to retain activity logs'},
        
        # Compliance
        'compliance.expiry_alert_days': {'value': '30', 'category': 'compliance', 'data_type': 'number', 'description': 'Days before expiry to alert'},
        'compliance.auto_generate_reports': {'value': 'false', 'category': 'compliance', 'data_type': 'boolean', 'description': 'Auto-generate compliance reports'},
    }

    def __init__(self, session: Session):
        """Initialize settings manager.
        
        Args:
            session: Database session
        """
        self.session = session
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        """Ensure default settings exist in database."""
        try:
            for key, config in self.DEFAULTS.items():
                # Check if setting exists
                stmt = select(system_settings).where(system_settings.c.key == key)
                result = self.session.execute(stmt)
                existing = result.fetchone()
                
                if not existing:
                    # Create default setting
                    stmt = system_settings.insert().values(
                        key=key,
                        value=config['value'],
                        category=config['category'],
                        data_type=config['data_type'],
                        description=config['description'],
                    )
                    self.session.execute(stmt)
            
            self.session.commit()
        except Exception as e:
            logger.error(f"Failed to ensure default settings: {e}")
            self.session.rollback()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value.
        
        Args:
            key: Setting key
            default: Default value if setting not found
            
        Returns:
            Setting value (converted to appropriate type)
        """
        try:
            stmt = select(system_settings).where(system_settings.c.key == key)
            result = self.session.execute(stmt)
            row = result.fetchone()
            
            if not row:
                return default
            
            setting = dict(row._mapping)
            value = setting['value']
            data_type = setting['data_type']
            
            # Convert to appropriate type
            if data_type == 'number':
                try:
                    return Decimal(value) if '.' in value else int(value)
                except (ValueError, TypeError):
                    return default
            elif data_type == 'boolean':
                return value.lower() in ('true', '1', 'yes')
            elif data_type == 'json':
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return default
            else:
                return value
        except Exception as e:
            logger.error(f"Failed to get setting {key}: {e}")
            return default

    def set(
        self,
        key: str,
        value: Any,
        category: str = 'general',
        description: str = '',
        user_id: Optional[int] = None,
    ) -> bool:
        """Set a setting value.
        
        Args:
            key: Setting key
            value: Setting value
            category: Setting category
            description: Setting description
            user_id: User making the change
            
        Returns:
            True if successful
        """
        try:
            # Determine data type
            if isinstance(value, bool):
                data_type = 'boolean'
                value_str = 'true' if value else 'false'
            elif isinstance(value, (int, float, Decimal)):
                data_type = 'number'
                value_str = str(value)
            elif isinstance(value, (dict, list)):
                data_type = 'json'
                value_str = json.dumps(value)
            else:
                data_type = 'string'
                value_str = str(value)
            
            # Check if setting exists
            stmt = select(system_settings).where(system_settings.c.key == key)
            result = self.session.execute(stmt)
            existing = result.fetchone()
            
            if existing:
                # Update existing
                stmt = (
                    system_settings.update()
                    .where(system_settings.c.key == key)
                    .values(
                        value=value_str,
                        data_type=data_type,
                        updated_by=user_id,
                    )
                )
            else:
                # Insert new
                stmt = system_settings.insert().values(
                    key=key,
                    value=value_str,
                    category=category,
                    data_type=data_type,
                    description=description,
                    updated_by=user_id,
                )
            
            self.session.execute(stmt)
            self.session.commit()
            
            return True
        except Exception as e:
            logger.error(f"Failed to set setting {key}: {e}")
            self.session.rollback()
            return False

    def get_category(self, category: str) -> Dict[str, Any]:
        """Get all settings in a category.
        
        Args:
            category: Category name
            
        Returns:
            Dictionary of settings in category
        """
        try:
            stmt = select(system_settings).where(
                system_settings.c.category == category
            )
            result = self.session.execute(stmt)
            rows = result.fetchall()
            
            settings = {}
            for row in rows:
                setting = dict(row._mapping)
                key = setting['key']
                # Remove category prefix from key for cleaner access
                short_key = key.split('.', 1)[1] if '.' in key else key
                settings[short_key] = self.get(key)
            
            return settings
        except Exception as e:
            logger.error(f"Failed to get category {category}: {e}")
            return {}

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all settings.
        
        Returns:
            List of all settings with metadata
        """
        try:
            stmt = select(system_settings)
            result = self.session.execute(stmt)
            rows = result.fetchall()
            
            settings = []
            for row in rows:
                setting = dict(row._mapping)
                # Parse value to appropriate type
                setting['parsed_value'] = self.get(setting['key'])
                settings.append(setting)
            
            return settings
        except Exception as e:
            logger.error(f"Failed to get all settings: {e}")
            return []

    def delete(self, key: str) -> bool:
        """Delete a setting.
        
        Args:
            key: Setting key
            
        Returns:
            True if successful
        """
        try:
            stmt = system_settings.delete().where(system_settings.c.key == key)
            self.session.execute(stmt)
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to delete setting {key}: {e}")
            self.session.rollback()
            return False


__all__ = ['SettingsManager']
