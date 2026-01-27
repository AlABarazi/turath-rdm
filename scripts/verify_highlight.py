import requests
import json
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def verify_highlighting(query):
    base_url = "https://127.0.0.1:5000/api/records"
    
    # Manually request highlighting
    # Note: Invenio might not pass this through unless configured, but let's try
    params = {
        "q": f"custom_fields.turath\:fulltext:{query}",
        "size": 1,
        # "highlight": '{"fields":{"custom_fields.turath:fulltext":{}}}' # Complex param, might not work in URL
    }
    
    # We'll try to rely on the server config first, but since that failed, 
    # we might need to look at the response more closely or debug server side.
    # Let's print the full response keys to be sure.
    
    print(f"Searching for: {params['q']}")
    
    try:
        response = requests.get(base_url, params=params, verify=False)
        response.raise_for_status()
        
        data = response.json()
        
        # Debug: Print top level keys
        # print("Response Keys:", data.keys())
        
        hits = data['hits']['hits']
        
        if not hits:
            print("No hits found.")
            return
            
        hit = hits[0]
        print(f"Hit ID: {hit['id']}")
        # print("Hit Keys:", hit.keys())
        
        if 'highlight' in hit:
            print("✅ 'highlight' field found in response!")
            print(json.dumps(hit['highlight'], indent=2, ensure_ascii=False))
        else:
            print("❌ 'highlight' field MISSING in response.")
            print("Double check: 1. Field mapping is 'text'. 2. RDM_SEARCH config is correct. 3. App restarted.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_highlighting("الرحمن")
