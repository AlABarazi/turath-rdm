#!/usr/bin/env python3
"""Test script to verify HOCR files can be accessed from Celery task context."""

from celery import shared_task
from flask import current_app
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_access.permissions import system_identity
from invenio_app.factory import create_app


@shared_task
def test_hocr_file_access(record_id):
    """Test task to verify file access from Celery context."""
    try:
        print(f"\n{'='*60}")
        print(f"Celery Task: Testing File Access for Record {record_id}")
        print(f"{'='*60}\n")
        
        # Read the record
        record = current_rdm_records_service.read(system_identity, record_id)
        print(f"✅ Step 1: Record read successfully")
        print(f"   Record ID: {record.id}")
        print(f"   Title: {record.data.get('metadata', {}).get('title', 'N/A')}")
        
        # Check for HOCR files
        hocr_files = []
        print(f"\nDEBUG: Checking files structure...")
        print(f"   'files' in record.data: {'files' in record.data}")
        if 'files' in record.data:
            print(f"   files.enabled: {record.data['files'].get('enabled')}")
            print(f"   files.entries type: {type(record.data['files'].get('entries'))}")
            
            entries = record.data['files'].get('entries', [])
            # Entries might be a dict with file keys or a list
            if isinstance(entries, dict):
                for key, file_entry in entries.items():
                    if key.endswith('.hocr'):
                        hocr_files.append({'key': key, **file_entry})
            elif isinstance(entries, list):
                for file_entry in entries:
                    if isinstance(file_entry, dict) and file_entry.get('key', '').endswith('.hocr'):
                        hocr_files.append(file_entry)
        
        print(f"\n✅ Step 2: Found {len(hocr_files)} HOCR file(s)")
        for f in hocr_files:
            print(f"   - {f['key']} ({f['size']} bytes)")
        
        if not hocr_files:
            return {
                'success': False,
                'error': 'No HOCR files found in record'
            }
        
        # Try to access first HOCR file content
        file_key = hocr_files[0]['key']
        print(f"\n⏳ Step 3: Attempting to read file content: {file_key}")
        
        # Access file directly from record
        # Re-read record with resolved files
        record = current_rdm_records_service.record_cls.pid.resolve(record_id)
        
        # Get the file object
        file_obj = record.files[file_key]
        print(f"   File object type: {type(file_obj)}")
        
        # Open file stream using get_stream method
        file_stream = file_obj.get_stream('rb')
        # Read first 200 characters
        content_preview = file_stream.read(200).decode('utf-8', errors='ignore')
        file_stream.close()
        
        print(f"✅ Step 4: File content accessible!")
        print(f"\n   Preview (first 200 chars):")
        print(f"   {content_preview[:200]}...")
        
        return {
            'success': True,
            'record_id': record_id,
            'hocr_files_found': len(hocr_files),
            'test_file': file_key,
            'content_accessible': True,
            'preview': content_preview[:100]
        }
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def run_test(record_id):
    """Run the test synchronously for development."""
    print("\n" + "="*60)
    print("Testing HOCR File Access from Celery Task")
    print("="*60 + "\n")
    
    app = create_app()
    with app.app_context():
        print("🔄 Method 1: Running task synchronously (for testing)...")
        result = test_hocr_file_access(record_id)
        
        print("\n" + "="*60)
        print("Synchronous Test Complete")
        print("="*60)
        print(f"Result: {result}")
        
        print("\n" + "="*60)
        print("🔄 Method 2: Queueing task asynchronously (production mode)...")
        print("="*60)
        
        task = test_hocr_file_access.delay(record_id)
        print(f"\n✅ Task queued!")
        print(f"   Task ID: {task.id}")
        print(f"\n⏳ Waiting for result (timeout: 30s)...")
        
        try:
            async_result = task.get(timeout=30)
            print(f"\n✅ Async task completed!")
            print(f"   Result: {async_result}")
        except Exception as e:
            print(f"\n❌ Async task failed: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_celery_file_access.py <record_id>")
        print("\nExample:")
        print("  python test_celery_file_access.py er0yr-89563")
        sys.exit(1)
    
    record_id = sys.argv[1]
    run_test(record_id)
