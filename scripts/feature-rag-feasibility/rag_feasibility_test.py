#!/usr/bin/env python3
"""
RAG Feasibility Test Script

This script tests the ability to extract metadata and full-text (HOCR) from
the Turath InvenioRDM APIs for use in a Retrieval-Augmented Generation (RAG) pipeline.

Usage:
  python rag_feasibility_test.py --record-id <RECORD_PID> [--token <API_TOKEN>]

It connects to the local instance (https://127.0.0.1:5000), fetches metadata,
downloads HOCR files, and attempts to extract raw text suitable for an LLM.
"""

import argparse
import requests
import json
import time
import os
import sys
import tempfile
from bs4 import BeautifulSoup
import urllib3

# Suppress insecure request warnings for local self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://127.0.0.1:5000"

def get_record_metadata(record_pid, headers):
    """Fetch record metadata from the API."""
    print(f"[*] Fetching metadata for record {record_pid}...")
    start_time = time.time()
    url = f"{BASE_URL}/api/records/{record_pid}"
    
    response = requests.get(url, headers=headers, verify=False)
    
    if response.status_code != 200:
        print(f"[!] Error fetching record: {response.status_code} - {response.text}")
        return None, 0
        
    data = response.json()
    elapsed = time.time() - start_time
    print(f"[+] Metadata fetched in {elapsed:.2f} seconds.")
    
    # Extract key fields for RAG context
    metadata = data.get("metadata", {})
    extracted = {
        "title": metadata.get("title"),
        "description": metadata.get("description"),
        "creators": [c.get("person_or_org", {}).get("name") for c in metadata.get("creators", [])],
        "publication_date": metadata.get("publication_date"),
        "subjects": [s.get("subject") for s in metadata.get("subjects", [])]
    }
    
    return extracted, elapsed

def get_hocr_files(record_pid, headers):
    """List HOCR files attached to the record."""
    print(f"[*] Fetching file list for record {record_pid}...")
    start_time = time.time()
    url = f"{BASE_URL}/api/records/{record_pid}/files"
    
    response = requests.get(url, headers=headers, verify=False)
    
    if response.status_code != 200:
        print(f"[!] Error fetching files: {response.status_code} - {response.text}")
        return [], 0
        
    data = response.json()
    entries = data.get("entries", {})
    
    hocr_files = []
    
    # Handle both dict and list structures depending on API version
    if isinstance(entries, dict):
        for filename, info in entries.items():
            if filename.endswith(".hocr"):
                hocr_files.append({
                    "filename": filename,
                    "url": info.get("links", {}).get("content", f"{BASE_URL}/api/records/{record_pid}/files/{filename}/content")
                })
    elif isinstance(entries, list):
         for entry in entries:
            filename = entry.get("key", "")
            if filename.endswith(".hocr"):
                hocr_files.append({
                    "filename": filename,
                    "url": entry.get("links", {}).get("content", f"{BASE_URL}/api/records/{record_pid}/files/{filename}/content")
                })
                
    hocr_files.sort(key=lambda x: x["filename"])
    elapsed = time.time() - start_time
    print(f"[+] Found {len(hocr_files)} HOCR files in {elapsed:.2f} seconds.")
    
    return hocr_files, elapsed

def extract_text_from_hocr(hocr_content):
    """Parse HOCR HTML/XML and extract raw text."""
    soup = BeautifulSoup(hocr_content, 'html.parser')
    words = soup.find_all(class_='ocrx_word')
    return ' '.join(w.get_text(strip=True) for w in words) if words else ''

def download_and_extract_text(hocr_files, headers, limit=5):
    """Download HOCR files and extract text."""
    print(f"[*] Downloading and extracting text from top {limit} HOCR files...")
    
    total_text = ""
    total_time = 0
    
    for i, file_info in enumerate(hocr_files[:limit]):
        start_time = time.time()
        url = file_info["url"]
        print(f"  -> Fetching {file_info['filename']}...")
        
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            text = extract_text_from_hocr(response.content)
            total_text += f"\n--- Page {file_info['filename']} ---\n{text}\n"
        else:
            print(f"  [!] Failed to download {file_info['filename']}")
            
        elapsed = time.time() - start_time
        total_time += elapsed
        
    print(f"[+] Extracted {len(total_text)} characters in {total_time:.2f} seconds.")
    return total_text, total_time

def main():
    parser = argparse.ArgumentParser(description="Test API for RAG Pipeline")
    parser.add_argument("--record-id", required=True, help="InvenioRDM Record PID (e.g., 7cxkj-kvp29)")
    parser.add_argument("--token", help="RDM API Token (optional for public records)")
    parser.add_argument("--limit", type=int, default=5, help="Number of HOCR pages to extract (default: 5)")
    args = parser.parse_args()

    headers = {}
    if args.token:
        headers["Authorization"] = f"Bearer {args.token}"

    print(f"=== Starting RAG Feasibility Test for Record {args.record_id} ===")
    
    # 1. Fetch Metadata
    metadata, meta_time = get_record_metadata(args.record_id, headers)
    if not metadata:
        sys.exit(1)
        
    print("\n[Extracted Metadata for Context Window]")
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    
    # 2. Fetch File List
    hocr_files, list_time = get_hocr_files(args.record_id, headers)
    if not hocr_files:
        print("[!] No HOCR files found. Cannot extract full text.")
        sys.exit(1)
        
    # 3. Download and Extract Text
    text, text_time = download_and_extract_text(hocr_files, headers, limit=args.limit)
    
    # 4. Summary Report
    total_time = meta_time + list_time + text_time
    
    print("\n=== RAG Feasibility Summary ===")
    print(f"Total API Latency:  {total_time:.2f} seconds")
    print(f"Metadata Status:    SUCCESS ({len(json.dumps(metadata))} bytes)")
    print(f"Full-Text Status:   SUCCESS ({len(text)} characters extracted from {min(args.limit, len(hocr_files))} pages)")
    
    print("\n[Sample Text for Context Window (first 500 chars)]")
    print(text[:500] + "..." if len(text) > 500 else text)
    
    # Write to file for inspection
    output_file = f"/tmp/rag_test_output_{args.record_id}.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"METADATA:\n{json.dumps(metadata, indent=2, ensure_ascii=False)}\n\n")
        f.write(f"TEXT:\n{text}")
    print(f"\n[+] Full test output written to {output_file}")

if __name__ == "__main__":
    main()
