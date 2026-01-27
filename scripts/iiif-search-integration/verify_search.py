import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def search_fulltext(query):
    base_url = "https://127.0.0.1:5000/api/records"
    
    # Construct the query parameter for the custom field
    # Note: Invenio search syntax for nested fields usually uses dot notation
    # We will try a simple query string first
    
    params = {
        "q": f"custom_fields.turath\:fulltext:{query}",
        "size": 10
    }
    
    print(f"Searching for: {params['q']}")
    
    try:
        response = requests.get(base_url, params=params, verify=False)
        response.raise_for_status()
        
        data = response.json()
        total = data['hits']['total']
        print(f"Found {total} hits")
        
        for hit in data['hits']['hits']:
            print(f"- ID: {hit['id']}")
            print(f"  Title: {hit['metadata']['title']}")
            # print(f"  Score: {hit['score']}")
            
    except Exception as e:
        print(f"Error: {e}")
        if 'response' in locals():
            print(f"Response: {response.text}")

if __name__ == "__main__":
    # Search for a word known to be in 005.hocr ("الرحمن")
    search_fulltext("الرحمن")
