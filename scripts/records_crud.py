#!/usr/bin/env python3
"""
Record CRUD + Single-Book Ingestion Test (local-only endpoints)

- Create a draft record
- Upload one book's PDF (+ optional first HOCR)
- Publish record
- Verify file access via REST (HEAD + GET)
- Mirror PDF to Cantaloupe S3 bucket under books/<book_id>/<book_id>.pdf (optional)
- Verify S3 object exists (boto3) and print sample IIIF URL

Usage examples:
  python scripts/records_crud.py ingest-book \
    --books-root "/absolute/path/to/docs/rdm/books" \
    --book-id history00872 \
    --include-hocr \
    --base-url https://127.0.0.1:5000

  python scripts/records_crud.py get --id <record_id>
  python scripts/records_crud.py list-files --id <record_id>
  python scripts/records_crud.py verify-file --id <record_id> --filename <name>

Env:
  RDM_API_TOKEN                API token
  AWS_ENDPOINT_URL             MinIO endpoint (e.g., http://127.0.0.1:9000)
  AWS_ACCESS_KEY_ID
  AWS_SECRET_ACCESS_KEY
  AWS_DEFAULT_REGION           default: us-east-1
  AWS_S3_ADDRESSING_STYLE      default: path
  CANTALOUPE_S3_BUCKET         bucket where mirrored PDFs are stored (optional)
  IIIF_IMAGE_BASE              default: http://127.0.0.1:8182
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

try:
    import boto3
    from botocore.config import Config as BotoConfig
except Exception:
    boto3 = None
    BotoConfig = None

requests.packages.urllib3.disable_warnings()  # self-signed TLS in dev


# ---------- helpers ----------

def load_token(env_path: str = ".env") -> Optional[str]:
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("RDM_API_TOKEN="):
                        return line.strip().split("=", 1)[1]
        except Exception:
            pass
    return os.getenv("RDM_API_TOKEN")


def h_auth(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def api_get(url: str, token: str) -> requests.Response:
    return requests.get(url, headers=h_auth(token), verify=False)


def api_post(url: str, token: str, json_body=None) -> requests.Response:
    headers = {**h_auth(token), "Content-Type": "application/json", "Accept": "application/json"}
    return requests.post(url, headers=headers, json=json_body, verify=False)


def api_post_empty(url: str, token: str) -> requests.Response:
    return requests.post(url, headers=h_auth(token), verify=False)


def api_put_bytes(url: str, token: str, data: bytes, content_type: str = "application/octet-stream") -> requests.Response:
    headers = {**h_auth(token), "Content-Type": content_type}
    return requests.put(url, headers=headers, data=data, verify=False)


# ---------- dummy custom fields for local experimentation ----------


def build_dummy_custom_fields(book_id: str) -> Dict[str, object]:
    """Build a dummy custom_fields payload for turath:* fields.

    This is intended for local testing of the upload pipeline with the
    Turath custom fields. It uses simple, obviously fake values and
    only relies on vocabulary IDs that are expected to exist in a
    standard InvenioRDM setup (e.g., languages, licenses, resource
    types). For project-specific vocabularies like creators or places,
    we keep the payload minimal to avoid hard dependency on local
    fixture content.
    """

    return {
        # 1. Title
        "turath:title": f"Dummy title for {book_id}",
        # 2. Alternative titles (multi-value)
        "turath:alternative_title": [
            f"Alternative transliterated title for {book_id}",
            "عنوان بديل تجريبي ١",
        ],
        # 3. Publisher (multi-value keyword)
        "turath:publisher": [
            "Dummy Publisher A",
            "Dummy Publisher B",
        ],
        # 6-7. Date and Date-Issued
        "turath:date": "2024-01-15",
        "turath:date_issued": "2024-02-01",
        # 9. Description (multi-value)
        "turath:description": [
            "Short English description for testing custom fields.",
            "وصف عربي تجريبي لحقل الوصف.",
        ],
        # 10. Type (resource_type) – align with core metadata where possible
        "turath:resource_type": {
            "id": "publication-book",
        },
        # 11. Format (multi-value vocab) – keep generic example IDs, safe to adjust
        # in real data by looking up /api/vocabularies/formats.
        # Here we only show structure; IDs may need to be updated in practice.
        # "turath:format": [
        #     {"id": "text"},
        #     {"id": "application-pdf"},
        # ],
        # 11. Extent
        "turath:format_extent": "300 pages; 25 cm",
        # 12. Identifier (multi-value)
        "turath:identifier": [
            f"{book_id}.pdf",
            f"https://example.org/books/{book_id}",
        ],
        # 13. Source (multi-value)
        "turath:source": [
            "Example Collection, Box 1, Folder 2",
            "Donated by Example Family, 2020",
        ],
        # 14. Language (multi-value vocab) – use standard ISO 639-2 codes
        "turath:language": [
            {"id": "ara"},
            {"id": "eng"},
        ],
        # 15. Coverage-Temporal
        "turath:coverage_temporal_start": "1900-01-01",
        "turath:coverage_temporal_end": "1950-12-31",
        # 17. Relation
        "turath:relation_identifier": f"REL-{book_id}",
        "turath:bibliographic_citation": [
            "Dummy Author. Dummy Title. Dummy Place: Dummy Publisher, 2024.",
            "مؤلف تجريبي. عنوان تجريبي. مكان تجريبي: ناشر تجريبي، ٢٠٢٤.",
        ],
        # 18. Rights – use an existing license ID from vocabularies/licenses
        "turath:rights": {
            "id": "cc-by-4.0",
        },
        "turath:rights_uri": "https://creativecommons.org/licenses/by/4.0/",
        "turath:rights_identifier": "CC-BY-4.0",
    }


def load_custom_fields_from_metadata(book_dir: Path) -> Optional[Dict[str, object]]:
    """
    Load custom_fields from metadata.json in book directory.
    
    Returns None if metadata.json doesn't exist or can't be loaded.
    """
    import json
    
    metadata_file = book_dir / "metadata.json"
    if not metadata_file.exists():
        return None
    
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        custom_fields = data.get("custom_fields", {})
        if not custom_fields:
            print(f"⚠️  Warning: metadata.json exists but has no custom_fields", file=sys.stderr)
            return None
        
        print(f"✓ Loaded {len(custom_fields)} custom fields from metadata.json")
        return custom_fields
    
    except Exception as e:
        print(f"⚠️  Warning: Failed to load metadata.json: {e}", file=sys.stderr)
        return None


# ---------- CRUD minimal ----------

def create_draft(
    base_url: str,
    token: str,
    title: str,
    resource_type_id: str = "publication-book",
    custom_fields: Optional[Dict[str, object]] = None,
) -> dict:
    url = f"{base_url}/api/records"
    payload = {
        "metadata": {
            "title": title,
            "resource_type": {"id": resource_type_id},
            "creators": [
                {
                    "person_or_org": {
                        "type": "personal",
                        "family_name": "Uploader",
                        "given_name": "Turath",
                    }
                }
            ],
            "publication_date": "2025-01-01",
        },
        "access": {"record": "public", "files": "public"},
        "files": {"enabled": True},
    }
    if custom_fields:
        payload["custom_fields"] = custom_fields
    r = api_post(url, token, payload)
    if not r.ok:
        raise RuntimeError(f"Create draft failed: {r.status_code} {r.text}")
    return r.json()


def get_record(base_url: str, token: str, record_id: str) -> dict:
    r = api_get(f"{base_url}/api/records/{record_id}", token)
    r.raise_for_status()
    return r.json()


def init_files(base_url: str, token: str, record_id: str, keys: List[str]) -> dict:
    url = f"{base_url}/api/records/{record_id}/draft/files"
    body = [{"key": k} for k in keys]
    r = api_post(url, token, body)
    if not r.ok:
        raise RuntimeError(f"Init files failed: {r.status_code} {r.text}")
    return r.json()


def upload_and_commit(base_url: str, token: str, record_id: str, key: str, file_path: Path) -> None:
    content_url = f"{base_url}/api/records/{record_id}/draft/files/{key}/content"
    commit_url = f"{base_url}/api/records/{record_id}/draft/files/{key}/commit"
    with open(file_path, "rb") as f:
        data = f.read()
    r_put = api_put_bytes(content_url, token, data)
    if not r_put.ok:
        raise RuntimeError(f"Upload failed for {key}: {r_put.status_code} {r_put.text}")
    r_commit = api_post_empty(commit_url, token)
    if not r_commit.ok:
        raise RuntimeError(f"Commit failed for {key}: {r_commit.status_code} {r_commit.text}")


def publish(base_url: str, token: str, record_id: str) -> dict:
    r = api_post_empty(f"{base_url}/api/records/{record_id}/draft/actions/publish", token)
    if not r.ok:
        raise RuntimeError(f"Publish failed: {r.status_code} {r.text}")
    return r.json()


def list_files(base_url: str, token: str, record_id: str) -> List[dict]:
    r = api_get(f"{base_url}/api/records/{record_id}/files", token)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and "entries" in data:
        return data["entries"]
    if isinstance(data, list):
        return data
    raise RuntimeError("Unexpected files response shape")


def head_content_length(base_url: str, token: str, record_id: str, key: str) -> Optional[int]:
    r = requests.head(f"{base_url}/api/records/{record_id}/files/{key}/content", headers=h_auth(token), verify=False)
    if not r.ok:
        return None
    v = r.headers.get("Content-Length")
    try:
        return int(v) if v else None
    except ValueError:
        return None


def download_and_sha256(base_url: str, token: str, record_id: str, key: str) -> Tuple[str, int, str]:
    r = api_get(f"{base_url}/api/records/{record_id}/files/{key}/content", token)
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


def delete_record(base_url: str, token: str, record_id: str) -> bool:
    # Deleting published records may be disabled by policy; this may fail.
    r = requests.delete(f"{base_url}/api/records/{record_id}", headers=h_auth(token), verify=False)
    return r.ok


def cmd_mirror_existing(args):
    """Mirror an existing local PDF to the Cantaloupe S3 bucket.

    This avoids creating a new record. It expects the local books folder to contain
    `<book_id>/<book_id>.pdf` (or any .pdf in the folder). The S3 bucket is taken
    from CANTALOUPE_S3_BUCKET, and the key pattern is `books/{book_id}/{book_id}.pdf`.
    """
    books_root = Path(args.books_root).expanduser().resolve()
    book_dir = books_root / args.book_id
    if not book_dir.exists():
        raise FileNotFoundError(f"Book directory not found: {book_dir}")

    pdf = book_dir / f"{args.book_id}.pdf"
    if not pdf.exists():
        cands = sorted(book_dir.glob("*.pdf"))
        if not cands:
            raise FileNotFoundError(f"No PDF found in {book_dir}")
        pdf = cands[0]

    mirrored = mirror_pdf_to_cantaloupe(pdf, args.book_id)
    if not mirrored:
        print({"mirrored": False, "reason": "CANTALOUPE_S3_BUCKET not set or boto3 missing"})
        return
    bucket, key = mirrored
    iiif_base = os.getenv("IIIF_IMAGE_BASE", "http://127.0.0.1:8182")
    iiif_full = f"{iiif_base}/iiif/2/{key}/full/full/0/default.jpg?page=1"
    print({"mirrored": f"s3://{bucket}/{key}", "sample_iiif_page1": iiif_full})


# ---------- S3 mirror for Cantaloupe ----------

def s3_client_from_env():
    if boto3 is None:
        return None
    endpoint = os.getenv("AWS_ENDPOINT_URL", "http://127.0.0.1:9000")
    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    ak = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
    sk = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
    addr_style = os.getenv("AWS_S3_ADDRESSING_STYLE", "path")
    cfg = BotoConfig(s3={"addressing_style": addr_style}) if BotoConfig else None
    return boto3.session.Session().client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=ak,
        aws_secret_access_key=sk,
        region_name=region,
        config=cfg,
    )


def ensure_fulltext_indexing(record_id: str):
    """
    Explicitly trigger HOCR sync and fulltext indexing for a record.
    This runs via Invenio application context (server-side logic),
    ensuring robust indexing even if HTTP signals were missed.
    """
    print(f"\n[Indexer] Ensuring fulltext indexing for {record_id}...")
    try:
        from invenio_app.factory import create_app
        from invenio_pidstore.models import PersistentIdentifier
        from invenio_rdm_records.records.api import RDMRecord
        from invenio_rdm_records.proxies import current_rdm_records_service
        from turath_inveniordm.signals import sync_files_to_filesystem
        from turath_inveniordm.fulltext import extract_hocr_text
        
        app = create_app()
        with app.app_context():
            # Resolve PID
            pid = PersistentIdentifier.get('recid', record_id)
            record = RDMRecord.get_record(pid.object_uuid)
            
            # 1. Sync Files
            print(f"[Indexer] Syncing files to disk...")
            pdf_count, hocr_count = sync_files_to_filesystem(record)
            print(f"[Indexer] Synced {pdf_count} PDFs and {hocr_count} HOCRs.")
            
            # 2. Extract Text
            print(f"[Indexer] Extracting text...")
            text = extract_hocr_text(record_id)
            if text:
                print(f"[Indexer] Extracted {len(text)} characters.")
                # 3. Update Record
                record.setdefault('custom_fields', {})['turath:fulltext'] = text
                record.commit()
                # 4. Index
                print(f"[Indexer] Re-indexing record...")
                current_rdm_records_service.indexer.index(record)
                print(f"[Indexer] ✅ Success.")
            else:
                print(f"[Indexer] ⚠️ No text extracted (no HOCR?).")
                
    except ImportError:
        print("[Indexer] ⚠️ Invenio packages not found. Skipping server-side indexing. Ensure you run with 'pipenv run'.")
    except Exception as e:
        print(f"[Indexer] ❌ Failed: {e}")
        import traceback
        traceback.print_exc()


def mirror_pdf_to_cantaloupe(pdf_path: Path, book_id: str) -> Optional[Tuple[str, str]]:
    bucket = os.getenv("CANTALOUPE_S3_BUCKET")
    if not bucket:
        print("[mirror] CANTALOUPE_S3_BUCKET not set; skipping mirror")
        return None
    s3 = s3_client_from_env()
    if s3 is None:
        print("[mirror] boto3 not available; skipping mirror")
        return None
    key = f"books/{book_id}/{book_id}.pdf"
    with open(pdf_path, "rb") as f:
        s3.put_object(Bucket=bucket, Key=key, Body=f)
    # Verify existence
    s3.head_object(Bucket=bucket, Key=key)
    return bucket, key


def mirror_pdf_to_local_disk(pdf_path: Path, record_id: str, pdf_key: str) -> None:
    """Mirror PDF to local shared volume for FilesystemSource."""
    # Base dir is ./cantaloupe-files (mounted to /opt/cantaloupe/images in docker)
    base_dir = Path("cantaloupe-files")
    base_dir.mkdir(exist_ok=True)
    
    target_dir = base_dir / record_id
    target_dir.mkdir(parents=True, exist_ok=True)
    
    target_file = target_dir / pdf_key
    print(f"[mirror] Copying PDF to local disk: {target_file}...")
    shutil.copy(pdf_path, target_file)


# ---------- commands ----------

def cmd_ingest_book(args):
    token = load_token()
    if not token:
        print("RDM_API_TOKEN not found in environment or .env", file=sys.stderr)
        sys.exit(1)

    books_root = Path(args.books_root).expanduser().resolve()
    book_dir = books_root / args.book_id
    if not book_dir.exists():
        raise FileNotFoundError(f"Book directory not found: {book_dir}")

    # PDF
    pdf = book_dir / f"{args.book_id}.pdf"
    if not pdf.exists():
        cands = sorted(book_dir.glob("*.pdf"))
        if not cands:
            raise FileNotFoundError(f"No PDF found in {book_dir}")
        pdf = cands[0]

    # HOCR (optional): gather ALL *.hocr files from root and optional 'hocr/' subfolder
    hocr_files = []
    if args.include_hocr:
        # Collect from root
        hocr_files.extend(sorted(book_dir.glob("*.hocr")))
        # Collect from 'hocr' subdirectory if present
        hocr_dir = book_dir / "hocr"
        if hocr_dir.exists():
            hocr_files.extend(sorted(hocr_dir.glob("*.hocr")))

    # Try to load custom fields from metadata.json, fallback to dummy
    print(f"\n{'='*60}")
    print(f"Loading metadata for: {args.book_id}")
    print(f"{'='*60}")
    
    custom_fields = load_custom_fields_from_metadata(book_dir)
    
    if custom_fields:
        print(f"✓ Using custom fields from metadata.json")
        # Extract title from custom fields if available
        title = custom_fields.get("turath:title", args.book_id)
    else:
        print(f"⚠️  No metadata.json found, using dummy custom fields")
        custom_fields = build_dummy_custom_fields(args.book_id)
        title = args.book_id
    
    print(f"\nCreating draft record...")
    draft = create_draft(
        args.base_url,
        token,
        title=title,
        resource_type_id=getattr(args, "resource_type", "publication-book"),
        custom_fields=custom_fields,
    )
    record_id = draft.get("id")
    print({"record_id": record_id})

    # Init files (PDF + all HOCRs if requested)
    keys = [pdf.name] + [p.name for p in hocr_files]
    init_files(args.base_url, token, record_id, keys)

    # Upload + commit
    upload_and_commit(args.base_url, token, record_id, pdf.name, pdf)
    for hocr_path in hocr_files:
        upload_and_commit(args.base_url, token, record_id, hocr_path.name, hocr_path)

    # Publish
    published = publish(args.base_url, token, record_id)
    print({"published": True, "links": published.get("links", {})})

    # Verify via REST
    entries = list_files(args.base_url, token, record_id)
    print({"files": [e.get("key") for e in entries]})

    cl = head_content_length(args.base_url, token, record_id, pdf.name)
    path, size, sha = download_and_sha256(args.base_url, token, record_id, pdf.name)
    print({"pdf_content_length": cl, "download_path": path, "size": size, "sha256": sha})

    # Mirror to Cantaloupe bucket
    mirrored = mirror_pdf_to_cantaloupe(pdf, args.book_id)
    if mirrored:
        bucket, key = mirrored
        iiif_base = os.getenv("IIIF_IMAGE_BASE", "http://127.0.0.1:8182")
        iiif_full = f"{iiif_base}/iiif/2/{key}/full/full/0/default.jpg?page=1"
        print({"mirrored": f"s3://{bucket}/{key}", "sample_iiif_page1": iiif_full})

    # Mirror to local disk (FilesystemSource)
    mirror_pdf_to_local_disk(pdf, record_id, pdf.name)

    ui_url = f"{args.base_url.replace('/api', '')}/records/{record_id}"
    print({"record_ui": ui_url})
    
    # Ensure fulltext indexing (server-side logic)
    ensure_fulltext_indexing(record_id)
    
    # Return record_id for use by calling scripts
    return record_id


def cmd_get(args):
    token = load_token()
    if not token:
        print("RDM_API_TOKEN not found", file=sys.stderr)
        sys.exit(1)
    doc = get_record(args.base_url, token, args.id)
    print(doc)


def cmd_list_files(args):
    token = load_token()
    if not token:
        print("RDM_API_TOKEN not found", file=sys.stderr)
        sys.exit(1)
    entries = list_files(args.base_url, token, args.id)
    print({"files": [e.get("key") for e in entries]})


def cmd_verify_file(args):
    token = load_token()
    if not token:
        print("RDM_API_TOKEN not found", file=sys.stderr)
        sys.exit(1)
    cl = head_content_length(args.base_url, token, args.id, args.filename)
    path, size, sha = download_and_sha256(args.base_url, token, args.id, args.filename)
    print({"content_length": cl, "download_path": path, "size": size, "sha256": sha})


def cmd_delete(args):
    token = load_token()
    if not token:
        print("RDM_API_TOKEN not found", file=sys.stderr)
        sys.exit(1)
    ok = delete_record(args.base_url, token, args.id)
    print({"deleted_request_ok": ok})


def main():
    p = argparse.ArgumentParser(description="Record CRUD + Single-Book Ingestion Test")
    p.add_argument("command", choices=[
        "ingest-book", "get", "list-files", "verify-file", "delete", "mirror-existing",
    ])
    p.add_argument("--base-url", default="https://127.0.0.1:5000")
    p.add_argument("--books-root")
    p.add_argument("--book-id")
    p.add_argument("--include-hocr", action="store_true")
    p.add_argument("--id")
    p.add_argument("--filename")
    p.add_argument("--resource-type", default="publication-book", help="Resource type ID (e.g., publication-book)")

    args = p.parse_args()

    if args.command == "ingest-book":
        if not args.books_root or not args.book_id:
            print("--books-root and --book-id are required for ingest-book", file=sys.stderr)
            sys.exit(2)
        return cmd_ingest_book(args)
    elif args.command == "get":
        if not args.id:
            print("--id required", file=sys.stderr)
            sys.exit(2)
        return cmd_get(args)
    elif args.command == "list-files":
        if not args.id:
            print("--id required", file=sys.stderr)
            sys.exit(2)
        return cmd_list_files(args)
    elif args.command == "verify-file":
        if not args.id or not args.filename:
            print("--id and --filename required", file=sys.stderr)
            sys.exit(2)
        return cmd_verify_file(args)
    elif args.command == "delete":
        if not args.id:
            print("--id required", file=sys.stderr)
            sys.exit(2)
        return cmd_delete(args)
    elif args.command == "mirror-existing":
        if not args.books_root or not args.book_id:
            print("--books-root and --book-id are required for mirror-existing", file=sys.stderr)
            sys.exit(2)
        return cmd_mirror_existing(args)


if __name__ == "__main__":
    main()
