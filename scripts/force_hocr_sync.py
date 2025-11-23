import os
import sys
from invenio_app.factory import create_app
from invenio_rdm_records.proxies import current_rdm_records
from invenio_pidstore.errors import PIDDoesNotExistError
from turath_inveniordm.signals import sync_hocr_to_filesystem

# Setup app context
app = create_app()

def force_sync(pid_value):
    with app.app_context():
        try:
            # Let's get the internal record object directly
            from invenio_pidstore.models import PersistentIdentifier
            from invenio_rdm_records.records.api import RDMRecord
            
            # Resolve PID to UUID
            pid = PersistentIdentifier.get('recid', pid_value)
            # Fetch record
            record = RDMRecord.get_record(pid.object_uuid)
            
            print(f"Found record {pid_value}")
            count = sync_hocr_to_filesystem(record)
            
            # Determine mount path
            mount_base = os.environ.get('HOCR_MOUNT_BASE', os.path.join(os.getcwd(), 'hocr_mount/books'))
            print(f"Synced {count} files to {mount_base}/{pid_value}/hocr")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/force_hocr_sync.py <PID>")
        sys.exit(1)
    
    force_sync(sys.argv[1])
