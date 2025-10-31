#!/usr/bin/env python3
"""Test script to verify signals fire for record deletion."""

from flask import current_app
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_access.permissions import system_identity
from invenio_app.factory import create_app

def test_delete_signal():
    """Test deletion signal by creating and then deleting a record."""
    print("\n" + "="*60)
    print("Testing DELETE Signal - Signal Verification")
    print("="*60 + "\n")
    
    try:
        # First, create a new test record
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data = {
            "files": {"enabled": False},
            "metadata": {
                "title": f"Delete Test Record - {timestamp}",
                "resource_type": {"id": "image-photo"},
                "creators": [
                    {
                        "person_or_org": {
                            "type": "personal",
                            "family_name": "Delete",
                            "given_name": "Test"
                        }
                    }
                ],
                "publication_date": "2025-01-01"
            }
        }
        
        print("1. Creating a test record...")
        draft = current_rdm_records_service.create(system_identity, data)
        record = current_rdm_records_service.publish(system_identity, draft.id)
        test_record_pid = record.id
        print(f"   ✅ Record created and published: {test_record_pid}\n")
        
        print(f"2. Now deleting record: {test_record_pid}")
        print("   ⏳ Watch for: '🗑️  SIGNAL TEST: Record deleted' message...\n")
        
        # Delete the record
        current_rdm_records_service.delete(system_identity, test_record_pid)
        
        print(f"   ✅ Record {test_record_pid} deleted successfully!")
        
        print("\n" + "="*60)
        print("Test Complete!")
        print("="*60)
        print("\n⚠️  Check output above for signal message:")
        print("   Look for: '🗑️  SIGNAL TEST: Record deleted - ID: {}'".format(test_record_pid))
        print("\n📝 Result: Signals fire for DELETE = YES/NO")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        test_delete_signal()
