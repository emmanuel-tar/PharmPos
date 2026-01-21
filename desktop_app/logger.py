"""
PharmaPOS NG - Centralized Logging System

Provides comprehensive logging for debugging, auditing, and error tracking.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from desktop_app.config import PROJECT_ROOT, LOGS_DIR


class PharmaPOSLogger:
    """Centralized logging system for PharmaPOS."""
    
    _instance: Optional['PharmaPOSLogger'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_logging()
            PharmaPOSLogger._initialized = True
    
    def _setup_logging(self):
        """Setup logging configuration."""
        # Create logs directory if it doesn't exist
        logs_dir = LOGS_DIR
        if not logs_dir.exists():
            logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        root_logger.handlers.clear()
        
        # File handler for all logs (rotating)
        all_log_file = logs_dir / 'pharmapos.log'
        file_handler = RotatingFileHandler(
            all_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # File handler for errors only
        error_log_file = logs_dir / 'errors.log'
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
        
        # Log startup
        logging.info("=" * 80)
        logging.info("PharmaPOS NG Started")
        logging.info(f"Log directory: {logs_dir}")
        logging.info("=" * 80)
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get a logger instance for a specific module.
        
        Args:
            name: Logger name (typically __name__)
            
        Returns:
            Logger instance
        """
        return logging.getLogger(name)


def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    # Ensure logger is initialized
    PharmaPOSLogger()
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, exc: Exception, context: str = ""):
    """Log an exception with full context.
    
    Args:
        logger: Logger instance
        exc: Exception to log
        context: Additional context information
    """
    if context:
        logger.error(f"{context}: {type(exc).__name__}: {str(exc)}", exc_info=True)
    else:
        logger.error(f"{type(exc).__name__}: {str(exc)}", exc_info=True)


def log_user_action(username: str, action: str, details: str = ""):
    """Log user actions for audit trail.
    
    Args:
        username: Username performing the action
        action: Action performed
        details: Additional details
    """
    logger = get_logger('audit')
    log_msg = f"USER: {username} | ACTION: {action}"
    if details:
        log_msg += f" | DETAILS: {details}"
    logger.info(log_msg)


def log_database_operation(operation: str, table: str, record_id: Optional[int] = None, user: str = ""):
    """Log database operations for audit trail.
    
    Args:
        operation: Operation type (INSERT, UPDATE, DELETE)
        table: Table name
        record_id: Record ID if applicable
        user: Username performing operation
    """
    logger = get_logger('database')
    log_msg = f"DB {operation} | TABLE: {table}"
    if record_id:
        log_msg += f" | ID: {record_id}"
    if user:
        log_msg += f" | USER: {user}"
    logger.info(log_msg)


__all__ = [
    'PharmaPOSLogger',
    'get_logger',
    'log_exception',
    'log_user_action',
    'log_database_operation',
]
