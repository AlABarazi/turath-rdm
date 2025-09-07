from invenio_files_rest.models import Location

# List Files-REST Locations
# Run with:
#   pipenv run invenio shell -c 'exec(open("scripts/list_locations.py").read())'

for loc in Location.query.all():
    print(f"Location: {loc.name}  URI: {loc.uri}  default: {loc.default}")
