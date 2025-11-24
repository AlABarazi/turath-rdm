import os
import sys
from invenio_app.factory import create_app
from invenio_pidstore.models import PersistentIdentifier
from invenio_rdm_records.records.api import RDMRecord
from invenio_rdm_records.proxies import current_rdm_records_service
from turath_inveniordm.fulltext import extract_hocr_text

app = create_app()

def backfill_record(pid_value):
    with app.app_context():
        try:
            # Resolve PID
            pid = PersistentIdentifier.get('recid', pid_value)
            record = RDMRecord.get_record(pid.object_uuid)
            
            print(f"📖 Processing record {pid_value}...")
            
            # 1. Extract Text
            text = extract_hocr_text(pid_value)
            if not text:
                print("⚠️  No HOCR text found. Did you sync files first?")
                return

            print(f"📝 Extracted {len(text)} characters.")
            
            # 2. Inject into Record
            # We inject into 'custom_fields' because Invenio indexer respects it
            # Top-level 'fulltext' was ignored by the dumper
            record.setdefault('custom_fields', {})['turath:fulltext'] = text
            
            # 3. Commit & Index
            print("💾 Committing and Indexing...")
            record.commit()
            current_rdm_records_service.indexer.index(record)
            
            print("✅ Success!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/backfill_fulltext.py <PID>")
        sys.exit(1)
    
    backfill_record(sys.argv[1])
