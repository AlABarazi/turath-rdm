#!/usr/bin/env python3
"""
Test HOCR filesystem cleanup on record deletion.
Adapted from feature-hocr-fulltext-search test scripts.

Tests CRITICAL edge case discovered in HOCR project:
- Soft delete (is_deleted flag) triggers cleanup
- Hard delete (force) triggers cleanup
- HOCR directory removed
"""

from flask import current_app
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_rdm_records.records.api import RDMRecord
from invenio_access.permissions import system_identity
from invenio_app.factory import create_app
import os
import sys


def test_soft_delete(record_pid):
    """
    Test SOFT DELETE (the common case).
    
    CRITICAL: InvenioRDM uses soft delete by default!
    Records get is_deleted=True flag, not physically deleted.
    """
    print("\n" + "="*70)
    print("Test 1: SOFT DELETE (Normal UI Delete)")
    print("="*70 + "\n")
    
    hocr_mount_base = os.environ.get('HOCR_MOUNT_BASE', '/hocr_mount/books')
    hocr_dir = os.path.join(hocr_mount_base, record_pid, 'hocr')
    
    try:
        print(f"1. Checking HOCR directory BEFORE delete...")
        if os.path.exists(hocr_dir):
            hocr_files = [f for f in os.listdir(hocr_dir) if f.endswith('.hocr')]
            print(f"   ✅ Directory exists: {hocr_dir}")
            print(f"   ✅ Contains {len(hocr_files)} HOCR files")
        else:
            print(f"   ⚠️  Directory doesn't exist: {hocr_dir}")
            print("   (Create HOCR files first by publishing record with HOCR)")
            return False
        
        print(f"\n2. Performing SOFT DELETE on record: {record_pid}")
        print("   ⏳ Watch for signal message: '🪦 Record {pid} soft deleted - cleaning up HOCR'")
        
        # Soft delete via service (normal way)
        current_rdm_records_service.delete(system_identity, record_pid)
        
        print(f"   ✅ Record soft deleted")
        
        print(f"\n3. Checking HOCR directory AFTER delete...")
        if os.path.exists(hocr_dir):
            print(f"   ❌ Directory STILL exists: {hocr_dir}")
            print(f"   ❌ HOCR cleanup FAILED!")
            return False
        else:
            print(f"   ✅ Directory removed: {hocr_dir}")
            print(f"   ✅ HOCR cleanup SUCCESS!")
            return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hard_delete(record_pid):
    """
    Test HARD DELETE (rare case).
    
    NOTE: This requires CLI access and force flag.
    Most deletions are SOFT delete.
    """
    print("\n" + "="*70)
    print("Test 2: HARD DELETE (Force Delete via CLI)")
    print("="*70 + "\n")
    
    print("⚠️  HARD DELETE requires InvenioRDM shell access:")
    print("\n   invenio shell")
    print("   >>> from invenio_rdm_records.records.api import RDMRecord")
    print(f"   >>> record = RDMRecord.pid.resolve('{record_pid}')")
    print("   >>> record.delete(force=True)")
    print("   >>> db.session.commit()")
    print("\n   Look for signal: '🗑️ Hard delete signal for {pid}'")
    print("\n   Then verify HOCR directory removed:")
    print(f"   ls /hocr_mount/books/{record_pid}/")


def test_version_creation(record_pid):
    """
    Test NEW VERSION CREATION (CRITICAL edge case).
    
    Each version gets NEW PID!
    Old version should be cleaned up.
    """
    print("\n" + "="*70)
    print("Test 3: NEW VERSION CREATION")
    print("="*70 + "\n")
    
    hocr_mount_base = os.environ.get('HOCR_MOUNT_BASE', '/hocr_mount/books')
    
    try:
        print(f"1. Reading original record: {record_pid}")
        record = current_rdm_records_service.read(system_identity, record_pid)
        
        version_index = record.data.get('versions', {}).get('index', 1)
        print(f"   Current version: {version_index}")
        
        old_hocr_dir = os.path.join(hocr_mount_base, record_pid, 'hocr')
        if os.path.exists(old_hocr_dir):
            print(f"   ✅ Old version HOCR exists: {old_hocr_dir}")
        
        print(f"\n2. Creating NEW VERSION...")
        new_version = current_rdm_records_service.new_version(system_identity, record_pid)
        
        print(f"\n3. Publishing new version...")
        print("   ⏳ Watch for: '🔄 Record {new_pid} is new version {n}'")
        published = current_rdm_records_service.publish(system_identity, new_version.id)
        new_pid = published.id
        
        print(f"   ✅ New version published: {new_pid}")
        print(f"   ✅ This is version: {version_index + 1}")
        print(f"   ⚠️  Note: NEW PID created (not same as {record_pid})")
        
        print(f"\n4. Checking filesystem...")
        new_hocr_dir = os.path.join(hocr_mount_base, new_pid, 'hocr')
        
        if os.path.exists(new_hocr_dir):
            print(f"   ✅ New version HOCR synced: {new_hocr_dir}")
        else:
            print(f"   ℹ️  New version has no HOCR (if no files uploaded)")
        
        if os.path.exists(old_hocr_dir):
            print(f"   ⚠️  Old version HOCR still exists: {old_hocr_dir}")
            print(f"   (cleanup_old_versions function should remove this)")
        else:
            print(f"   ✅ Old version HOCR cleaned up: {old_hocr_dir}")
        
        return new_pid
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        if len(sys.argv) < 3:
            print("\nUsage: python test_hocr_sync_delete.py <test_type> <record_pid>")
            print("\nTest types:")
            print("  soft    - Test soft delete (normal UI delete)")
            print("  hard    - Show hard delete instructions")
            print("  version - Test new version creation")
            print("\nExamples:")
            print("  python test_hocr_sync_delete.py soft abc123-xyz")
            print("  python test_hocr_sync_delete.py version abc123-xyz")
            sys.exit(1)
        
        test_type = sys.argv[1]
        record_pid = sys.argv[2]
        
        if test_type == "soft":
            success = test_soft_delete(record_pid)
            if success:
                print("\n✅ SOFT DELETE TEST PASSED!")
            else:
                print("\n❌ SOFT DELETE TEST FAILED!")
        
        elif test_type == "hard":
            test_hard_delete(record_pid)
        
        elif test_type == "version":
            new_pid = test_version_creation(record_pid)
            if new_pid:
                print(f"\n✅ VERSION TEST COMPLETE!")
                print(f"   Old PID: {record_pid}")
                print(f"   New PID: {new_pid}")
        
        else:
            print(f"❌ Unknown test type: {test_type}")
            print("   Use: soft, hard, or version")
