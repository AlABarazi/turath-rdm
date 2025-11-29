"""
HOCR Filesystem Sync Signal Handlers for Turath InvenioRDM.

Automatically syncs HOCR files from records to filesystem for fast search/annotation access.
"""

import os
import shutil
import logging
from invenio_rdm_records.records.api import RDMRecord
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_records.signals import (
    after_record_insert,
    after_record_update,
    before_record_delete
)
from .fulltext import extract_hocr_text

logger = logging.getLogger(__name__)

# Base directory for HOCR filesystem cache
# Default to local project directory for dev (invenio-cli run), /hocr_mount/books for prod (containers)
HOCR_MOUNT_BASE = os.environ.get('HOCR_MOUNT_BASE', os.path.join(os.getcwd(), 'hocr_mount/books'))


# Base directory for FilesystemSource (PDFs)
# Mounted at /opt/cantaloupe/images in docker
CANTALOUPE_MOUNT_BASE = os.path.join(os.getcwd(), 'cantaloupe-files')


def sync_files_to_filesystem(record):
    """
    Sync PDF and HOCR files from record to filesystem.
    
    Structure:
    - PDFs: {record_pid}/{filename.pdf}  (for Cantaloupe)
    - HOCR: {record_pid}/hocr/{filename.hocr} (for Search)
    
    Args:
        record: RDMRecord instance with files
    
    Returns:
        tuple: (pdf_count, hocr_count)
    """
    if not record.files.enabled:
        logger.debug(f"Files not enabled for record {record.pid.pid_value}")
        return 0, 0
    
    record_pid = record.pid.pid_value
    
    # Directories
    # PDF goes to root of record folder for cleaner IIIF IDs
    pdf_dir = os.path.join(CANTALOUPE_MOUNT_BASE, record_pid)
    hocr_dir = os.path.join(HOCR_MOUNT_BASE, record_pid, 'hocr')
    
    # Ensure directories exist
    try:
        os.makedirs(pdf_dir, exist_ok=True)
        os.makedirs(hocr_dir, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create directories for {record_pid}: {e}")
        return 0, 0
    
    pdf_count = 0
    hocr_count = 0
    
    for file_key in record.files.entries.keys():
        try:
            file_obj = record.files[file_key]
            
            # Determine target
            target_path = None
            if file_key.lower().endswith('.pdf'):
                target_path = os.path.join(pdf_dir, file_key)
                pdf_count += 1
            elif file_key.lower().endswith('.hocr'):
                target_path = os.path.join(hocr_dir, file_key)
                hocr_count += 1
            
            if target_path:
                with file_obj.get_stream('rb') as source:
                    content = source.read()
                with open(target_path, 'wb') as f:
                    f.write(content)
                logger.debug(f"Synced {file_key} to {target_path}")
                
        except Exception as e:
            logger.error(f"Failed to sync {file_key} for {record_pid}: {e}")
    
    if pdf_count > 0 or hocr_count > 0:
        logger.info(f"✅ Synced {pdf_count} PDFs and {hocr_count} HOCRs for {record_pid}")
    
    return pdf_count, hocr_count


def cleanup_filesystem_cache(record_pid):
    """
    Remove both PDF and HOCR caches for a record PID.
    """
    # Cleanup HOCR
    hocr_path = os.path.join(HOCR_MOUNT_BASE, record_pid)
    if os.path.exists(hocr_path):
        shutil.rmtree(hocr_path, ignore_errors=True)
        
    # Cleanup PDF (Cantaloupe)
    pdf_path = os.path.join(CANTALOUPE_MOUNT_BASE, record_pid)
    if os.path.exists(pdf_path):
        shutil.rmtree(pdf_path, ignore_errors=True)
        
    logger.info(f"🗑️ Cleaned up filesystem cache for {record_pid}")
    return True


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
def comprehensive_filesystem_sync(sender, record=None, **kwargs):
    """
    Comprehensive filesystem sync handler for all record lifecycle events.
    
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
    
    record_pid = record.pid.pid_value
    
    # =============================
    # SCENARIO 1: Soft Delete
    # =============================
    # InvenioRDM doesn't physically delete records!
    # It sets is_deleted=True flag instead
    if record.get('is_deleted', False):
        logger.info(f"🪦 Record {record_pid} soft deleted - cleaning up filesystem")
        cleanup_filesystem_cache(record_pid)
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
    # Publish or update - sync Files (PDF + HOCR)
    if record.files.enabled:
        pdf_count, hocr_count = sync_files_to_filesystem(record)
        
        if hocr_count > 0:
            # T7: Unified Search - Indexing
            try:
                logger.info(f"🔍 Extracting fulltext for {record_pid}...")
                fulltext = extract_hocr_text(record_pid)
                
                if fulltext:
                    # FIX: Use correct custom field path
                    custom_fields = record.setdefault('custom_fields', {})
                    current_val = custom_fields.get('turath:fulltext')
                    
                    # FIX: Prevent infinite loop - only update if changed
                    if current_val != fulltext:
                        custom_fields['turath:fulltext'] = fulltext
                        
                        # We must commit because we are in 'after_...' signal
                        record.commit()
                        current_rdm_records_service.indexer.index(record)
                        logger.info(f"✅ Indexed fulltext ({len(fulltext)} chars) for {record_pid}")
                    else:
                        logger.debug(f"Fulltext unchanged for {record_pid}, skipping re-index")
                else:
                    logger.warning(f"⚠️ No text extracted for {record_pid}")
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
    Clean up filesystem when record is HARD deleted (rare).
    """
    if not isinstance(record, RDMRecord):
        return
    
    logger.info(f"🗑️ Hard delete signal for {record.pid.pid_value}")
    cleanup_filesystem_cache(record.pid.pid_value)
