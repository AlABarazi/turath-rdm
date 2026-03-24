"""
HOCR Filesystem Sync Signal Handlers for Turath InvenioRDM.

Automatically syncs HOCR files from records to filesystem for fast search/annotation access.
"""

import os
import shutil
import logging
import threading

from invenio_rdm_records.records.api import RDMRecord
from invenio_records.signals import (
    after_record_insert,
    after_record_update,
    before_record_delete
)

from .cantaloupe_mirror import cleanup_cantaloupe_record_dir, sync_hocr_files_parallel

logger = logging.getLogger(__name__)

# Base directory for HOCR filesystem cache
# Default to local project directory for dev (invenio-cli run), /hocr_mount/books for prod (containers)
HOCR_MOUNT_BASE = os.environ.get('HOCR_MOUNT_BASE', os.path.join(os.getcwd(), 'hocr_mount/books'))


def sync_hocr_to_filesystem(record):
    """
    Sync HOCR files from record to filesystem.
    
    Args:
        record: RDMRecord instance with files
    
    Returns:
        int: Number of HOCR files synced
    """
    if not record.files.enabled:
        logger.debug(f"Files not enabled for record {record.pid.pid_value}")
        return 0
    
    parent_id = record.parent.pid.pid_value
    hocr_dir = os.path.join(HOCR_MOUNT_BASE, parent_id, 'hocr')
    
    # Count HOCR files in record
    record_hocr_keys = [k for k in record.files.entries.keys() if k.endswith('.hocr')]
    
    # If record has no HOCR files but directory exists with files, preserve them
    # (supports --mirror-hocr-only workflow where HOCR is only on filesystem)
    if not record_hocr_keys and os.path.exists(hocr_dir):
        existing_files = [f for f in os.listdir(hocr_dir) if f.endswith('.hocr')]
        if existing_files:
            logger.info(f"Preserving {len(existing_files)} manually mirrored HOCR files for {parent_id}")
            return len(existing_files)
    
    # Remove old directory if exists (for updates when record has HOCR)
    if os.path.exists(hocr_dir):
        try:
            shutil.rmtree(hocr_dir)
            logger.info(f"Removed old HOCR cache for {parent_id}")
        except Exception as e:
            logger.error(f"Failed to remove old HOCR for {parent_id}: {e}")
            return 0
    
    # Create fresh directory
    try:
        os.makedirs(hocr_dir, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create HOCR directory for {parent_id}: {e}")
        return 0
    
    # Download all HOCR files in parallel (much faster than sequential for large books)
    hocr_count = sync_hocr_files_parallel(record, hocr_dir)
    if hocr_count > 0:
        logger.info("Synced %d HOCR files for %s (parallel)", hocr_count, parent_id)
    return hocr_count


def cleanup_hocr_from_filesystem(parent_id):
    """
    Remove HOCR filesystem cache for a parent ID.
    
    Args:
        parent_id: String parent ID
    
    Returns:
        bool: True if cleanup successful
    """
    hocr_base_dir = os.path.join(HOCR_MOUNT_BASE, parent_id)
    
    if not os.path.exists(hocr_base_dir):
        logger.debug(f"No HOCR cache to clean for {parent_id}")
        return True
    
    try:
        shutil.rmtree(hocr_base_dir)
        logger.info(f"🗑️ Cleaned up HOCR cache for {parent_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to cleanup HOCR for {parent_id}: {e}")
        return False


def cleanup_old_versions_for_parent(parent_id, except_pid=None):
    """
    Cleanup HOCR for old versions of a record when new version published.
    
    Args:
        parent_id: Parent record ID linking all versions
        except_pid: PID to exclude from cleanup (the new version)
    """
    # TODO: Query all records with this parent_id
    # For now, this is a placeholder for Phase 2
    logger.info(f"Cleanup old versions for parent {parent_id} (except {except_pid})")
    pass


# =============================
# COMPREHENSIVE SIGNAL HANDLER
# =============================
# Handles ALL scenarios: publish, update, version, soft delete, file changes
# Based on lessons from feature-hocr-fulltext-search project (Oct 2025)

@after_record_insert.connect
@after_record_update.connect
def comprehensive_hocr_handler(sender, record=None, **kwargs):
    """
    Dispatch background processing after a record is inserted or updated.

    Handles soft deletes synchronously (cleanup must happen immediately).
    All file processing (PDF→JPEG, HOCR sync, fulltext indexing) is
    delegated to the `process_record_files` Celery task so the publish
    request returns immediately.
    """
    if not isinstance(record, RDMRecord):
        return

    record_pid = record.pid.pid_value

    # Soft delete — clean up filesystem immediately
    if record.get("is_deleted", False):
        parent_id = record.parent.pid.pid_value
        logger.info("Record %s soft deleted — cleaning up", record_pid)
        cleanup_hocr_from_filesystem(parent_id)
        cleanup_cantaloupe_record_dir(parent_id)
        return

    # Skip old versions
    if not record.get("versions", {}).get("is_latest", True):
        return

    if not record.files.enabled:
        return

    # Run processing in a background thread so publish returns immediately.
    # We use a thread (not Celery) because the worker needs access to the
    # local cantaloupe-files/ filesystem which is only available in the
    # web process on the host machine.
    try:
        from flask import current_app
        app = current_app._get_current_object()

        def _background(app, pid):
            import time
            time.sleep(3)  # Let the publish transaction commit before we read the record
            with app.app_context():
                from .tasks import _do_process_record_files
                _do_process_record_files(pid)

        t = threading.Thread(target=_background, args=(app, record_pid), daemon=True)
        t.start()
        logger.info("Started background thread for %s", record_pid)
    except Exception as exc:
        logger.error("Failed to start background thread for %s: %s", record_pid, exc)


# =============================
# Signal: Hard Delete (Rare)
# =============================
@before_record_delete.connect
def handle_hard_delete(sender, record=None, **kwargs):
    """
    Clean up HOCR when record is HARD deleted (rare).
    
    NOTE: InvenioRDM normally uses SOFT delete (is_deleted flag).
    This signal only fires for:
    - Admin force delete via CLI
    - API delete with force flag
    - Direct database deletion
    
    Most deletions are handled in comprehensive_hocr_handler via is_deleted flag.
    """
    if not isinstance(record, RDMRecord):
        return
    
    parent_id = record.parent.pid.pid_value
    logger.info(f"🗑️ Hard delete signal for {record.pid.pid_value}")
    cleanup_hocr_from_filesystem(parent_id)
    cleanup_cantaloupe_record_dir(parent_id)
