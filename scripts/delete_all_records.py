import requests
import os
import sys

requests.packages.urllib3.disable_warnings()

TOKEN = os.getenv("RDM_API_TOKEN")
BASE_URL = "https://127.0.0.1:5000"

if not TOKEN:
    print("Error: RDM_API_TOKEN not set")
    sys.exit(1)

def h_auth():
    return {"Authorization": f"Bearer {TOKEN}"}

def get_all_records():
    # Fetch all published records
    url = f"{BASE_URL}/api/records?size=1000&sort=newest&allversions=true"
    try:
        r = requests.get(url, headers=h_auth(), verify=False)
        if not r.ok:
            print(f"Failed to list records: {r.status_code} {r.text}")
            return []
        return r.json()['hits']['hits']
    except Exception as e:
        print(f"Connection failed: {e}")
        return []

def delete_record(rec_id):
    print(f"Deleting {rec_id}...")
    url = f"{BASE_URL}/api/records/{rec_id}"
    r = requests.delete(url, headers=h_auth(), verify=False)
    if r.status_code == 204:
        print("  Deleted (204).")
    elif r.status_code == 403:
        print("  Forbidden (403). Cannot delete published record via API without admin/config?")
    else:
        print(f"  Failed: {r.status_code} {r.text}")

def main():
    print("Fetching records...")
    records = get_all_records()
    print(f"Found {len(records)} records.")
    
    if not records:
        print("No records to delete.")
        return

    print("Starting deletion...")
    for rec in records:
        delete_record(rec['id'])

if __name__ == "__main__":
    main()
