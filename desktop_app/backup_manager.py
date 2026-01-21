"""
PharmaPOS NG - Backup and Recovery Manager

Handles automated backups, manual backups, and database restoration.
"""

import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Tuple
import json

from desktop_app.config import PROJECT_ROOT, DB_PATH
from desktop_app.logger import get_logger

logger = get_logger(__name__)


class BackupManager:
    """Manages database backups and restoration."""
    
    def __init__(self, db_path: Optional[str] = None, backup_dir: Optional[str] = None):
        """Initialize backup manager.
        
        Args:
            db_path: Path to database file (defaults to config)
            backup_dir: Directory for backups (defaults to ./backups)
        """
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.backup_dir = Path(backup_dir) if backup_dir else PROJECT_ROOT / "backups"
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"BackupManager initialized: DB={self.db_path}, Backups={self.backup_dir}")
    
    def create_backup(self, backup_name: Optional[str] = None) -> Tuple[bool, str, Optional[Path]]:
        """Create a database backup.
        
        Args:
            backup_name: Optional custom backup name
            
        Returns:
            Tuple of (success, message, backup_path)
        """
        try:
            # Check if database exists
            if not self.db_path.exists():
                return False, f"Database not found: {self.db_path}", None
            
            # Generate backup filename
            if backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"{backup_name}_{timestamp}.db"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"pharmapos_backup_{timestamp}.db"
            
            backup_path = self.backup_dir / backup_filename
            
            # Create backup using SQLite backup API (safer than file copy)
            logger.info(f"Creating backup: {backup_path}")
            
            source_conn = sqlite3.connect(str(self.db_path))
            backup_conn = sqlite3.connect(str(backup_path))
            
            with backup_conn:
                source_conn.backup(backup_conn)
            
            source_conn.close()
            backup_conn.close()
            
            # Create metadata file
            metadata = {
                "backup_date": datetime.now().isoformat(),
                "original_db": str(self.db_path),
                "backup_size": backup_path.stat().st_size,
                "backup_type": "manual" if backup_name else "automatic"
            }
            
            metadata_path = backup_path.with_suffix('.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Backup created successfully: {backup_path}")
            return True, f"Backup created: {backup_filename}", backup_path
            
        except Exception as e:
            logger.error(f"Backup failed: {e}", exc_info=True)
            return False, f"Backup failed: {str(e)}", None
    
    def restore_backup(self, backup_path: Path) -> Tuple[bool, str]:
        """Restore database from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not backup_path.exists():
                return False, f"Backup file not found: {backup_path}"
            
            # Create a safety backup of current database
            safety_backup_name = f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            success, msg, _ = self.create_backup(safety_backup_name)
            if not success:
                logger.warning(f"Could not create safety backup: {msg}")
            
            # Verify backup integrity
            if not self._verify_backup(backup_path):
                return False, "Backup file is corrupted or invalid"
            
            # Close all connections (important!)
            logger.info(f"Restoring from backup: {backup_path}")
            
            # Copy backup to database location
            shutil.copy2(backup_path, self.db_path)
            
            logger.info("Database restored successfully")
            return True, "Database restored successfully"
            
        except Exception as e:
            logger.error(f"Restore failed: {e}", exc_info=True)
            return False, f"Restore failed: {str(e)}"
    
    def list_backups(self) -> List[dict]:
        """List all available backups.
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        try:
            for backup_file in sorted(self.backup_dir.glob("*.db"), reverse=True):
                metadata_file = backup_file.with_suffix('.json')
                
                backup_info = {
                    "filename": backup_file.name,
                    "path": backup_file,
                    "size": backup_file.stat().st_size,
                    "created": datetime.fromtimestamp(backup_file.stat().st_mtime),
                }
                
                # Load metadata if available
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            backup_info.update(metadata)
                    except Exception as e:
                        logger.warning(f"Could not load metadata for {backup_file}: {e}")
                
                backups.append(backup_info)
                
        except Exception as e:
            logger.error(f"Error listing backups: {e}", exc_info=True)
        
        return backups
    
    def cleanup_old_backups(self, keep_count: int = 10, keep_days: Optional[int] = None) -> int:
        """Remove old backups based on retention policy.
        
        Args:
            keep_count: Number of recent backups to keep
            keep_days: Keep backups newer than this many days (optional)
            
        Returns:
            Number of backups deleted
        """
        try:
            backups = self.list_backups()
            deleted_count = 0
            
            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x['created'], reverse=True)
            
            for i, backup in enumerate(backups):
                should_delete = False
                
                # Keep recent backups
                if i >= keep_count:
                    should_delete = True
                
                # Check age if keep_days is specified
                if keep_days and not should_delete:
                    age = datetime.now() - backup['created']
                    if age.days > keep_days:
                        should_delete = True
                
                if should_delete:
                    try:
                        backup_path = backup['path']
                        metadata_path = backup_path.with_suffix('.json')
                        
                        backup_path.unlink()
                        if metadata_path.exists():
                            metadata_path.unlink()
                        
                        deleted_count += 1
                        logger.info(f"Deleted old backup: {backup['filename']}")
                        
                    except Exception as e:
                        logger.error(f"Error deleting backup {backup['filename']}: {e}")
            
            logger.info(f"Cleanup complete: {deleted_count} backups deleted")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}", exc_info=True)
            return 0
    
    def _verify_backup(self, backup_path: Path) -> bool:
        """Verify backup file integrity.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if backup is valid
        """
        try:
            conn = sqlite3.connect(str(backup_path))
            cursor = conn.cursor()
            
            # Try to query sqlite_master
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            conn.close()
            
            # Should have at least some tables
            return len(tables) > 0
            
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False
    
    def get_backup_size(self) -> int:
        """Get total size of all backups in bytes.
        
        Returns:
            Total size in bytes
        """
        total_size = 0
        try:
            for backup_file in self.backup_dir.glob("*.db"):
                total_size += backup_file.stat().st_size
        except Exception as e:
            logger.error(f"Error calculating backup size: {e}")
        
        return total_size


class AutoBackupScheduler:
    """Handles automatic backup scheduling."""
    
    def __init__(self, backup_manager: BackupManager):
        """Initialize auto-backup scheduler.
        
        Args:
            backup_manager: BackupManager instance
        """
        self.backup_manager = backup_manager
        self.last_backup_file = PROJECT_ROOT / ".last_backup"
        logger.info("AutoBackupScheduler initialized")
    
    def should_backup(self, interval_hours: int = 24) -> bool:
        """Check if a backup should be performed.
        
        Args:
            interval_hours: Backup interval in hours
            
        Returns:
            True if backup is due
        """
        try:
            if not self.last_backup_file.exists():
                return True
            
            with open(self.last_backup_file, 'r') as f:
                last_backup_str = f.read().strip()
                last_backup = datetime.fromisoformat(last_backup_str)
            
            time_since_backup = datetime.now() - last_backup
            return time_since_backup.total_seconds() >= (interval_hours * 3600)
            
        except Exception as e:
            logger.warning(f"Error checking backup schedule: {e}")
            return True
    
    def perform_auto_backup(self) -> Tuple[bool, str]:
        """Perform automatic backup if due.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self.should_backup():
                return True, "Backup not due yet"
            
            success, msg, _ = self.backup_manager.create_backup("auto")
            
            if success:
                # Update last backup time
                with open(self.last_backup_file, 'w') as f:
                    f.write(datetime.now().isoformat())
                
                # Cleanup old backups (keep last 10)
                self.backup_manager.cleanup_old_backups(keep_count=10)
            
            return success, msg
            
        except Exception as e:
            logger.error(f"Auto-backup failed: {e}", exc_info=True)
            return False, f"Auto-backup failed: {str(e)}"


__all__ = [
    'BackupManager',
    'AutoBackupScheduler',
]
