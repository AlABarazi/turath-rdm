"""Custom search parameter interpreters for Turath InvenioRDM."""

from invenio_records_resources.services.records.params.base import (
    ParamInterpreter,
)


class ExcludeFulltextSourceParam(ParamInterpreter):
    """
    Exclude heavy fields from OpenSearch _source responses.

    Two fields cause search response bloat:
    - turath:fulltext: ~1MB per record (full HOCR-extracted text)
    - files.entries: ~100KB per record (metadata for hundreds of HOCR files)

    Both remain fully indexed and searchable. Thumbnails are served via
    links.thumbnails (not files.entries), so excluding entries is safe.
    """

    def apply(self, identity, search, params):
        """Remove fulltext and per-file metadata from _source."""
        return search.source(
            excludes=[
                "custom_fields.turath:fulltext",
                "files.entries",
            ],
        )
