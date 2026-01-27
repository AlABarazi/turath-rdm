import sys
from invenio_app.factory import create_app
from invenio_search import current_search_client

app = create_app()

def run_probe():
    with app.app_context():
        index_alias = "turath-inveniordm-rdmrecords-records"
        
        print(f"🔎 Inspecting mapping for {index_alias}...")
        mapping = current_search_client.indices.get_mapping(index=index_alias)
        
        # Get concrete index name
        actual_index = list(mapping.keys())[-1]
        props = mapping[actual_index]['mappings']['properties']
        
        cf = props.get('custom_fields', {}).get('properties', {})
        fulltext_map = cf.get('turath:fulltext', 'MISSING')
        
        print(f"   Field 'custom_fields.turath:fulltext': {fulltext_map}")
        
        if fulltext_map == 'MISSING':
            print("❌ Field is not in the mapping (Dynamic mapping might not have created it yet or it's ignored)")
        elif isinstance(fulltext_map, dict):
            ft_type = fulltext_map.get('type', 'unknown')
            print(f"   Type: {ft_type}")
            if ft_type == 'text':
                print("✅ Success: Mapped as 'text' (Analyzed). Phrase search will work.")
            elif ft_type == 'keyword':
                print("⚠️  Warning: Mapped as 'keyword'. Phrase search will FAIL (only exact match of whole book).")
            else:
                print(f"ℹ️  Mapped as {ft_type}")

if __name__ == "__main__":
    run_probe()
