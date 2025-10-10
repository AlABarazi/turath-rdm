import os
from invenio_db import db
from invenio_files_rest.models import Location

# Create/update S3 Location and set as default using env S3_BUCKET_NAME
# Run with:
#   pipenv run invenio shell -c 'exec(open("scripts/create_s3_location.py").read())'

bucket = os.getenv("S3_BUCKET_NAME")
if not bucket:
    raise RuntimeError("S3_BUCKET_NAME is required in environment.")

loc = Location.query.filter_by(name="s3").one_or_none()
if not loc:
    loc = Location(name="s3", uri=f"s3://{bucket}/", default=True)
    db.session.add(loc)
else:
    loc.uri = f"s3://{bucket}/"
    loc.default = True

db.session.commit()
print(f"Location: {loc.name}  URI: {loc.uri}  default: {loc.default}")
