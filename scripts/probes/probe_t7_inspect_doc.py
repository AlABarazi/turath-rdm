import sys
from invenio_app.factory import create_app
from invenio_search import current_search_client

app = create_app()

def run_probe():
    with app.app_context():
        index_alias = "turath-inveniordm-rdmrecords-records"
        pid = "z1jz2-qt181"
        
        print(f"🔎 Inspecting doc for PID {pid}...")
        
        # Find doc by PID
        res = current_search_client.search(
            index=index_alias,
            body={
                "query": {
                    "term": {
                        "id": pid # Wait, ID in ES is UUID usually, but let's try recid
                    }
                }
            }
        )
        
        if res['hits']['total']['value'] == 0:
            # Try searching metadata.recid
            res = current_search_client.search(
                index=index_alias,
                body={
                    "query": {
                        "term": {
                            "metadata.recid": pid 
                        }
                    }
                }
            )
            
        if res['hits']['total']['value'] == 0:
            print("❌ Doc not found in index.")
            return

        doc = res['hits']['hits'][0]['_source']
        print(f"✅ Doc found. ID: {res['hits']['hits'][0]['_id']}")
        
        cf = doc.get('custom_fields', {})
        if 'turath:fulltext' in cf:
            text = cf['turath:fulltext']
            print(f"✅ 'custom_fields.turath:fulltext' field present.")
            print(f"   Length: {len(text)}")
            print(f"   Preview: {text[:100]}...")
        else:
            print("❌ 'turath:fulltext' field MISSING from custom_fields.")
            print(f"   Keys: {list(cf.keys())}")

if __name__ == "__main__":
    run_probe()
