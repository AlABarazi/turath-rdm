import os
from flask import current_app

# Prints key storage-related environment variables and Flask config keys.
# Run with:
#   pipenv run invenio shell -c 'exec(open("scripts/print_storage_env.py").read())'

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
    "S3_ACCESS_KEY_ID",
    "S3_SECRET_ACCESS_KEY",
    "S3_BUCKET_NAME",
    "S3_REGION",
    "S3_ENDPOINT_URL",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
]

print("# Environment variables:")
for k in ENV_KEYS:
    print(f"{k} = {os.getenv(k)}")

print("\n# Flask config values:")
for k in CFG_KEYS:
    print(f"{k} = {current_app.config.get(k)}")
