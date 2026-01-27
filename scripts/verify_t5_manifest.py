import requests
import json
import sys

# Disable warnings for self-signed certs
requests.packages.urllib3.disable_warnings()

BASE_URL = "https://127.0.0.1:5000"

def get_first_record_id():
    """Get the PID of the first record found."""
    try:
        r = requests.get(f"{BASE_URL}/api/records", params={"size": 1}, verify=False)
        r.raise_for_status()
        hits = r.json().get("hits", {}).get("hits", [])
        if not hits:
            print("❌ No records found in InvenioRDM")
            return None
        return hits[0]["id"]
    except Exception as e:
        print(f"❌ Failed to fetch records: {e}")
        return None

def verify_manifest(record_pid):
    """Fetch manifest and check for search service."""
    manifest_url = f"{BASE_URL}/api/iiif/record:{record_pid}/manifest"
    print(f"🔍 Fetching manifest: {manifest_url}")
    
    try:
        r = requests.get(manifest_url, verify=False)
        r.raise_for_status()
        manifest = r.json()
        
        # Check for service block
        services = manifest.get("service", [])
        if isinstance(services, dict):
            services = [services]
            
        search_service = None
        for s in services:
            if s.get("profile") == "http://iiif.io/api/search/0/search":
                search_service = s
                break
        
        if search_service:
            print("✅ SUCCESS: Search service found in manifest!")
            print(json.dumps(search_service, indent=2))
            
            # Check autocomplete
            autocomplete = search_service.get("service")
            if autocomplete and autocomplete.get("profile") == "http://iiif.io/api/search/0/autocomplete":
                 print("✅ SUCCESS: Autocomplete service found!")
            else:
                 print("⚠️  WARNING: Autocomplete service MISSING or incorrect profile")
                 
            return True
        else:
            print("❌ FAILURE: Search service NOT found in manifest")
            print("Services found:", json.dumps(services, indent=2))
            return False
            
    except Exception as e:
        print(f"❌ Failed to fetch/parse manifest: {e}")
        return False

if __name__ == "__main__":
    pid = get_first_record_id()
    if pid:
        success = verify_manifest(pid)
        sys.exit(0 if success else 1)
    else:
        sys.exit(1)
