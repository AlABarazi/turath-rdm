"""Custom search parameter interpreters for Turath InvenioRDM."""

from invenio_records_resources.services.records.params.base import (
    ParamInterpreter,
)


class ExcludeFulltextSourceParam(ParamInterpreter):
    """
    Exclude heavy fields from OpenSearch _source responses.

    Two fields cause search response bloat:
    - turath:fulltext: ~1MB per record (full HOCR-extracted text)
    - files: metadata for every attached file (216KB for 899-file book)

    Both remain fully indexed/searchable. Files are accessible via
    the dedicated /api/records/{id}/files endpoint.
    """

    def apply(self, identity, search, params):
        """Remove fulltext and file metadata from _source."""
        return search.source(
            excludes=[
                "custom_fields.turath:fulltext",
                "files",
            ],
        )
