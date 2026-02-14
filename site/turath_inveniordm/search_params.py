"""Custom search parameter interpreters for Turath InvenioRDM."""

from invenio_records_resources.services.records.params.base import (
    ParamInterpreter,
)


class ExcludeFulltextSourceParam(ParamInterpreter):
    """
    Exclude the fulltext field from OpenSearch _source responses.

    The turath:fulltext field stores the entire HOCR-extracted text of
    a book (~1MB per record). Excluding it from _source cuts response
    size from ~1.1MB to ~200KB for 10 records. The field remains fully
    indexed and searchable.

    Note: files.entries is intentionally NOT excluded — the frontend
    needs it to locate and display thumbnails in search results.
    """

    def apply(self, identity, search, params):
        """Remove fulltext from _source in search results."""
        return search.source(
            excludes=[
                "custom_fields.turath:fulltext",
            ],
        )
