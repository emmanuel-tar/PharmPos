"""
Test script for Enhanced Expiry Management functionality.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from desktop_app.inventory import InventoryAlerts
from desktop_app.config import DATABASE_PATH


def test_expiry_management():
    """Test the enhanced expiry management features."""
    print("=" * 60)
    print("Testing Enhanced Expiry Management")
    print("=" * 60)
    
    alerts = InventoryAlerts(DATABASE_PATH)
    
    try:
        # Test 1: Get expiry timeline
        print("\n[Test 1] Getting expiry timeline (12 months)...")
        timeline = alerts.get_expiry_timeline(store_id=1, months=12)
        print(f"  [OK] Timeline generated")
        print(f"    - Months: {timeline['months']}")
        print(f"    - Total batches expiring: {timeline['total_batches']}")
        print(f"    - Total items expiring: {timeline['total_items']}")
        if timeline['timeline']:
            print(f"    - First month: {timeline['timeline'][0]['month']} ({timeline['timeline'][0]['batch_count']} batches)")
        
        # Test 2: Suggest promotions
        print("\n[Test 2] Getting promotion suggestions (60 days)...")
        suggestions = alerts.suggest_promotions(store_id=1, days_to_expiry=60)
        print(f"  [OK] Found {len(suggestions)} promotion suggestions")
        for i, suggestion in enumerate(suggestions[:3], 1):
            print(f"    {i}. {suggestion['product_name']}")
            print(f"       - Days until expiry: {suggestion['days_until_expiry']}")
            print(f"       - Suggested discount: {suggestion['suggested_discount']}%")
            print(f"       - Urgency: {suggestion['urgency']}")
        
        # Test 3: Auto-mark expired
        print("\n[Test 3] Identifying expired batches...")
        count, expired = alerts.auto_mark_expired(store_id=1)
        print(f"  [OK] Found {count} expired batch(es)")
        if expired:
            total_value = sum(item['total_value'] for item in expired)
            print(f"    - Total value: N{total_value:.2f}")
            for item in expired[:3]:
                print(f"    - {item['product_name']}: {item['quantity']} units (N{item['total_value']:.2f})")
        
        # Test 4: Get expiry summary
        print("\n[Test 4] Getting expiry summary...")
        summary = alerts.get_expiry_summary(store_id=1)
        print(f"  [OK] Summary generated")
        print(f"    - Expired: {summary['expired']['count']} items (N{summary['expired']['total_value']:.2f})")
        print(f"    - Expiring in 7 days: {summary['expiring_soon']['7_days']}")
        print(f"    - Expiring in 30 days: {summary['expiring_soon']['30_days']}")
        print(f"    - Expiring in 90 days: {summary['expiring_soon']['90_days']}")
        print(f"    - Requires immediate action: {summary['requires_action']} items")
        
        # Test 5: Generate alerts (existing method)
        print("\n[Test 5] Generating comprehensive alerts...")
        alert_report = alerts.generate_alerts(store_id=1)
        print(f"  [OK] Generated {alert_report['total_alerts']} alert(s)")
        for alert in alert_report['alerts']:
            print(f"    - [{alert['type'].upper()}] {alert['message']}")
        
        print("\n" + "=" * 60)
        print("[OK] All Enhanced Expiry Management tests passed!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        alerts.close()


if __name__ == "__main__":
    success = test_expiry_management()
    sys.exit(0 if success else 1)
