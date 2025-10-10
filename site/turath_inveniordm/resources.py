"""
Custom IIIF resources for Turath InvenioRDM.

This module provides extended IIIF resources that use custom serializers
with IIIF Search services injection.
"""

from flask import g
from flask_cors import cross_origin
from invenio_rdm_records.resources.iiif import IIIFResource
from invenio_records_resources.resources.base import response_handler
from invenio_records_resources.resources.records.resource import (
    iiif_request_view_args,
    proxy_pass,
    with_iiif_content_negotiation,
)

from .serializers import TurathIIIFManifestV2JSONSerializer


class TurathIIIFResource(IIIFResource):
    """Extended IIIF resource with custom manifest serializer."""

    #
    # IIIF Manifest - override to use custom serializer with search services
    #
    @cross_origin(origin="*", methods=["GET"])
    @with_iiif_content_negotiation(TurathIIIFManifestV2JSONSerializer)
    @iiif_request_view_args
    @response_handler()
    @proxy_pass.__func__
    def manifest(self):
        """Manifest with IIIF Search services."""
        return self._get_record_with_files().to_dict(), 200
