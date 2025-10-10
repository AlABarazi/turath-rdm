# verify_storage.md

A quick verifier for storage configuration. Use it to confirm MinIO/S3 environment variables, Files-REST Locations, and optionally resolve a file's storage URI.

## Prerequisites
- Run inside the project virtualenv.
- `python-dotenv` installed if you rely on `.env` auto-loading.
- Script must run in the Invenio app context via `invenio shell`.

## Environment variables (MinIO example)
Set these in `.env` or export them in your shell:
```
S3_BUCKET_NAME=turath-files
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
S3_REGION=us-east-1
S3_ENDPOINT_URL=http://127.0.0.1:9000
S3_SIGNATURE_VERSION=s3v4
S3_SECURE=false
```
If auto-loading doesn’t work, force-load:
```
set -a && source .env && set +a
```

## Basic usage
Print env vars and list Files-REST Locations:
```
pipenv run invenio shell -c 'exec(open("scripts/verify_storage.py").read())'
```
Expected output (example):
```
# Environment variables:
S3_BUCKET_NAME = turath-files
...

# Flask config values:
FILES_REST_DEFAULT_LOCATION = None
...

# Files-REST Locations:
Location: default-location  URI: /.../.venv/var/instance/data  default: True
Location: s3  URI: s3://turath-files/  default: True
```
Note: You can have both the legacy filesystem and S3 locations present; the `default: True` one is used for new uploads.

## Resolve a specific object (optional)
If you know `bucket_id` and `key`, resolve its storage URI:
```
pipenv run invenio shell -c 'bucket="<bucket_uuid>"; key="<filename>"; exec(open("scripts/verify_storage.py").read())'
```
Example result on S3/MinIO:
```
# Object resolution:
bucket_id: dab62764-...ea2c
key: history00872.pdf
uri: s3://turath-files/...
```
Example result on filesystem (legacy):
```
# Object resolution:
uri: /path/to/.venv/var/instance/data/<hash>/<hash>/data
```

## Troubleshooting
- "None None" for env vars:
  - Install dotenv: `pipenv install python-dotenv`.
  - Or `set -a && source .env && set +a` before running.
- Missing S3 Location:
  - Create it: `pipenv run invenio shell -c 'exec(open("scripts/create_s3_location.py").read())'`
- New uploads still go to filesystem:
  - Ensure S3 location is `default: True` and restart the app.

## Related helpers
- `scripts/print_storage_env.py` – prints env + config keys
- `scripts/list_locations.py` – lists Files-REST Locations
- `scripts/create_s3_location.py` – creates/updates S3 location
- `scripts/resolve_object_path.py` – resolves URI of specific object
