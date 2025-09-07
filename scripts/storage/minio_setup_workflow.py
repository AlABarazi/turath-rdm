#!/usr/bin/env python3
import argparse
import os
import sys
import subprocess
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("Missing dependency: requests. Install with 'pip install requests' or run via your venv.")
    sys.exit(1)


def run(cmd: list[str], check: bool = True) -> int:
    print("$", " ".join(cmd))
    return subprocess.run(cmd, check=check).returncode


def print_env():
    keys = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_DEFAULT_REGION",
        "AWS_ENDPOINT_URL",
        "AWS_S3_ADDRESSING_STYLE",
        "AWS_S3_SIGNATURE_VERSION",
        "S3_BUCKET_NAME",
    ]
    print("# Environment variables:")
    for k in keys:
        print(f"{k} = {os.getenv(k)}")


def check_minio_health(endpoint: str) -> bool:
    # Try common health endpoint; fallback to simple GET
    health_url = urljoin(endpoint if endpoint.endswith('/') else endpoint + '/', 'minio/health/live')
    try:
        r = requests.get(health_url, timeout=3)
        if r.ok:
            print(f"MinIO health OK: {health_url} -> {r.status_code}")
            return True
        print(f"MinIO health check failed: {health_url} -> {r.status_code}")
    except Exception as e:
        print(f"MinIO health check error: {e}")
    # Fallback
    try:
        r = requests.get(endpoint, timeout=3)
        print(f"MinIO reachability: {endpoint} -> {r.status_code}")
        return r.ok
    except Exception as e:
        print(f"MinIO reachability error: {e}")
        return False


def ensure_default_s3_location():
    # Use existing helper to set default s3 location to s3://{S3_BUCKET_NAME}/
    return run([
        "invenio", "shell", "-c",
        "exec(open('scripts/create_s3_location.py').read())",
    ])


def verify_storage():
    return run([
        "invenio", "shell", "-c",
        "exec(open('scripts/verify_storage.py').read())",
    ], check=False)


def main():
    parser = argparse.ArgumentParser(description="MinIO setup workflow for InvenioRDM")
    parser.add_argument("--skip-health", action="store_true", help="Skip MinIO health check")
    parser.add_argument("--non-interactive", action="store_true", help="Do not prompt")
    parser.add_argument("--endpoint", default=os.getenv("AWS_ENDPOINT_URL", "http://127.0.0.1:9000"), help="MinIO endpoint URL")
    args = parser.parse_args()

    print_env()

    if not args.skip_health:
        ok = check_minio_health(args.endpoint)
        if not ok:
            print("WARNING: MinIO health check failed. Ensure the 's3' service is running.")
            if not args.non_interactive:
                resp = input("Continue anyway? [y/N]: ").strip().lower()
                if resp != 'y':
                    return 2

    rc = ensure_default_s3_location()
    if rc != 0:
        print("ERROR: Failed to set default S3 Location.")
        return rc

    print("\nVerifying storage...")
    verify_storage()

    print("\nDone. If running containerized, ensure endpoint is http://s3:9000 inside containers.")
    print("Tip: Open MinIO Console at http://127.0.0.1:9001 and confirm bucket and objects.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
