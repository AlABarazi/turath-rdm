"""
Background Celery tasks for Turath InvenioRDM.

Handles PDF-to-image conversion, HOCR filesystem sync, and fulltext indexing
after a record is published or updated.
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


def _do_process_record_files(record_pid: str) -> None:
    """
    Core logic: convert PDF→JPEGs, sync HOCR, index fulltext.

    Called from:
    - Background thread in the web process (dev / mixed setup)
    - Celery task in process_record_files (production Docker)
    """
    from invenio_db import db
    from invenio_rdm_records.proxies import current_rdm_records_service
    from invenio_rdm_records.records.api import RDMRecord

    from .cantaloupe_mirror import mirror_pdf_pages_to_cantaloupe_filesystem
    from .fulltext import extract_hocr_text
    from .signals import sync_hocr_to_filesystem

    record = RDMRecord.pid.resolve(record_pid)

    if not record.files.enabled:
        return

    parent_id = record.parent.pid.pid_value

    # Step 1: PDF → JPEG pages
    pages_dir = mirror_pdf_pages_to_cantaloupe_filesystem(record, record_pid)
    if pages_dir:
        logger.info("Converted PDF pages for %s → %s", record_pid, pages_dir)
    else:
        logger.info("No PDF found for %s; skipping image conversion", record_pid)

    # Step 2: HOCR → filesystem
    hocr_count = sync_hocr_to_filesystem(record)
    logger.info("Synced %d HOCR files for %s (parent: %s)", hocr_count, record_pid, parent_id)

    if hocr_count == 0:
        return

    # Step 3: Fulltext extraction + indexing
    fulltext = extract_hocr_text(parent_id)
    if not fulltext:
        logger.warning("No fulltext extracted for %s", record_pid)
        return

    # Skip commit if fulltext unchanged (prevents signal re-dispatch loop)
    existing = (record.get("custom_fields") or {}).get("turath:fulltext")
    if existing == fulltext:
        logger.info("Fulltext unchanged for %s; skipping re-index", record_pid)
        return

    record.setdefault("custom_fields", {})["turath:fulltext"] = fulltext
    record.commit()
    db.session.commit()
    current_rdm_records_service.indexer.index(record)

    logger.info(
        "Indexed fulltext (%d chars) for %s (parent: %s)",
        len(fulltext), record_pid, parent_id,
    )


@shared_task(ignore_result=True, bind=True, max_retries=3, default_retry_delay=60)
def process_record_files(self, record_pid: str) -> None:
    """
    Celery task wrapper around _do_process_record_files.

    Used in production (full Docker) where the worker has cantaloupe-files/
    mounted and can run the processing asynchronously.
    """
    try:
        _do_process_record_files(record_pid)
    except Exception as exc:
        logger.exception("process_record_files failed for %s: %s", record_pid, exc)
        raise self.retry(exc=exc)
