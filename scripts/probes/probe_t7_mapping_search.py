import sys
from invenio_app.factory import create_app
from invenio_search import current_search_client

app = create_app()

def run_probe():
    with app.app_context():
        index = "probe-test-fulltext"
        
        print(f"🧹 Cleaning up {index}...")
        if current_search_client.indices.exists(index=index):
            current_search_client.indices.delete(index=index)
            
        print(f"🔨 Creating index {index} with 'text' mapping...")
        current_search_client.indices.create(index=index, body={
            "mappings": {
                "properties": {
                    "my_fulltext": {"type": "text"}  # Standard analyzed text
                }
            }
        })
        
        print("🚀 Indexing document...")
        current_search_client.index(
            index=index, 
            body={"my_fulltext": "The quick brown fox jumps over the lazy dog. History of the kingdom."}, 
            refresh=True
        )
        
        print("🔎 Searching for 'history' (partial match)...")
        res = current_search_client.search(index=index, body={
            "query": {
                "match": {
                    "my_fulltext": "History" 
                }
            }
        })
        
        hits = res['hits']['total']['value']
        print(f"✅ Hits: {hits}")
        
        if hits > 0:
            print("🎉 Success: Text mapping allows searching!")
        else:
            print("❌ Fail: Still no hits.")

        # Cleanup
        current_search_client.indices.delete(index=index)

if __name__ == "__main__":
    run_probe()
