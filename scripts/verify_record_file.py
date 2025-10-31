#!/usr/bin/env python3
"""
Verify record file retrieval via REST:
- Read RDM_API_TOKEN from .env
- List files for a record PID
- Pick a file (or a specific filename)
- HEAD to get Content-Length
- Download content, compute SHA256 and size
- Compare to REST-reported metadata

Usage:
  python scripts/verify_record_file.py --pid 7cxkj-kvp29 [--filename some.hocr] [--base-url https://127.0.0.1:5000]
"""
from __future__ import annotations
import argparse
import hashlib
import os
import sys
import tempfile
from typing import Optional, Tuple

import requests


def load_token_from_env(env_path: str = ".env") -> Optional[str]:
    if not os.path.exists(env_path):
        return os.getenv("RDM_API_TOKEN")
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("RDM_API_TOKEN="):
                    return line.strip().split("=", 1)[1]
    except Exception:
        pass
    return os.getenv("RDM_API_TOKEN")


def api_get(url: str, token: str) -> requests.Response:
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers, verify=False)  # local dev with self-signed TLS


def api_head(url: str, token: str) -> requests.Response:
    headers = {"Authorization": f"Bearer {token}"}
    return requests.head(url, headers=headers, verify=False)


def get_files(base_url: str, pid: str, token: str):
    url = f"{base_url}/api/records/{pid}/files"
    r = api_get(url, token)
    r.raise_for_status()
    data = r.json()
    # Support both shapes: {"entries": [...]} or a bare list
    if isinstance(data, dict) and "entries" in data and isinstance(data["entries"], list):
        return data["entries"]
    if isinstance(data, list):
        return data
    raise RuntimeError("Unexpected files API response shape; expected list or object with 'entries'.")


def select_file(entries, prefer_name: Optional[str]) -> Tuple[str, Optional[int], Optional[str]]:
    if not entries:
        raise RuntimeError("No files found for record")
    if prefer_name:
        for e in entries:
            if e.get("key") == prefer_name:
                return e.get("key"), e.get("size"), (e.get("xchecksums", {}) or {}).get("sha256") or e.get("checksum")
        raise RuntimeError(f"Requested filename not found: {prefer_name}")
    e0 = entries[0]
    return e0.get("key"), e0.get("size"), (e0.get("xchecksums", {}) or {}).get("sha256") or e0.get("checksum")


def head_content_length(base_url: str, pid: str, key: str, token: str) -> Optional[int]:
    url = f"{base_url}/api/records/{pid}/files/{key}/content"
    r = api_head(url, token)
    if not r.ok:
        return None
    cl = r.headers.get("Content-Length")
    try:
        return int(cl) if cl is not None else None
    except ValueError:
        return None


def download_file(base_url: str, pid: str, key: str, token: str) -> Tuple[str, int, str]:
    url = f"{base_url}/api/records/{pid}/files/{key}/content"
    r = api_get(url, token)
    r.raise_for_status()
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(r.content)
        path = tmp.name
    size = os.path.getsize(path)
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return path, size, h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Verify record file retrieval via REST")
    parser.add_argument("--pid", required=True, help="Record PID")
    parser.add_argument("--filename", help="Specific filename to verify (optional)")
    parser.add_argument("--base-url", default="https://127.0.0.1:5000", help="Base URL for the API")
    args = parser.parse_args()

    token = load_token_from_env()
    if not token:
        print("RDM_API_TOKEN not found in environment or .env", file=sys.stderr)
        sys.exit(1)

    # 1) List files
    entries = get_files(args.base_url, args.pid, token)
    print({"files_count": len(entries), "sample_keys": [e.get("key") for e in entries[:5]]})

    # 2) Select file
    key, size_rest, checksum_rest = select_file(entries, args.filename)
    print({"selected": key, "rest_size": size_rest, "rest_checksum": checksum_rest})

    # 3) HEAD for content-length
    cl = head_content_length(args.base_url, args.pid, key, token)
    print({"content_length": cl})

    # 4) Download and compute size + sha256
    path, size_local, sha_local = download_file(args.base_url, args.pid, key, token)
    print({"download_path": path, "local_size": size_local, "local_sha256": sha_local})

    # 5) Compare
    size_match = (size_rest is None) or (int(size_rest) == int(size_local))
    cl_match = (cl is None) or (int(cl) == int(size_local))
    sha_match = False
    if checksum_rest and len(checksum_rest) >= 64:
        sha_match = (checksum_rest.lower() == sha_local.lower())

    print({
        "size_match": size_match,
        "content_length_match": cl_match,
        "sha256_match": sha_match,
    })

    # Exit code: non-zero if both size and content-length mismatch (strict), or if checksum present but mismatched
    if (size_rest is not None and not size_match) or (cl is not None and not cl_match) or (checksum_rest and len(checksum_rest) >= 64 and not sha_match):
        sys.exit(2)


if __name__ == "__main__":
    main()
