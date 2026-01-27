import time
import os
from bs4 import BeautifulSoup

HOCR_PATH = "hocr_mount/books/z1jz2-qt181/hocr/001.hocr"

def run_probe():
    if not os.path.exists(HOCR_PATH):
        print(f"❌ Test file not found: {HOCR_PATH}")
        return

    print("📖 Reading HOCR file...")
    with open(HOCR_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    print("⏱️  Starting 500-page parse simulation...")
    start_time = time.time()
    
    total_text_len = 0
    for i in range(500):
        soup = BeautifulSoup(content, 'lxml')
        # Extract text same way Search Service does (or simpler)
        # We just want raw text for indexing
        text = soup.get_text(" ", strip=True)
        total_text_len += len(text)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"✅ Parsed 500 pages in {duration:.2f} seconds")
    print(f"   Average per page: {duration/500:.4f}s")
    print(f"   Total text extracted: {total_text_len} chars")

if __name__ == "__main__":
    run_probe()
