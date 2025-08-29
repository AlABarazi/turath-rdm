"""
IIIF Search Services Monkey Patch for Turath InvenioRDM.

This module patches the IIIF manifest serializer to inject Search services
without forking the core InvenioRDM library.
"""

from flask import current_app
from invenio_rdm_records.resources.serializers.iiif.schema import IIIFManifestV2Schema


def patch_iiif_manifest_schema():
    """Monkey patch the IIIF manifest schema to inject search services."""
    
    # Store the original post_dump method
    original_sortcanvases = IIIFManifestV2Schema.sortcanvases
    
    def enhanced_sortcanvases(self, manifest, many, **kwargs):
        """Enhanced sortcanvases that also injects IIIF Search services."""
        # First apply the original sorting
        manifest = original_sortcanvases(self, manifest, many, **kwargs)
        
        # Check if IIIF Search services are enabled
        if not current_app.config.get('RDM_IIIF_SEARCH_ENABLED', False):
            return manifest
        
        # Extract record PID from manifest @id
        manifest_id = manifest.get('@id', '')
        if '/record:' in manifest_id:
            record_pid = manifest_id.split('/record:')[1].split('/')[0]
        else:
            return manifest
        
        # Extend @context to include IIIF Search API
        current_context = manifest.get("@context", [])
        if isinstance(current_context, str):
            current_context = [current_context]
        
        if "http://iiif.io/api/search/0/context.json" not in current_context:
            extended_context = current_context + ["http://iiif.io/api/search/0/context.json"]
            manifest["@context"] = extended_context
        
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
    
    # Apply the monkey patch
    IIIFManifestV2Schema.sortcanvases = enhanced_sortcanvases


def init_iiif_search_patch(app):
    """Initialize the IIIF Search services patch."""
    with app.app_context():
        patch_iiif_manifest_schema()
        app.logger.info("IIIF Search services patch applied successfully")
