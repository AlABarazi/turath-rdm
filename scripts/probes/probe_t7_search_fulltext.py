import sys
from invenio_app.factory import create_app
from invenio_search import current_search_client

app = create_app()

def run_probe():
    with app.app_context():
        index_alias = "turath-inveniordm-rdmrecords-records"
        term = "الأمانة"
        
        print(f"🔎 Searching {index_alias}...")
        
        # 1. Specific Field Search
        print(f"1. Field Search (custom_fields.turath:fulltext:{term})")
        res = current_search_client.search(
            index=index_alias,
            body={
                "query": {
                    "match": {
                        "custom_fields.turath:fulltext": term
                    }
                }
            }
        )
        hits1 = res['hits']['total']['value']
        print(f"   Hits: {hits1}")
        
        # 2. Default Query String (simulating UI q=term)
        print(f"2. Query String Search ({term})")
        res = current_search_client.search(
            index=index_alias,
            body={
                "query": {
                    "query_string": {
                        "query": f"custom_fields.turath\:fulltext:{term}" # Escaped colon for query_string
                    }
                }
            }
        )
        hits2 = res['hits']['total']['value']
        print(f"   Hits: {hits2}")

if __name__ == "__main__":
    run_probe()
