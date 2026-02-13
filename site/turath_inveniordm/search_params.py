"""Custom search parameter interpreters for Turath InvenioRDM."""

from invenio_records_resources.services.records.params.base import (
    ParamInterpreter,
)


class ExcludeFulltextSourceParam(ParamInterpreter):
    """
    Exclude heavy fields from OpenSearch _source responses.

    Two fields cause search response bloat:
    - turath:fulltext: ~1MB per record (full HOCR-extracted text)
    - files.entries: metadata for every attached file (216KB for 899-file book)

    We exclude files.entries (not files itself) because InvenioRDM's
    pre_load checks `if "entries" in files:` — setting files to None
    causes a TypeError. Keeping the parent object avoids the crash.
    Individual file details are accessible via /api/records/{id}/files.
    """

    def apply(self, identity, search, params):
        """Remove fulltext and per-file metadata from _source."""
        return search.source(
            excludes=[
                "custom_fields.turath:fulltext",
                "files.entries",
            ],
        )
