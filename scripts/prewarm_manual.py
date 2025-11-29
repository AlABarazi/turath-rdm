import requests
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Exact encoded base URL from your logs
base_url = "https://127.0.0.1:5000/iiif/2/https%3A%2F%2Fhost.docker.internal%3A5000%2Frecords%2Fabemh-brn03%2Ffiles%2F062_%D9%83%D8%B4%D9%81_%D8%A7%D9%84%D8%BA%D9%85%D8%A9__%D8%A7%D9%84%D8%AC%D8%B2%D8%A1_%D8%A7%D9%84%D8%AB%D9%84%D8%A7%D8%AB.pdf"

# Tiles observed in your error logs for Page 1
tiles = [
    "/p1/full/251,/0/default.jpg",            # Thumbnail
    "/p1/0,0,1004,1024/502,/0/default.jpg",   # Zoom level 1
    "/p1/0,1024,1004,452/502,/0/default.jpg", # Zoom level 1 (bottom)
    "/p1/0,512,512,512/512,/0/default.jpg",   # Detailed tile
    "/p1/512,512,492,512/492,/0/default.jpg", # Detailed tile
    "/p1/0,0,512,512/512,/0/default.jpg",     # Detailed tile
    "/p1/512,0,492,512/492,/0/default.jpg",   # Detailed tile
    "/p1/0,1024,512,452/512,/0/default.jpg",  # Detailed tile
    "/p1/512,1024,492,452/492,/0/default.jpg" # Detailed tile
]

print(f"🔥 Pre-warming tiles for pages 1-300 with retries...")
success = 0
total_tiles = 0

for page in range(1, 301):
    print(f"--- Page {page} ---")
    current_tiles = [t.replace("/p1/", f"/p{page}/") for t in tiles]
    
    for i, tile in enumerate(current_tiles, 1):
        url = base_url + tile
        # print(f"[{i}/{len(current_tiles)}] Fetching {tile} ... ", end="", flush=True)
        
        for attempt in range(3):
            try:
                start = time.time()
                resp = requests.get(url, verify=False, timeout=60) # 60s timeout
                elapsed = time.time() - start
                
                if resp.status_code == 200:
                    print(f"✅ P{page} Tile {i}: DONE in {elapsed:.1f}s")
                    success += 1
                    break # Next tile
                elif resp.status_code == 502:
                    print(f"⚠️ P{page} Tile {i}: 502 Timeout. Retrying ({attempt+1}/3)...")
                    time.sleep(2)
                else:
                    print(f"❌ P{page} Tile {i}: HTTP {resp.status_code}")
                    break
            except Exception as e:
                print(f"❌ ERROR: {e}")
                time.sleep(2)
        
        total_tiles += 1

print(f"\nPre-warm complete. {success}/{total_tiles} tiles cached.")
