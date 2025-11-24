import sys
import os
import random
import string
from invenio_app.factory import create_app
from invenio_search import current_search_client

# Setup app context
app = create_app()

def generate_large_text(pages=1000, chars_per_page=2000):
    """Generate a large string simulating book content."""
    print(f"Generating text for {pages} pages ({chars_per_page} chars/page)...")
    # Use some Arabic to be realistic
    arabic_sample = "المملكة العربية السعودية تاريخ وحضارة "
    filler = arabic_sample * 50  # ~1000 chars
    full_text = []
    for i in range(pages):
        full_text.append(f"Page {i}: {filler} " + "".join(random.choices(string.ascii_letters, k=500)))
    
    return "\n".join(full_text)

def run_probe():
    with app.app_context():
        index_alias = "turath-inveniordm-rdmrecords-records"
        
        # 1. Inspect Mapping
        print(f"🔍 Inspecting mapping for {index_alias}...")
        try:
            mapping = current_search_client.indices.get_mapping(index=index_alias)
            # Get the first (and likely only) index name from the response
            actual_index = list(mapping.keys())[-1] # Use the last one (latest version)
            print(f"   Targeting concrete index: {actual_index}")
            
            properties = mapping[actual_index]['mappings']['properties']
            
            cf_mapping = properties.get('custom_fields', {})
            print(f"   'custom_fields' type: {cf_mapping.get('type', 'object')}")
            print(f"   'custom_fields' dynamic: {cf_mapping.get('dynamic', 'default')}")
            
            # Check if we can add arbitrary fields
            is_dynamic = cf_mapping.get('dynamic') == 'true'
            print(f"   Dynamic Custom Fields Allowed? {is_dynamic}")
            
        except Exception as e:
            print(f"❌ Failed to get mapping: {e}")
            return

        # 2. Generate Payload
        large_text = generate_large_text(1000)
        payload_size_mb = len(large_text.encode('utf-8')) / (1024 * 1024)
        print(f"📦 Payload Size: {payload_size_mb:.2f} MB")

        # 3. Attempt Indexing
        doc_id = "probe-test-large-payload"
        body = {
            "id": doc_id,
            "custom_fields": {
                "turath:fulltext_test": large_text  # Using a namespaced field
            },
            # Minimal required fields to pass validation if any (though we are bypassing marshmallow here)
            "access": {"record": "public", "files": "public"},
            "metadata": {"title": "Probe Test"} 
        }
        
        print(f"🚀 Attempting to index document {doc_id}...")
        try:
            current_search_client.index(
                index=actual_index,  # Use concrete index
                id=doc_id,
                body=body,
                refresh=True
            )
            print("✅ SUCCESS: Large payload indexed without error.")
            
            # 3.5 Verify Storage (Get Source)
            print("🔍 Fetching document to verify storage...")
            doc = current_search_client.get(index=actual_index, id=doc_id)
            stored_cf = doc['_source'].get('custom_fields', {})
            if "turath:fulltext_test" in stored_cf:
                print(f"   ✅ Field 'turath:fulltext_test' exists in _source. Length: {len(stored_cf['turath:fulltext_test'])}")
            else:
                print("   ❌ Field 'turath:fulltext_test' MISSING from _source (silently discarded).")

            # 4. Verify Searchability
            print("🔎 Verifying searchability...")
            # Search for a unique string from the end of the text
            unique_term = "Page 999"
            res = current_search_client.search(
                index=actual_index,  # Use concrete index
                body={
                    "query": {
                        "term": {
                            "custom_fields.turath:fulltext_test.keyword": unique_term 
                            # Note: Text fields are usually analyzed. 
                            # If mapping is not dynamic, this might fail or be 'keyword' if default.
                        }
                    }
                }
            )
            print(f"   Search hits: {res['hits']['total']['value']}")
            
            # Cleanup
            print("🧹 Cleaning up...")
            current_search_client.delete(index=actual_index, id=doc_id)
            print("   Cleanup complete.")
            
        except Exception as e:
            print(f"❌ FAIL: Indexing failed. Reason: {e}")

if __name__ == "__main__":
    run_probe()
