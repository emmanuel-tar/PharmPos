#!/usr/bin/env python3
"""
Scheduled expiry job script.
Runs expiry checks for all stores and logs results.
Can be invoked from cron/scheduler or manually.

Usage:
  python expire_job.py [--days=10] [--store-id=<id>]
  
Example:
  python expire_job.py --days=10
  python expire_job.py --store-id=1 --days=15
"""

import sys
import argparse
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from desktop_app.database import get_db_path, get_engine
from desktop_app.models import InventoryService, get_session, StoreService, UserService


def run_expiry_job(days=10, store_id=None):
    """
    Run expiry checks for specified store or all stores.
    
    Args:
        days: Number of days threshold for expiry (default 10)
        store_id: Optional store ID to run expiry for; if None, runs for all active stores
    
    Returns:
        tuple: (total_expired_count, details_dict)
    """
    engine = get_engine()
    session = get_session()
    
    try:
        # Get primary user for audit (use 'admin' or fallback to first active user)
        user_service = UserService(session)
        admin_user = user_service.get_user_by_username('admin')
        if not admin_user:
            users = session.execute("SELECT * FROM users WHERE is_active = 1 LIMIT 1").fetchone()
            if not users:
                logger.error("No active users found; cannot run expiry audit.")
                return 0, {}
            user_id = users[0]
        else:
            user_id = admin_user.id
        
        # Get stores to process
        store_service = StoreService(session)
        if store_id:
            stores = [store_service.get_store(store_id)]
            if not stores[0]:
                logger.error(f"Store {store_id} not found.")
                return 0, {}
        else:
            # Get all active stores
            stores = session.execute("SELECT * FROM stores WHERE is_active = 1").fetchall()
            stores = [type('Store', (), {'id': s[0], 'name': s[1]})() for s in stores]
        
        inv_service = InventoryService(session)
        total_expired = 0
        details = {}
        
        for store in stores:
            if store:
                logger.info(f"Running expiry check for store: {store.id} (days={days})")
                try:
                    expired_count = inv_service.expire_batches_within_days(store.id, days, user_id)
                    total_expired += expired_count
                    details[store.id] = {'expired': expired_count, 'status': 'success'}
                    logger.info(f"  → Expired {expired_count} batches")
                except Exception as e:
                    logger.error(f"  → Error: {e}")
                    details[store.id] = {'expired': 0, 'status': 'error', 'error': str(e)}
        
        session.commit()
        logger.info(f"Expiry job completed. Total expired: {total_expired}")
        return total_expired, details
    
    except Exception as e:
        logger.error(f"Expiry job failed: {e}")
        session.rollback()
        return 0, {'error': str(e)}
    
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description='Run scheduled inventory expiry checks.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python expire_job.py                    # Run for all stores, 10-day threshold
  python expire_job.py --days=15          # Run for all stores, 15-day threshold
  python expire_job.py --store-id=1       # Run for store 1 only
  python expire_job.py --store-id=2 --days=7  # Run for store 2, 7-day threshold
        '''
    )
    parser.add_argument('--days', type=int, default=10,
                        help='Days threshold for expiry (default: 10)')
    parser.add_argument('--store-id', type=int, default=None,
                        help='Optional store ID; if not specified, runs for all active stores')
    
    args = parser.parse_args()
    
    logger.info(f"Starting expiry job at {datetime.now().isoformat()}")
    logger.info(f"Configuration: days={args.days}, store_id={args.store_id}")
    
    total_expired, details = run_expiry_job(days=args.days, store_id=args.store_id)
    
    logger.info(f"Results: {total_expired} batches expired")
    if details:
        for store_id, result in details.items():
            logger.info(f"  Store {store_id}: {result}")
    
    logger.info(f"Job completed at {datetime.now().isoformat()}")
    sys.exit(0)


if __name__ == '__main__':
    main()
