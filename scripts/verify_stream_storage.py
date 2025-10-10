#!/usr/bin/env python3
"""
Verify storage-level streaming via ObjectVersion.open() under app context.
Steps:
- Read RDM_API_TOKEN from .env (for REST calls only)
- REST: get files for PID; pick a file (or specific filename) and retrieve bucket_id/key (fallback to record JSON)
- Create API app with invenio_app.factory.create_api()
- Use invenio_files_rest.models.ObjectVersion.get(bucket_id, key) and stream bytes, compute sha256 and size
- Print comparisons with REST metadata (if present)

Usage:
  python scripts/verify_stream_storage.py --pid 7cxkj-kvp29 [--filename DSC_0003.JPG] [--base-url https://127.0.0.1:5000]
"""
from __future__ import annotations
import argparse
import hashlib
import os
import sys
from typing import Optional, Tuple

import requests
from flask import current_app
from invenio_app.factory import create_api
from invenio_db import db
from invenio_files_rest.models import ObjectVersion

requests.packages.urllib3.disable_warnings()  # local https


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


def api_get(url: str, token: Optional[str]):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.get(url, headers=headers, verify=False)
    r.raise_for_status()
    return r


def get_files(base_url: str, pid: str, token: Optional[str]):
    url = f"{base_url}/api/records/{pid}/files"
    data = api_get(url, token).json()
    if isinstance(data, dict) and "entries" in data and isinstance(data["entries"], list):
        return data["entries"]
    if isinstance(data, list):
        return data
    raise RuntimeError("Unexpected files API response shape; expected list or object with 'entries'.")


def get_record(base_url: str, pid: str, token: Optional[str]):
    url = f"{base_url}/api/records/{pid}"
    return api_get(url, token).json()


def pick_entry(entries, prefer_name: Optional[str]):
    if not entries:
        raise RuntimeError("No files found for record")
    if prefer_name:
        for e in entries:
            if e.get("key") == prefer_name:
                return e
        raise RuntimeError(f"Requested filename not found: {prefer_name}")
    return entries[0]


def resolve_bucket_and_key(entry: dict, record_json: Optional[dict]) -> Tuple[str, str]:
    key = entry.get("key")
    bucket_id = entry.get("bucket_id") or entry.get("bucket", {}).get("id")
    if not bucket_id and record_json:
        # Try known locations in record payload
        files = record_json.get("files") or {}
        bucket_id = files.get("bucket_id") or files.get("bucket", {}).get("id")
    if not key or not bucket_id:
        raise RuntimeError("Could not resolve bucket_id and key for file")
    return bucket_id, key


def stream_object(bucket_id: str, key: str) -> Tuple[int, str]:
    h = hashlib.sha256()
    total = 0
    # ObjectVersion.get expects Bucket or UUID. It can accept a string UUID for bucket
    ov = ObjectVersion.get(bucket_id, key)
    # Use storage interface to open a readable stream
    storage = ov.file.storage()
    with storage.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            if not chunk:
                break
            h.update(chunk)
            total += len(chunk)
    return total, h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Verify storage-level streaming via ObjectVersion.open()")
    parser.add_argument("--pid", required=True)
    parser.add_argument("--filename")
    parser.add_argument("--base-url", default="https://127.0.0.1:5000")
    args = parser.parse_args()

    token = load_token_from_env()

    # REST side (to find entry and metadata)
    entries = get_files(args.base_url, args.pid, token)
    print({"files_count": len(entries), "keys": [e.get("key") for e in entries]})
    entry = pick_entry(entries, args.filename)
    record_json = None
    try:
        record_json = get_record(args.base_url, args.pid, token)
    except Exception:
        pass

    bucket_id, key = resolve_bucket_and_key(entry, record_json)
    print({"selected": key, "bucket_id": bucket_id, "rest_size": entry.get("size"), "rest_checksum": entry.get("xchecksums", {}).get("sha256") or entry.get("checksum")})

    # App context: stream via storage
    app = create_api()
    with app.app_context():
        # Ensure DB session is ready
        db.session.commit()
        size, sha = stream_object(bucket_id, key)
        print({"storage_stream_size": size, "storage_stream_sha256": sha})

    # Optional comparison if REST had sha256
    rest_sha = (entry.get("xchecksums", {}) or {}).get("sha256")
    if rest_sha:
        print({"sha256_match": rest_sha.lower() == sha.lower()})


if __name__ == "__main__":
    main()
