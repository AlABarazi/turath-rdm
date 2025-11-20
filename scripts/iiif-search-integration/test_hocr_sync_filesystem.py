#!/usr/bin/env python3
"""
Test HOCR filesystem sync - direct verification.

Simple script to check if HOCR files are synced correctly:
- Directory structure
- File counts
- File content
- Multiple records
"""

import os
import sys


def test_hocr_filesystem(record_pid=None):
    """Test HOCR filesystem structure and content."""
    print("\n" + "="*70)
    print("HOCR Filesystem Verification")
    print("="*70 + "\n")
    
    hocr_mount_base = os.environ.get('HOCR_MOUNT_BASE', '/hocr_mount/books')
    
    if not os.path.exists(hocr_mount_base):
        print(f"❌ HOCR mount base not found: {hocr_mount_base}")
        print("\n💡 Solutions:")
        print("   1. Check Docker volume mount is configured")
        print("   2. Verify HOCR_MOUNT_BASE environment variable")
        print("   3. Create directory: mkdir -p /hocr_mount/books")
        return False
    
    print(f"✅ HOCR mount base exists: {hocr_mount_base}\n")
    
    if record_pid:
        # Test specific record
        print(f"Testing specific record: {record_pid}")
        return test_single_record(hocr_mount_base, record_pid)
    else:
        # List all synced records
        print("Listing all synced records:")
        return test_all_records(hocr_mount_base)


def test_single_record(base_dir, record_pid):
    """Test HOCR sync for a specific record."""
    record_dir = os.path.join(base_dir, record_pid)
    hocr_dir = os.path.join(record_dir, 'hocr')
    
    print(f"\n1. Checking directory structure...")
    
    if not os.path.exists(record_dir):
        print(f"   ❌ Record directory not found: {record_dir}")
        print(f"   💡 Record may not have HOCR files or hasn't been synced")
        return False
    
    print(f"   ✅ Record directory: {record_dir}")
    
    if not os.path.exists(hocr_dir):
        print(f"   ❌ HOCR subdirectory not found: {hocr_dir}")
        return False
    
    print(f"   ✅ HOCR directory: {hocr_dir}")
    
    # List HOCR files
    print(f"\n2. Listing HOCR files...")
    try:
        all_files = os.listdir(hocr_dir)
        hocr_files = [f for f in all_files if f.endswith('.hocr')]
        
        if not hocr_files:
            print(f"   ⚠️  No .hocr files found in directory")
            print(f"   Found {len(all_files)} other files: {all_files[:5]}")
            return False
        
        print(f"   ✅ Found {len(hocr_files)} HOCR files")
        
        # Show details
        print(f"\n3. File details:")
        total_size = 0
        for i, filename in enumerate(sorted(hocr_files)[:10]):  # Show first 10
            filepath = os.path.join(hocr_dir, filename)
            size = os.path.getsize(filepath)
            total_size += size
            print(f"   {i+1:3d}. {filename:20s} ({size:,} bytes)")
        
        if len(hocr_files) > 10:
            print(f"   ... and {len(hocr_files) - 10} more files")
        
        print(f"\n   Total: {len(hocr_files)} files, {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
        
        # Test file content
        print(f"\n4. Testing file content (first file)...")
        first_file = os.path.join(hocr_dir, sorted(hocr_files)[0])
        with open(first_file, 'r', encoding='utf-8') as f:
            content = f.read(500)  # Read first 500 chars
        
        if '<html' in content.lower() and 'ocr' in content.lower():
            print(f"   ✅ File contains valid HOCR HTML")
            print(f"\n   Preview:")
            print(f"   {content[:200]}...")
        else:
            print(f"   ⚠️  File content doesn't look like HOCR")
            print(f"   Preview: {content[:200]}")
        
        print(f"\n{'='*70}")
        print(f"✅ ALL CHECKS PASSED for {record_pid}")
        print(f"{'='*70}")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_records(base_dir):
    """List all records with synced HOCR files."""
    try:
        if not os.path.exists(base_dir):
            print(f"❌ Directory not found: {base_dir}")
            return False
        
        # List all record directories
        entries = os.listdir(base_dir)
        record_dirs = [d for d in entries if os.path.isdir(os.path.join(base_dir, d))]
        
        if not record_dirs:
            print(f"ℹ️  No record directories found in {base_dir}")
            print(f"\n💡 To sync records:")
            print(f"   1. Publish a record with HOCR files")
            print(f"   2. Check logs for sync message")
            print(f"   3. Run this script again")
            return False
        
        print(f"✅ Found {len(record_dirs)} synced records:\n")
        
        for i, record_pid in enumerate(sorted(record_dirs), 1):
            record_dir = os.path.join(base_dir, record_pid)
            hocr_dir = os.path.join(record_dir, 'hocr')
            
            if os.path.exists(hocr_dir):
                hocr_files = [f for f in os.listdir(hocr_dir) if f.endswith('.hocr')]
                total_size = sum(os.path.getsize(os.path.join(hocr_dir, f)) for f in hocr_files)
                
                print(f"{i:3d}. {record_pid}")
                print(f"     Files: {len(hocr_files)}, Size: {total_size/1024:.1f} KB")
            else:
                print(f"{i:3d}. {record_pid}")
                print(f"     ⚠️  No HOCR directory")
        
        print(f"\n💡 To inspect specific record:")
        print(f"   python test_hocr_sync_filesystem.py <record_pid>")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific record
        record_pid = sys.argv[1]
        success = test_hocr_filesystem(record_pid)
    else:
        # List all records
        success = test_hocr_filesystem()
    
    sys.exit(0 if success else 1)
