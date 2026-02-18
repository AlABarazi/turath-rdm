import argparse
import os
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import requests

requests.packages.urllib3.disable_warnings()


def load_token(env_file: str = ".env") -> str:
    """Load RDM_API_TOKEN from .env file first, then environment."""
    token = None
    env_path = Path(env_file)
    
    # Try .env file first
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("RDM_API_TOKEN="):
                    token = line.split("=", 1)[1].strip()
                    break
    
    # Fall back to environment variable
    if not token:
        token = os.getenv("RDM_API_TOKEN")
    
    if not token:
        raise RuntimeError("RDM_API_TOKEN not found in .env or environment")
    
    return token


def get_auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def get_json_headers(token: str) -> Dict[str, str]:
    return {
        **get_auth_headers(token),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def iter_records(base_url: str, token: str, page_size: int) -> Iterable[dict]:
    url: Optional[str] = (
        f"{base_url}/api/records?size={page_size}&sort=newest&allversions=true"
    )
    while url:
        response = requests.get(url, headers=get_auth_headers(token), verify=False)
        if not response.ok:
            raise RuntimeError(
                f"Failed to list records: {response.status_code} {response.text}"
            )
        payload = response.json()
        for hit in payload.get("hits", {}).get("hits", []):
            yield hit
        url = payload.get("links", {}).get("next")


def delete_record_via_api(base_url: str, token: str, record_id: str) -> bool:
    """Soft-delete a published record via DELETE /api/records/{id}/delete."""
    get_response = requests.get(
        f"{base_url}/api/records/{record_id}",
        headers=get_auth_headers(token),
        verify=False,
    )
    if get_response.status_code in {404, 410}:
        return True
    if not get_response.ok:
        print(f"  GET failed: {get_response.status_code} {get_response.text[:200]}")
        return False

    etag = get_response.headers.get("ETag", "").strip('"')
    headers = get_json_headers(token)
    if etag:
        headers["If-Match"] = etag

    tombstone_body = {"note": "Bulk cleanup for re-upload"}

    response = requests.delete(
        f"{base_url}/api/records/{record_id}/delete",
        headers=headers,
        json=tombstone_body,
        verify=False,
    )
    if response.status_code in {200, 202, 204}:
        return True
    print(f"  DELETE failed: {response.status_code} {response.text[:200]}")
    return False


def delete_local_record_cache(record_id: str, cantaloupe_root: Path, hocr_root: Path) -> None:
    cantaloupe_dir = cantaloupe_root / record_id
    if cantaloupe_dir.exists():
        shutil.rmtree(cantaloupe_dir)

    hocr_record_dir = hocr_root / record_id
    if hocr_record_dir.exists():
        shutil.rmtree(hocr_record_dir)


def delete_all_subdirectories(root_dir: Path) -> None:
    if not root_dir.exists():
        return
    for child in root_dir.iterdir():
        if child.is_dir():
            shutil.rmtree(child)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="https://127.0.0.1:5000")
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()

    token = load_token()
    repo_root = Path(__file__).resolve().parents[1]
    cantaloupe_root = repo_root / "cantaloupe-files"
    hocr_root = repo_root / "hocr_mount" / "books"

    record_ids: List[str] = [
        r["id"] for r in iter_records(args.base_url, token, args.page_size)
    ]
    print(f"Found {len(record_ids)} records.")

    if not record_ids:
        print("No records to delete.")
        return 0

    print(f"Cantaloupe cleanup root: {cantaloupe_root}")
    print(f"HOCR cleanup root: {hocr_root}")

    if args.dry_run:
        for record_id in record_ids:
            print(f"[dry-run] Would delete record {record_id}")
            print(
                f"[dry-run] Would delete {cantaloupe_root / record_id} (if exists)"
            )
            print(f"[dry-run] Would delete {hocr_root / record_id} (if exists)")
        return 0

    if not args.yes:
        print("Refusing to delete records without --yes.")
        return 2

    deleted_count = 0
    for record_id in record_ids:
        print(f"Deleting record {record_id}...")
        deleted = delete_record_via_api(args.base_url, token, record_id)
        if not deleted:
            print(f"  Failed to delete record {record_id}")
            continue
        deleted_count += 1
        delete_local_record_cache(record_id, cantaloupe_root, hocr_root)
        print("  Deleted + cleaned local cache")

    delete_all_subdirectories(cantaloupe_root)
    delete_all_subdirectories(hocr_root)

    print(f"Deleted {deleted_count}/{len(record_ids)} records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
