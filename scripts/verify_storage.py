import os
import sys
from flask import current_app
from invenio_files_rest.models import Location, ObjectVersion

# Consolidated storage verification
# Run with:
#   pipenv run invenio shell -c 'exec(open("scripts/verify_storage.py").read())'
# Optional (resolve a single object):
#   pipenv run invenio shell -c 'bucket="<uuid>"; key="<name>"; exec(open("scripts/verify_storage.py").read())'

ENV_KEYS = [
    "S3_BUCKET_NAME",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "S3_REGION",
    "S3_ENDPOINT_URL",
    "S3_SIGNATURE_VERSION",
    "S3_SECURE",
]

CFG_KEYS = [
    "FILES_REST_DEFAULT_LOCATION",
    "FILES_REST_LOCATIONS",
]

print("# Environment variables:")
for k in ENV_KEYS:
    print(f"{k} = {os.getenv(k)}")

print("\n# Flask config values:")
for k in CFG_KEYS:
    print(f"{k} = {current_app.config.get(k)}")

print("\n# Files-REST Locations:")
for loc in Location.query.all():
    print(f"Location: {loc.name}  URI: {loc.uri}  default: {loc.default}")

# Optional object resolution
bucket = globals().get("bucket") or os.getenv("BUCKET_ID")
key = globals().get("key") or os.getenv("OBJECT_KEY")
if bucket and key:
    try:
        ov = ObjectVersion.get(bucket, key)
        fi = ov.file
        print("\n# Object resolution:")
        print("bucket_id:", bucket)
        print("key:", key)
        print("uri:", fi.uri)
    except Exception as e:
        print("\n# Object resolution error:", e)
