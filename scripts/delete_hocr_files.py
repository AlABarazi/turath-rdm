#!/usr/bin/env python3
"""
Safely delete HOCR files from InvenioRDM records.

Default behavior: Delete HOCR files ONLY from record storage (S3/MinIO).
Filesystem cache and fulltext index are preserved by default (needed for Mirador viewer and search).

Usage:
    # Delete from specific record (only from storage)
    python scripts/delete_hocr_files.py --record-id abc12-xyz34 --yes

    # Delete from all records (only from storage)
    python scripts/delete_hocr_files.py --all --yes

    # Also delete from filesystem cache
    python scripts/delete_hocr_files.py --record-id abc12-xyz34 --delete-filesystem --yes

    # Also clear fulltext index
    python scripts/delete_hocr_files.py --record-id abc12-xyz34 --delete-index --yes

    # Full cleanup (all 3 locations)
    python scripts/delete_hocr_files.py --record-id abc12-xyz34 --delete-filesystem --delete-index --yes

    # Dry-run to see what would be deleted
    python scripts/delete_hocr_files.py --record-id abc12-xyz34 --dry-run

Environment:
    RDM_API_TOKEN: API token for authentication
    HOCR_MOUNT_BASE: Base directory for HOCR filesystem cache (default: ./hocr_mount/books)
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

requests.packages.urllib3.disable_warnings()


def load_token(env_path: str = ".env") -> Optional[str]:
    """Load RDM_API_TOKEN from environment or .env file."""
    token = os.getenv("RDM_API_TOKEN")
    if token:
        return token
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("RDM_API_TOKEN="):
                        return line.strip().split("=", 1)[1]
        except Exception:
            pass
    return None


def get_auth_headers(token: str) -> Dict[str, str]:
    """Get authorization headers."""
    return {"Authorization": f"Bearer {token}"}


def get_json_headers(token: str) -> Dict[str, str]:
    """Get JSON headers with auth."""
    return {
        **get_auth_headers(token),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def list_hocr_files(record_id: str, token: str, base_url: str) -> Tuple[bool, List[str], Optional[str]]:
    """
    List HOCR files in a record.
    
    Returns:
        (success, hocr_files, parent_id)
    """
    url = f"{base_url}/api/records/{record_id}"
    response = requests.get(url, headers=get_auth_headers(token), verify=False)
    
    if response.status_code == 404:
        return False, [], None
    
    if not response.ok:
        print(f"  ❌ Failed to fetch record: {response.status_code}")
        return False, [], None
    
    record = response.json()
    
    # Get parent ID
    parent_id = record.get("parent", {}).get("id")
    if not parent_id:
        print(f"  ⚠️ Record has no parent ID")
        return False, [], None
    
    # Get HOCR files
    files = record.get("files", {}).get("entries", {})
    hocr_files = [filename for filename in files.keys() if filename.endswith(".hocr")]
    
    return True, hocr_files, parent_id


def delete_hocr_from_record(record_id: str, hocr_files: List[str], token: str, base_url: str, dry_run: bool = False) -> Tuple[bool, int]:
    """
    Delete HOCR files from record storage via API.
    
    InvenioRDM workflow for removing files (creates new version):
    1. Create new version draft
    2. Import files from previous version
    3. Delete unwanted HOCR files from draft
    4. Publish draft as new version
    
    Returns:
        (success, count_deleted)
    """
    if not hocr_files:
        return True, 0
    
    if dry_run:
        print(f"  [DRY-RUN] Would create new version without {len(hocr_files)} HOCR files")
        return True, len(hocr_files)
    
    # Step 1: Create new version draft
    new_version_url = f"{base_url}/api/records/{record_id}/versions"
    response = requests.post(new_version_url, headers=get_json_headers(token), verify=False)
    
    if not response.ok:
        print(f"    ❌ Failed to create new version: {response.status_code} - {response.text[:200]}")
        return False, 0
    
    draft = response.json()
    draft_id = draft.get("id")
    
    if not draft_id:
        print(f"    ❌ No draft ID in response")
        return False, 0
    
    print(f"    📝 Created new version draft: {draft_id}")
    
    # Step 2: Import files from previous version
    import_url = f"{base_url}/api/records/{draft_id}/draft/actions/files-import"
    response = requests.post(import_url, headers=get_json_headers(token), verify=False)
    
    if not response.ok:
        print(f"    ❌ Failed to import files: {response.status_code}")
        return False, 0
    
    print(f"    📥 Imported files from previous version")
    
    # Step 3: Delete HOCR files from draft
    deleted_count = 0
    
    for filename in hocr_files:
        file_url = f"{base_url}/api/records/{draft_id}/draft/files/{filename}"
        response = requests.delete(file_url, headers=get_auth_headers(token), verify=False)
        
        if response.ok or response.status_code == 404:
            deleted_count += 1
        else:
            print(f"    ⚠️ Failed to delete {filename}: {response.status_code}")
    
    print(f"    🗑️ Deleted {deleted_count}/{len(hocr_files)} HOCR files from draft")
    
    if deleted_count == 0:
        print(f"    ⚠️ No files deleted, discarding draft")
        # Discard the draft since nothing was deleted
        discard_url = f"{base_url}/api/records/{draft_id}/draft"
        requests.delete(discard_url, headers=get_auth_headers(token), verify=False)
        return False, 0
    
    # Step 4: Ensure required metadata is present (publication_date)
    # Fetch the draft to check metadata
    draft_url = f"{base_url}/api/records/{draft_id}/draft"
    response = requests.get(draft_url, headers=get_auth_headers(token), verify=False)
    
    if response.ok:
        draft_data = response.json()
        metadata = draft_data.get("metadata", {})
        
        # Add publication_date if missing (use today's date)
        if "publication_date" not in metadata:
            from datetime import date
            metadata["publication_date"] = date.today().isoformat()
            
            # Update the draft with required metadata
            update_payload = {"metadata": metadata}
            response = requests.put(
                draft_url,
                headers=get_json_headers(token),
                json=update_payload,
                verify=False
            )
            
            if not response.ok:
                print(f"    ⚠️ Failed to update metadata: {response.status_code}")
                # Continue anyway, publish might still work
    
    # Step 5: Publish the draft as new version
    publish_url = f"{base_url}/api/records/{draft_id}/draft/actions/publish"
    response = requests.post(publish_url, headers=get_json_headers(token), verify=False)
    
    if not response.ok:
        print(f"    ❌ Failed to publish new version: {response.status_code} - {response.text[:200]}")
        print(f"    ⚠️ Draft {draft_id} exists but unpublished - delete manually if needed")
        return False, deleted_count
    
    new_record = response.json()
    new_version = new_record.get("versions", {}).get("index", "?")
    print(f"    ✅ Published new version (v{new_version}) without HOCR files")
    
    return True, deleted_count


def delete_hocr_from_filesystem(parent_id: str, hocr_mount_base: str, dry_run: bool = False) -> bool:
    """
    Delete HOCR files from filesystem cache.
    
    Returns:
        success
    """
    hocr_dir = os.path.join(hocr_mount_base, parent_id)
    
    if not os.path.exists(hocr_dir):
        return True  # Already clean
    
    if dry_run:
        print(f"  [DRY-RUN] Would delete filesystem cache: {hocr_dir}")
        return True
    
    try:
        shutil.rmtree(hocr_dir)
        return True
    except Exception as e:
        print(f"    ❌ Failed to delete filesystem cache: {e}")
        return False


def clear_fulltext_field(record_id: str, token: str, base_url: str, dry_run: bool = False) -> bool:
    """
    Clear custom_fields.turath:fulltext from record and reindex.
    
    Returns:
        success
    """
    if dry_run:
        print(f"  [DRY-RUN] Would clear custom_fields.turath:fulltext from record")
        return True
    
    # Fetch current record
    url = f"{base_url}/api/records/{record_id}"
    response = requests.get(url, headers=get_auth_headers(token), verify=False)
    
    if not response.ok:
        print(f"    ❌ Failed to fetch record for fulltext clearing: {response.status_code}")
        return False
    
    record = response.json()
    
    # Check if fulltext field exists
    custom_fields = record.get("custom_fields", {})
    if "turath:fulltext" not in custom_fields:
        return True  # Already clean
    
    # Remove fulltext field
    del custom_fields["turath:fulltext"]
    
    # Get ETag for conditional update
    etag = response.headers.get("ETag", "").strip('"')
    
    # Update record
    headers = get_json_headers(token)
    if etag:
        headers["If-Match"] = etag
    
    update_payload = {"custom_fields": custom_fields}
    
    response = requests.put(
        url,
        headers=headers,
        json=update_payload,
        verify=False
    )
    
    if not response.ok:
        print(f"    ❌ Failed to update record: {response.status_code}")
        return False
    
    return True


def process_record(
    record_id: str,
    token: str,
    base_url: str,
    hocr_mount_base: str,
    delete_filesystem: bool = False,
    delete_index: bool = False,
    dry_run: bool = False
) -> Tuple[bool, Dict[str, any]]:
    """
    Process a single record for HOCR deletion.
    
    Returns:
        (success, stats)
    """
    stats = {
        "record_id": record_id,
        "hocr_count": 0,
        "storage_deleted": False,
        "filesystem_deleted": False,
        "index_cleared": False,
    }
    
    print(f"\nProcessing record {record_id}...")
    
    # List HOCR files
    success, hocr_files, parent_id = list_hocr_files(record_id, token, base_url)
    
    if not success:
        print(f"  ❌ Failed to fetch record")
        return False, stats
    
    stats["hocr_count"] = len(hocr_files)
    
    if len(hocr_files) == 0:
        print(f"  ℹ️ No HOCR files found in record storage")
        return True, stats
    
    print(f"  Found {len(hocr_files)} HOCR files in record storage")
    
    # Step 1: Delete from record storage (always, unless dry-run)
    print(f"  [1/1] Deleting from record storage...", end=" ")
    success, deleted_count = delete_hocr_from_record(record_id, hocr_files, token, base_url, dry_run)
    
    if success:
        stats["storage_deleted"] = True
        if dry_run:
            print(f"✓ [DRY-RUN] Would delete {deleted_count} files")
        else:
            print(f"✓ ({deleted_count} files deleted)")
    else:
        print(f"❌ Failed")
        return False, stats
    
    # Optional: Delete from filesystem
    if delete_filesystem and parent_id:
        print(f"  [OPTIONAL] Deleting from filesystem...", end=" ")
        if delete_hocr_from_filesystem(parent_id, hocr_mount_base, dry_run):
            stats["filesystem_deleted"] = True
            print("✓")
        else:
            print("❌ Failed")
    elif not dry_run:
        print(f"  ✅ Filesystem cache preserved (Mirador still functional)")
    
    # Optional: Clear fulltext index
    if delete_index:
        print(f"  [OPTIONAL] Clearing fulltext index...", end=" ")
        if clear_fulltext_field(record_id, token, base_url, dry_run):
            stats["index_cleared"] = True
            print("✓")
        else:
            print("❌ Failed")
    elif not dry_run:
        print(f"  ✅ Fulltext index preserved (search still functional)")
    
    if not dry_run:
        print(f"✅ Record {record_id} processed successfully")
    else:
        print(f"✓ [DRY-RUN] Record {record_id} would be processed")
    
    return True, stats


def get_all_records(base_url: str, token: str) -> List[str]:
    """Get all record IDs from the repository."""
    record_ids = []
    url = f"{base_url}/api/records?size=100&sort=newest&allversions=true"
    
    while url:
        response = requests.get(url, headers=get_auth_headers(token), verify=False)
        
        if not response.ok:
            print(f"❌ Failed to list records: {response.status_code}")
            break
        
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        
        for hit in hits:
            record_ids.append(hit["id"])
        
        url = data.get("links", {}).get("next")
    
    return record_ids


def main():
    parser = argparse.ArgumentParser(
        description="Safely delete HOCR files from InvenioRDM records",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Delete from specific record (only from storage)
  python scripts/delete_hocr_files.py --record-id abc12-xyz34 --yes

  # Delete from all records (only from storage)
  python scripts/delete_hocr_files.py --all --yes

  # Also delete from filesystem cache
  python scripts/delete_hocr_files.py --record-id abc12-xyz34 --delete-filesystem --yes

  # Full cleanup (all 3 locations)
  python scripts/delete_hocr_files.py --record-id abc12-xyz34 --delete-filesystem --delete-index --yes

  # Dry-run to preview
  python scripts/delete_hocr_files.py --all --dry-run
        """
    )
    
    # Scope
    scope_group = parser.add_mutually_exclusive_group(required=True)
    scope_group.add_argument("--record-id", help="Delete from specific record")
    scope_group.add_argument("--all", action="store_true", help="Delete from all records")
    
    # Safety
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without making changes")
    parser.add_argument("--yes", action="store_true", help="Confirm deletion (required for actual deletion)")
    
    # Optional additional cleanup
    parser.add_argument("--delete-filesystem", action="store_true",
                        help="Also delete HOCR from filesystem cache (disables Mirador search/overlay)")
    parser.add_argument("--delete-index", action="store_true",
                        help="Also clear fulltext from OpenSearch index (disables full-text search)")
    
    # Environment
    parser.add_argument("--base-url", default="https://127.0.0.1:5000",
                        help="InvenioRDM base URL (default: https://127.0.0.1:5000)")
    parser.add_argument("--hocr-mount-base",
                        default=os.environ.get('HOCR_MOUNT_BASE', './hocr_mount/books'),
                        help="Base directory for HOCR filesystem cache")
    
    args = parser.parse_args()
    
    # Validation: require --yes for actual deletion
    if not args.dry_run and not args.yes:
        print("❌ Actual deletion requires --yes flag (or use --dry-run to preview)")
        print("   Run with --dry-run to see what would be deleted")
        return 1
    
    # Load token
    token = load_token()
    if not token:
        print("❌ RDM_API_TOKEN not found in environment or .env file")
        return 1
    
    # Get record IDs to process
    if args.record_id:
        record_ids = [args.record_id]
    else:
        print("Fetching all records...")
        record_ids = get_all_records(args.base_url, token)
        if not record_ids:
            print("No records found")
            return 0
    
    # Show summary
    print("\n" + "=" * 60)
    print("HOCR DELETION SUMMARY")
    print("=" * 60)
    print(f"Records to process: {len(record_ids)}")
    print(f"Base URL: {args.base_url}")
    print(f"HOCR mount base: {args.hocr_mount_base}")
    print()
    print("Default operations:")
    print("  ✓ Delete from record storage (S3/MinIO)")
    print("  ✗ Keep filesystem cache (needed by Mirador)")
    print("  ✗ Keep fulltext index (needed for search)")
    print()
    print("Additional operations (if flags provided):")
    print(f"  --delete-filesystem: {'YES' if args.delete_filesystem else 'NO'}")
    print(f"  --delete-index: {'YES' if args.delete_index else 'NO'}")
    print()
    
    if args.dry_run:
        print("🔍 DRY-RUN MODE (no changes will be made)")
    else:
        print("⚠️ ACTUAL DELETION MODE")
    
    print("=" * 60)
    
    if not args.dry_run and not args.yes:
        print("\n❌ Aborting: --yes flag required for actual deletion")
        return 1
    
    # Process records
    total_hocr_deleted = 0
    successful_records = 0
    failed_records = 0
    
    for record_id in record_ids:
        success, stats = process_record(
            record_id=record_id,
            token=token,
            base_url=args.base_url,
            hocr_mount_base=args.hocr_mount_base,
            delete_filesystem=args.delete_filesystem,
            delete_index=args.delete_index,
            dry_run=args.dry_run
        )
        
        if success:
            successful_records += 1
            total_hocr_deleted += stats["hocr_count"]
        else:
            failed_records += 1
    
    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Total records processed: {len(record_ids)}")
    print(f"Successful: {successful_records}")
    print(f"Failed: {failed_records}")
    print(f"HOCR files deleted from record storage: {total_hocr_deleted}")
    
    if args.delete_filesystem:
        print(f"Filesystem cache: Deleted")
    else:
        print(f"Filesystem cache: Preserved")
    
    if args.delete_index:
        print(f"Fulltext index: Cleared")
    else:
        print(f"Fulltext index: Preserved")
    
    if args.dry_run:
        print("\n🔍 This was a DRY-RUN. No actual changes were made.")
        print("   Remove --dry-run and add --yes to perform actual deletion.")
    
    print("=" * 60)
    
    return 0 if failed_records == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
