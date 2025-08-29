"""
Custom IIIF serializers for Turath InvenioRDM.

This module provides extended IIIF manifest serializers that inject
IIIF Search and Autocomplete services into manifests.
"""

from marshmallow import fields, post_dump
from flask import current_app
from invenio_rdm_records.resources.serializers.iiif.schema import IIIFManifestV2Schema
from invenio_rdm_records.resources.serializers.iiif import IIIFManifestV2JSONSerializer
from invenio_records_resources.resources.records.serializers import MarshmallowSerializer
from invenio_records_resources.resources.records.serializers.json import JSONSerializer
from invenio_records_resources.resources.base.serializers import BaseListSchema


class TurathIIIFManifestV2Schema(IIIFManifestV2Schema):
    """Extended IIIF manifest schema with Search services for Turath."""
    
    def __init__(self, *args, **kwargs):
        """Initialize with extended context."""
        super().__init__(*args, **kwargs)
        # Override the @context to include IIIF Search API context
        self.fields["@context"] = fields.Method("get_extended_context")
    
    def get_extended_context(self, obj):
        """Return extended context including IIIF Search API."""
        return [
            "http://iiif.io/api/presentation/2/context.json",
            "http://iiif.io/api/search/0/context.json"
        ]
    
    @post_dump
    def inject_search_services(self, manifest, many, **kwargs):
        """Inject IIIF Search and Autocomplete services into manifest."""
        # First apply the parent's post_dump (sorts canvases)
        manifest = super().sortcanvases(manifest, many, **kwargs)
        
        # Check if IIIF Search services are enabled
        if not current_app.config.get('RDM_IIIF_SEARCH_ENABLED', False):
            return manifest
        
        # Extract record PID from manifest @id
        manifest_id = manifest.get('@id', '')
        if '/record:' in manifest_id:
            record_pid = manifest_id.split('/record:')[1].split('/')[0]
        else:
            # Fallback: try to extract from URL pattern
            # Example: https://127.0.0.1:5000/api/iiif/record:abc123/manifest
            return manifest
        
        # Build service URLs
        base_url = current_app.config.get('IIIF_SEARCH_SERVICE_BASE_URL', 'https://127.0.0.1:5001')
        search_url = f"{base_url}/search/{record_pid}"
        autocomplete_url = f"{base_url}/autocomplete/{record_pid}"
        
        # Create search service with nested autocomplete
        search_service = {
            "@id": search_url,
            "profile": "http://iiif.io/api/search/0/search",
            "label": "Search within this manifest",
            "service": {
                "@id": autocomplete_url,
                "profile": "http://iiif.io/api/search/0/autocomplete",
                "label": "Autocomplete words in this manifest"
            }
        }
        
        # Inject the service into the manifest
        manifest["service"] = [search_service]
        
        return manifest


class TurathIIIFManifestV2JSONSerializer(MarshmallowSerializer):
    """Marshmallow based IIIF Presi serializer with Search services for Turath."""

    def __init__(self, **options):
        """Constructor."""
        super().__init__(
            format_serializer_cls=JSONSerializer,
            object_schema_cls=TurathIIIFManifestV2Schema,
            list_schema_cls=BaseListSchema,
            **options,
        )
