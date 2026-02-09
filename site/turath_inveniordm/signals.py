"""
HOCR Filesystem Sync Signal Handlers for Turath InvenioRDM.

Automatically syncs HOCR files from records to filesystem for fast search/annotation access.
"""

import os
import shutil
import logging
from contextvars import ContextVar
from pathlib import Path

from invenio_rdm_records.records.api import RDMRecord
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_records.signals import (
    after_record_insert,
    after_record_update,
    before_record_delete
)

from .cantaloupe_mirror import (
    cleanup_cantaloupe_record_dir,
    create_dimensions_cache_from_hocr_dir,
    get_cantaloupe_files_base,
    mirror_pdf_to_cantaloupe_filesystem,
)
from .fulltext import extract_hocr_text

logger = logging.getLogger(__name__)

_fulltext_update_in_progress = ContextVar(
    "turath_fulltext_update_in_progress",
    default=False,
)

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
    
    record_pid = record.pid.pid_value
    hocr_dir = os.path.join(HOCR_MOUNT_BASE, record_pid, 'hocr')
    
    # Remove old directory if exists (for updates)
    if os.path.exists(hocr_dir):
        try:
            shutil.rmtree(hocr_dir)
            logger.info(f"Removed old HOCR cache for {record_pid}")
        except Exception as e:
            logger.error(f"Failed to remove old HOCR for {record_pid}: {e}")
            return 0
    
    # Create fresh directory
    try:
        os.makedirs(hocr_dir, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create HOCR directory for {record_pid}: {e}")
        return 0
    
    # Copy all .hocr files
    hocr_count = 0
    for file_key in record.files.entries.keys():
        if file_key.endswith('.hocr'):
            try:
                file_obj = record.files[file_key]
                with file_obj.get_stream('rb') as source:
                    content = source.read()
                
                target_path = os.path.join(hocr_dir, file_key)
                with open(target_path, 'wb') as f:
                    f.write(content)
                
                hocr_count += 1
                logger.debug(f"Synced {file_key} for {record_pid}")
            except Exception as e:
                logger.error(f"Failed to sync {file_key} for {record_pid}: {e}")
    
    if hocr_count > 0:
        logger.info(f"✅ Synced {hocr_count} HOCR files for record {record_pid}")
    
    return hocr_count


def cleanup_hocr_from_filesystem(record_pid):
    """
    Remove HOCR filesystem cache for a record PID.
    
    Args:
        record_pid: String record PID
    
    Returns:
        bool: True if cleanup successful
    """
    hocr_base_dir = os.path.join(HOCR_MOUNT_BASE, record_pid)
    
    if not os.path.exists(hocr_base_dir):
        logger.debug(f"No HOCR cache to clean for {record_pid}")
        return True
    
    try:
        shutil.rmtree(hocr_base_dir)
        logger.info(f"🗑️ Cleaned up HOCR cache for {record_pid}")
        return True
    except Exception as e:
        logger.error(f"Failed to cleanup HOCR for {record_pid}: {e}")
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
    Comprehensive HOCR sync handler for all record lifecycle events.
    
    Handles:
    - New record publish
    - Record edit → republish
    - New version creation
    - Soft delete (is_deleted flag)
    - File additions/removals
    
    CRITICAL: Based on lessons learned:
    - InvenioRDM uses SOFT DELETE (is_deleted flag, not signal)
    - Each version gets NEW PID (not same PID)
    - Old versions remain in DB with is_latest=false
    """
    if not isinstance(record, RDMRecord):
        return

    if _fulltext_update_in_progress.get():
        return
    
    record_pid = record.pid.pid_value
    
    # =============================
    # SCENARIO 1: Soft Delete
    # =============================
    # InvenioRDM doesn't physically delete records!
    # It sets is_deleted=True flag instead
    if record.get('is_deleted', False):
        logger.info(f"🪦 Record {record_pid} soft deleted - cleaning up HOCR")
        cleanup_hocr_from_filesystem(record_pid)
        cleanup_cantaloupe_record_dir(record_pid)
        return
    
    # =============================
    # SCENARIO 2: Old Version (skip)
    # =============================
    # Each version gets a NEW PID
    # Old versions have is_latest=false and should be skipped
    if not record.get('versions', {}).get('is_latest', True):
        logger.info(f"📜 Record {record_pid} is old version - skipping sync")
        return
    
    # =============================
    # SCENARIO 3: New Version (cleanup old)
    # =============================
    # If this is version 2+, cleanup old version's HOCR
    version_index = record.get('versions', {}).get('index', 1)
    if version_index > 1:
        logger.info(f"🔄 Record {record_pid} is new version {version_index}")
        parent_id = record.get('parent', {}).get('id')
        if parent_id:
            cleanup_old_versions_for_parent(parent_id, except_pid=record_pid)
    
    # =============================
    # SCENARIO 4 & 5: Normal Sync
    # =============================
    # Publish or update - sync HOCR files
    if record.files.enabled:
        hocr_count = sync_hocr_to_filesystem(record)
        if hocr_count == 0:
            logger.info(f"ℹ️ Record {record_pid} has no HOCR files")
        try:
            mirror_pdf_to_cantaloupe_filesystem(record, record_pid)
            hocr_dir = os.path.join(HOCR_MOUNT_BASE, record_pid, 'hocr')
            dims_file = (
                get_cantaloupe_files_base()
                / record_pid
                / "dimensions.json"
            )
            create_dimensions_cache_from_hocr_dir(
                Path(hocr_dir),
                dims_file,
            )
        except Exception as e:
            logger.error(
                "❌ Failed to mirror PDF/dimensions for %s: %s",
                record_pid,
                e,
            )

        if hocr_count == 0:
            return

        try:
            logger.info(f"🔍 Extracting fulltext for {record_pid}...")
            fulltext = extract_hocr_text(record_pid)
            if not fulltext:
                logger.warning(f"⚠️ No text extracted for {record_pid}")
                return

            existing = (record.get('custom_fields') or {}).get('turath:fulltext')
            if existing == fulltext:
                logger.info(
                    "ℹ️ Fulltext already up-to-date for %s; skipping commit",
                    record_pid,
                )
                return

            record.setdefault('custom_fields', {})['turath:fulltext'] = fulltext

            token = _fulltext_update_in_progress.set(True)
            try:
                record.commit()
                current_rdm_records_service.indexer.index(record)
            finally:
                _fulltext_update_in_progress.reset(token)

            logger.info(
                "✅ Indexed fulltext (%s chars) for %s",
                len(fulltext),
                record_pid,
            )
        except Exception as e:
            logger.error(f"❌ Failed to index fulltext for {record_pid}: {e}")

    else:
        logger.debug(f"Record {record_pid} has files disabled")


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
    
    logger.info(f"🗑️ Hard delete signal for {record.pid.pid_value}")
    cleanup_hocr_from_filesystem(record.pid.pid_value)
    cleanup_cantaloupe_record_dir(record.pid.pid_value)
