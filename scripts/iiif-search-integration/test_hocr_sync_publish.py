#!/usr/bin/env python3
"""
Test HOCR filesystem sync on record publish.
Adapted from feature-hocr-fulltext-search test scripts.

Tests:
- Signal fires on publish
- HOCR files synced to /hocr_mount/
- Filesystem structure correct
"""

from flask import current_app
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_access.permissions import system_identity
from datetime import datetime
from invenio_app.factory import create_app
import os
import sys


def test_hocr_sync_on_publish(record_pid=None):
    """Test HOCR sync when publishing a record via API."""
    print("\n" + "="*70)
    print("Testing HOCR Filesystem Sync on Publish")
    print("="*70 + "\n")
    
    hocr_mount_base = os.environ.get('HOCR_MOUNT_BASE', '/hocr_mount/books')
    
    try:
        if record_pid:
            # Test with existing record (edit → republish)
            print(f"1. Testing with existing record: {record_pid}")
            print("   (Simulating edit → republish)")
            
            # Read the record
            record = current_rdm_records_service.read(system_identity, record_pid)
            print(f"   ✅ Record found: {record.data.get('metadata', {}).get('title', 'N/A')}")
            
            # Create draft from published record
            draft = current_rdm_records_service.edit(system_identity, record_pid)
            print(f"   ✅ Draft created for editing")
            
            # Republish (this should trigger signal)
            print("\n2. Publishing record...")
            print("   ⏳ Watch for signal message: '✅ Synced X HOCR files for record {}'")
            record = current_rdm_records_service.publish(system_identity, draft.id)
            test_pid = record.id
            
        else:
            # Create new test record
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            data = {
                "files": {"enabled": False},  # Will test without files first
                "metadata": {
                    "title": f"HOCR Sync Test - {timestamp}",
                    "resource_type": {"id": "image-photo"},
                    "creators": [
                        {
                            "person_or_org": {
                                "type": "personal",
                                "family_name": "Test",
                                "given_name": "HOCR Sync"
                            }
                        }
                    ],
                    "publication_date": "2025-01-01"
                }
            }
            
            print("1. Creating new test record...")
            draft = current_rdm_records_service.create(system_identity, data)
            print(f"   ✅ Draft created: {draft.id}")
            
            print("\n2. Publishing record...")
            print("   ⏳ Watch for signal message: '✅ Synced X HOCR files for record {}'")
            record = current_rdm_records_service.publish(system_identity, draft.id)
            test_pid = record.id
        
        print(f"   ✅ Record published: {test_pid}")        
        # Check filesystem
        print("\n3. Checking filesystem...")
        hocr_dir = os.path.join(hocr_mount_base, test_pid, 'hocr')
        
        if os.path.exists(hocr_dir):
            hocr_files = [f for f in os.listdir(hocr_dir) if f.endswith('.hocr')]
            print(f"   ✅ HOCR directory exists: {hocr_dir}")
            print(f"   ✅ Found {len(hocr_files)} HOCR files")
            
            if hocr_files:
                for f in hocr_files[:3]:  # Show first 3
                    file_path = os.path.join(hocr_dir, f)
                    size = os.path.getsize(file_path)
                    print(f"      - {f} ({size} bytes)")
            else:
                print("   ℹ️  No HOCR files (record has no HOCR files)")
        else:
            print(f"   ⚠️  HOCR directory NOT found: {hocr_dir}")
            print("   This is expected if record has no HOCR files")
        
        print("\n" + "="*70)
        print("Test Complete!")
        print("="*70)
        print(f"\nRecord PID: {test_pid}")
        print(f"Expected HOCR path: {hocr_dir}")
        
        print("\n📝 Verification Checklist:")
        print("   - [ ] Signal message appeared in logs above")
        print("   - [ ] HOCR directory created (if files present)")
        print("   - [ ] HOCR files match record files")
        
        return test_pid
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_with_hocr_record():
    """Provide instructions for testing with actual HOCR files."""
    print("\n" + "="*70)
    print("To test with actual HOCR files:")
    print("="*70)
    print("\n1. Find a record with HOCR files:")
    print("   curl -k 'https://127.0.0.1:5000/api/records?size=10' | jq '.hits.hits[] | select(.files.entries | keys[] | endswith(\".hocr\")) | .id'")
    print("\n2. Run this script with that record PID:")
    print("   python test_hocr_sync_publish.py <record_pid>")
    print("\n3. Or create a new record with HOCR files via upload script")


if __name__ == "__main__":
    # FORCE S3 CONFIGURATION VIA ENV VARS (Before create_app)
    # Invenio-S3 configuration keys
    os.environ['INVENIO_S3_ENDPOINT_URL'] = 'http://127.0.0.1:9000'
    os.environ['INVENIO_S3_ACCESS_KEY_ID'] = 'minioadmin'
    os.environ['INVENIO_S3_SECRET_ACCESS_KEY'] = 'minioadmin'
    os.environ['INVENIO_S3_url_style'] = 'path'  # Lowercase might be key for some versions
    os.environ['INVENIO_S3_URL_STYLE'] = 'path'
    
    # Standard AWS keys (just in case)
    os.environ['AWS_ENDPOINT_URL'] = 'http://127.0.0.1:9000'
    os.environ['AWS_ACCESS_KEY_ID'] = 'minioadmin'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'minioadmin'
    os.environ['AWS_S3_ADDRESSING_STYLE'] = 'path'
    
    app = create_app()
    
    with app.app_context():
        if len(sys.argv) > 1:
            # Test with existing record
            record_pid = sys.argv[1]
            test_hocr_sync_on_publish(record_pid)
        else:
            # Test with new record (no files)
            result_pid = test_hocr_sync_on_publish()
            
            if result_pid:
                print("\n" + "="*70)
                test_with_hocr_record()
