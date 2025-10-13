#!/usr/bin/env python3
"""Test script to verify signals fire for API upload."""

from flask import current_app
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_access.permissions import system_identity
from datetime import datetime
from invenio_app.factory import create_app

def test_api_upload():
    """Create and publish a test record via API."""
    print("\n" + "="*60)
    print("Testing API Upload - Signal Verification")
    print("="*60 + "\n")
    
    # Create test record data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data = {
        "files": {"enabled": False},  # Disable files for this test
        "metadata": {
            "title": f"Signal Test Record API - {timestamp}",
            "resource_type": {"id": "image-photo"},
            "creators": [
                {
                    "person_or_org": {
                        "type": "personal",
                        "family_name": "Test",
                        "given_name": "Signal"
                    }
                }
            ],
            "publication_date": "2025-01-01"
        }
    }
    
    try:
        # Create draft
        print("1. Creating draft...")
        draft = current_rdm_records_service.create(system_identity, data)
        print(f"   ✅ Draft created: {draft.id}")
        
        # Publish record
        print("\n2. Publishing record...")
        print("   ⏳ Watch for: '🔔 SIGNAL TEST: Record published' message...")
        record = current_rdm_records_service.publish(system_identity, draft.id)
        print(f"   ✅ Record published: {record.id}")
        
        print("\n" + "="*60)
        print("Test Complete!")
        print("="*60)
        print(f"\nRecord PID: {record.id}")
        print("\n⚠️  Check logs above for signal message:")
        print("   Look for: '🔔 SIGNAL TEST: Record published - PID: {}'".format(record.id))
        print("\n📝 Result: Signals fire for API upload = YES/NO")
        
        return record.id
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        test_api_upload()
