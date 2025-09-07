# MinIO Setup Workflow for InvenioRDM

This folder contains a one-command workflow to verify MinIO connectivity and ensure InvenioRDM writes to the `s3` default location (bucket `turath-files`).

## Prerequisites

- MinIO service defined in `docker-services.yml` (service name: `s3`)
- Credentials (containerized):
  - `MINIO_ROOT_USER=admin@turath.com`
  - `MINIO_ROOT_PASSWORD=12345678`
- `.env` (local run via `invenio-cli run`):
  - `AWS_ACCESS_KEY_ID=admin@turath.com`
  - `AWS_SECRET_ACCESS_KEY=12345678`
  - `AWS_DEFAULT_REGION=us-east-1`
  - `AWS_ENDPOINT_URL=http://127.0.0.1:9000`
  - `AWS_S3_ADDRESSING_STYLE=path`
  - `AWS_S3_SIGNATURE_VERSION=s3v4`
  - `S3_BUCKET_NAME=turath-files`
- Containerized compose (web-ui/web-api/worker): env injected in `docker-services.yml` under `services.app.environment`:
  - `AWS_ENDPOINT_URL=http://s3:9000` (note container DNS)

## Quick start (local)

```bash
set -a && source .env && set +a
python scripts/storage/minio_setup_workflow.py
```

## Quick start (containerized)

```bash
docker compose -f docker-compose.full.yml up -d --build
# then, from host (will execute inside the container)
docker compose exec web-ui invenio shell -c "exec(open('scripts/verify_storage.py').read())"
```

## What the workflow does

1. Prints effective AWS/MinIO env.
2. Checks MinIO health (`/minio/health/live`).
3. Ensures default `Location` is `s3://{S3_BUCKET_NAME}/` via `scripts/create_s3_location.py`.
4. Verifies locations via `scripts/verify_storage.py`.

## Manual commands (fallback)

```bash
# Print env
invenio shell -c "exec(open('scripts/print_storage_env.py').read())"

# Ensure default S3 Location
invenio shell -c "exec(open('scripts/create_s3_location.py').read())"

# Verify storage
invenio shell -c "exec(open('scripts/verify_storage.py').read())"
```

## Notes

- Inside containers, use `http://s3:9000` as endpoint; on the host, use `http://127.0.0.1:9000`.
- Verify bucket exists in MinIO Console: http://127.0.0.1:9001
- Expected output: `Location: s3  URI: s3://turath-files/  default: True`.
