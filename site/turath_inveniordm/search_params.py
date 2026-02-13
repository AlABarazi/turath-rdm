"""Custom search parameter interpreters for Turath InvenioRDM."""

from invenio_records_resources.services.records.params.base import (
    ParamInterpreter,
)


class ExcludeFulltextSourceParam(ParamInterpreter):
    """
    Exclude the fulltext field from OpenSearch _source responses.

    The turath:fulltext field can be ~1MB per record. Including it
    in every search response wastes bandwidth and slows down queries.
    The field remains fully indexed and searchable — this only
    prevents the raw text from being returned in results.
    """

    def apply(self, identity, search, params):
        """Remove fulltext from _source in search results."""
        return search.source(
            excludes=["custom_fields.turath:fulltext"],
        )
