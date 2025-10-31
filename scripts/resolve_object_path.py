import os
import sys
from invenio_files_rest.models import ObjectVersion

# Resolve file instance URI for given bucket_id and key.
# Usage:
#   pipenv run invenio shell -c 'bucket="<uuid>"; key="<name>"; exec(open("scripts/resolve_object_path.py").read())'

bucket = globals().get("bucket") or os.getenv("BUCKET_ID")
key = globals().get("key") or os.getenv("OBJECT_KEY")
if not bucket or not key:
    print("ERROR: Provide bucket and key via variables: bucket, key (or BUCKET_ID, OBJECT_KEY)")
    sys.exit(1)

ov = ObjectVersion.get(bucket, key)
fi = ov.file
print("bucket_id:", bucket)
print("key:", key)
print("uri:", fi.uri)
