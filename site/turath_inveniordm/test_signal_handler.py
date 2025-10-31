"""Test signal handler to verify signal reliability."""

from flask import current_app
from invenio_rdm_records.services.signals import post_publish_signal
from invenio_records.signals import after_record_delete


def log_record_published(sender, pid=None, **kwargs):
    """Log when a record is published."""
    current_app.logger.info(f"🔔 SIGNAL TEST: Record published - PID: {pid}")
    print(f"🔔 SIGNAL TEST: Record published - PID: {pid}")


def log_record_deleted(sender, record=None, **kwargs):
    """Log when a record is deleted."""
    record_id = record.get('id') if record else 'unknown'
    current_app.logger.info(f"🗑️  SIGNAL TEST: Record deleted - ID: {record_id}")
    print(f"🗑️  SIGNAL TEST: Record deleted - ID: {record_id}")


def register_test_handlers(app):
    """Register test signal handlers."""
    post_publish_signal.connect(log_record_published)
    after_record_delete.connect(log_record_deleted)
    app.logger.info("✅ Test signal handlers registered!")
    print("✅ Test signal handlers registered!")
