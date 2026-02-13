"""Custom search options for Turath InvenioRDM."""

from invenio_rdm_records.services.config import RDMSearchOptions

from .search_params import ExcludeFulltextSourceParam


class TurathSearchOptions(RDMSearchOptions):
    """
    Turath-specific search options.

    Extends the default RDM search options to exclude the large
    fulltext field from _source responses, dramatically reducing
    response payload size (from ~6MB to ~200KB for 8 records).
    """

    params_interpreters_cls = [
        ExcludeFulltextSourceParam,
    ] + RDMSearchOptions.params_interpreters_cls
