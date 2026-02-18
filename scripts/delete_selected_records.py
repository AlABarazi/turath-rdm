"""
Delete specific records by PID from InvenioRDM (AWS or local).

Usage:
    # Dry run (see what would happen):
    python3 scripts/delete_selected_records.py --dry-run

    # Test on one record:
    python3 scripts/delete_selected_records.py --test-one

    # Delete all listed records:
    python3 scripts/delete_selected_records.py --yes
"""
import os
import sys
from typing import Dict, List, Tuple

import requests

requests.packages.urllib3.disable_warnings()

BASE_URL = "https://invenio.turath-project.com"

RECORDS_TO_DELETE: List[Tuple[str, str]] = [
    ("rb5ck-vb255", "027_درر_نحور_الحور_العين"),
    ("gp5xg-bn066", "024_غاية_الأماني"),
]


def load_token() -> str:
    """Load token from environment variable."""
    token = os.getenv("RDM_API_TOKEN")
    if not token:
        raise RuntimeError(
            "RDM_API_TOKEN not set. "
            "Run: source .env.aws && export RDM_API_TOKEN"
        )
    return token


def get_auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def get_json_headers(token: str) -> Dict[str, str]:
    return {
        **get_auth_headers(token),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def delete_record_via_tombstone(
    base_url: str, token: str, record_id: str
) -> bool:
    """Soft-delete a published record via DELETE /api/records/{id}/delete."""
    get_response = requests.get(
        f"{base_url}/api/records/{record_id}",
        headers=get_auth_headers(token),
        verify=False,
    )
    if get_response.status_code in {404, 410}:
        print(f"  Already gone ({get_response.status_code})")
        return True
    if not get_response.ok:
        print(
            f"  GET failed: {get_response.status_code} "
            f"{get_response.text[:200]}"
        )
        return False

    etag = get_response.headers.get("ETag", "").strip('"')
    headers = get_json_headers(token)
    if etag:
        headers["If-Match"] = etag

    tombstone_body = {"note": "Re-upload with corrected data"}

    response = requests.delete(
        f"{base_url}/api/records/{record_id}/delete",
        headers=headers,
        json=tombstone_body,
        verify=False,
    )
    if response.status_code in {200, 202, 204}:
        return True
    print(
        f"  DELETE failed: {response.status_code} "
        f"{response.text[:300]}"
    )
    return False


def run_dry_run() -> None:
    print(f"Target: {BASE_URL}")
    print(f"Records to delete: {len(RECORDS_TO_DELETE)}\n")
    for pid, name in RECORDS_TO_DELETE:
        print(f"  [dry-run] Would delete {pid}  ({name})")


def run_test_one() -> None:
    """Delete only the first record to verify the API works."""
    token = load_token()
    pid, name = RECORDS_TO_DELETE[0]
    print(f"Target: {BASE_URL}")
    print(f"TEST: Deleting 1 record: {pid} ({name})\n")

    ok = delete_record_via_tombstone(BASE_URL, token, pid)
    status = "✅ SUCCESS" if ok else "❌ FAILED"
    print(f"\n{status}: {pid} ({name})")

    if ok:
        print("\nVerification — fetching deleted record:")
        r = requests.get(
            f"{BASE_URL}/api/records/{pid}",
            headers=get_auth_headers(token),
            verify=False,
        )
        print(f"  Status: {r.status_code} (expect 410 Gone)")


def run_delete_all() -> None:
    """Delete all listed records."""
    token = load_token()
    print(f"Target: {BASE_URL}")
    print(f"Deleting {len(RECORDS_TO_DELETE)} records...\n")

    success_count = 0
    fail_count = 0

    for i, (pid, name) in enumerate(RECORDS_TO_DELETE, 1):
        print(f"[{i}/{len(RECORDS_TO_DELETE)}] {pid}  ({name})")
        ok = delete_record_via_tombstone(BASE_URL, token, pid)
        if ok:
            success_count += 1
            print("  ✅ Deleted")
        else:
            fail_count += 1
            print("  ❌ Failed")

    print(f"\nDone: {success_count} deleted, {fail_count} failed "
          f"out of {len(RECORDS_TO_DELETE)}")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    flag = sys.argv[1]
    if flag == "--dry-run":
        run_dry_run()
    elif flag == "--test-one":
        run_test_one()
    elif flag == "--yes":
        run_delete_all()
    else:
        print(f"Unknown flag: {flag}")
        print("Use --dry-run, --test-one, or --yes")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
