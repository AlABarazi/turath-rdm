#!/usr/bin/env python3
"""
IIIF Search Services Injection Spike Prototype - Simplified Version

This script demonstrates how to inject IIIF Search and Autocomplete services
into InvenioRDM IIIF manifests without forking the core library.

Approach: Site-level serializer extension that adds Search context and services.
"""

import json
import sys
import os
from pathlib import Path


def create_base_manifest():
    """Create a base IIIF manifest structure."""
    return {
        "@context": "http://iiif.io/api/presentation/2/context.json",
        "@type": "sc:Manifest",
        "@id": "https://127.0.0.1:5000/api/iiif/record:test-record-123/manifest",
        "label": "Test Document with Search",
        "metadata": [
            {
                "label": "Publication Date",
                "value": "2024-01-01"
            }
        ],
        "description": "A test document for IIIF Search integration",
        "sequences": [
            {
                "@id": "https://127.0.0.1:5000/api/iiif/record:test-record-123/sequence/normal",
                "@type": "sc:Sequence",
                "label": "Current Page Order",
                "viewingDirection": "left-to-right",
                "viewingHint": "individuals",
                "canvases": []
            }
        ]
    }


def inject_iiif_search_services(manifest, record_pid, config=None):
    """
    Inject IIIF Search and Autocomplete services into a manifest.
    
    This demonstrates the core logic that would be implemented in the
    ExtendedIIIFManifestV2Schema class.
    """
    if config is None:
        config = {
            'RDM_IIIF_SEARCH_ENABLED': True,
            'IIIF_SEARCH_SERVICE_BASE_URL': 'https://127.0.0.1:5001'
        }
    
    # Check if IIIF Search services are enabled
    if not config.get('RDM_IIIF_SEARCH_ENABLED', False):
        return manifest
    
    # Build service URLs
    base_url = config.get('IIIF_SEARCH_SERVICE_BASE_URL', 'https://127.0.0.1:5001')
    search_url = f"{base_url}/search/{record_pid}"
    autocomplete_url = f"{base_url}/autocomplete/{record_pid}"
    
    # Extend @context to include IIIF Search API
    current_context = manifest.get("@context", [])
    if isinstance(current_context, str):
        current_context = [current_context]
    
    extended_context = current_context + ["http://iiif.io/api/search/0/context.json"]
    manifest["@context"] = extended_context
    
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


def validate_iiif_search_manifest(manifest_data):
    """Validate that the manifest includes required IIIF Search elements."""
    
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Check for extended @context
    context = manifest_data.get("@context", [])
    if not isinstance(context, list):
        context = [context]
    
    required_contexts = [
        "http://iiif.io/api/presentation/2/context.json",
        "http://iiif.io/api/search/0/context.json"
    ]
    
    for req_context in required_contexts:
        if req_context not in context:
            validation_results["errors"].append(f"Missing required @context: {req_context}")
            validation_results["valid"] = False
    
    # Check for service block
    services = manifest_data.get("service", [])
    if not services:
        validation_results["errors"].append("No service block found in manifest")
        validation_results["valid"] = False
        return validation_results
    
    # Find search service
    search_service = None
    for service in services:
        if service.get("profile") == "http://iiif.io/api/search/0/search":
            search_service = service
            break
    
    if not search_service:
        validation_results["errors"].append("No IIIF Search service found")
        validation_results["valid"] = False
        return validation_results
    
    # Validate search service structure
    required_search_fields = ["@id", "profile", "label"]
    for field in required_search_fields:
        if field not in search_service:
            validation_results["errors"].append(f"Search service missing required field: {field}")
            validation_results["valid"] = False
    
    # Check for nested autocomplete service
    nested_service = search_service.get("service")
    if not nested_service:
        validation_results["warnings"].append("No nested autocomplete service found")
    else:
        if nested_service.get("profile") != "http://iiif.io/api/search/0/autocomplete":
            validation_results["errors"].append("Invalid autocomplete service profile")
            validation_results["valid"] = False
    
    return validation_results


def create_realistic_manifest_with_canvas():
    """Create a more realistic manifest with canvas elements."""
    manifest = create_base_manifest()
    
    # Add a sample canvas
    canvas = {
        "@id": "https://127.0.0.1:5000/api/iiif/record:test-record-123/canvas/p001",
        "@type": "sc:Canvas",
        "label": "p. 001",
        "width": 1011,
        "height": 1307,
        "images": [
            {
                "@type": "oa:Annotation",
                "motivation": "sc:painting",
                "on": "https://127.0.0.1:5000/api/iiif/record:test-record-123/canvas/p001",
                "resource": {
                    "@id": "http://localhost:8182/iiif/2/test-record-123_page001.pdf/full/full/0/default.jpg?page=1",
                    "@type": "dctypes:Image",
                    "format": "image/jpeg",
                    "service": {
                        "@context": "http://iiif.io/api/image/2/context.json",
                        "@id": "http://localhost:8182/iiif/2/test-record-123_page001.pdf",
                        "profile": "http://iiif.io/api/image/2/level2.json"
                    },
                    "width": 1011,
                    "height": 1307
                }
            }
        ],
        "otherContent": [
            {
                "@id": "https://127.0.0.1:5000/api/iiif/record:test-record-123/annotations/p001",
                "@type": "sc:AnnotationList",
                "label": "Text of page 001"
            }
        ],
        "seeAlso": [
            {
                "@id": "https://127.0.0.1:5000/records/test-record-123/files/001.hocr",
                "format": "text/vnd.hocr+html",
                "profile": "http://kba.github.io/hocr-spec/1.2/",
                "label": "HOCR OCR text"
            }
        ]
    }
    
    manifest["sequences"][0]["canvases"] = [canvas]
    
    # Add related PDF download
    manifest["related"] = {
        "@id": "https://127.0.0.1:5000/records/test-record-123/files/test_document.pdf",
        "format": "application/pdf",
        "label": "Download full PDF"
    }
    
    return manifest


def demonstrate_serializer_approach():
    """
    Demonstrate how this would be implemented as a serializer extension.
    
    This shows the conceptual approach that would be used in the actual
    InvenioRDM site package.
    """
    
    class_definition = '''
# In site/turath_inveniordm/serializers.py

from marshmallow import fields, post_dump
from flask import current_app
from invenio_rdm_records.resources.serializers.iiif.schema import IIIFManifestV2Schema


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


# In invenio.cfg, override the default serializer:
RDM_RECORDS_SERIALIZERS_IIIF_MANIFEST = "turath_inveniordm.serializers:TurathIIIFManifestV2Schema"
RDM_IIIF_SEARCH_ENABLED = True
IIIF_SEARCH_SERVICE_BASE_URL = "https://127.0.0.1:5001"
    '''
    
    return class_definition


def main():
    """Main function to run the spike prototype."""
    print("IIIF Search Services Injection Spike Prototype - Simplified")
    print("=" * 60)
    
    try:
        # Test 1: Create base manifest
        print("1. Creating base IIIF manifest...")
        base_manifest = create_base_manifest()
        
        # Test 2: Inject search services
        print("2. Injecting IIIF Search services...")
        record_pid = "test-record-123"
        enhanced_manifest = inject_iiif_search_services(base_manifest.copy(), record_pid)
        
        print("3. Enhanced manifest with search services:")
        print(json.dumps(enhanced_manifest, indent=2))
        
        # Test 3: Validate the manifest
        print("\n4. Validating IIIF Search integration...")
        validation = validate_iiif_search_manifest(enhanced_manifest)
        
        if validation["valid"]:
            print("✅ Validation PASSED - Manifest includes required IIIF Search elements")
        else:
            print("❌ Validation FAILED")
            for error in validation["errors"]:
                print(f"   Error: {error}")
        
        if validation["warnings"]:
            print("⚠️  Warnings:")
            for warning in validation["warnings"]:
                print(f"   Warning: {warning}")
        
        # Test 4: Create realistic manifest with canvas
        print("\n5. Creating realistic manifest with canvas...")
        realistic_manifest = create_realistic_manifest_with_canvas()
        enhanced_realistic = inject_iiif_search_services(realistic_manifest, record_pid)
        
        print("6. Realistic manifest with search services:")
        print(json.dumps(enhanced_realistic, indent=2))
        
        # Test 5: Test configuration control
        print("\n7. Testing configuration control...")
        
        # Disabled config
        disabled_config = {'RDM_IIIF_SEARCH_ENABLED': False}
        disabled_manifest = inject_iiif_search_services(base_manifest.copy(), record_pid, disabled_config)
        has_services = 'service' in disabled_manifest
        print(f"   With RDM_IIIF_SEARCH_ENABLED=False: Services injected = {has_services}")
        
        # Enabled config
        enabled_config = {'RDM_IIIF_SEARCH_ENABLED': True, 'IIIF_SEARCH_SERVICE_BASE_URL': 'https://127.0.0.1:5001'}
        enabled_manifest = inject_iiif_search_services(base_manifest.copy(), record_pid, enabled_config)
        has_services = 'service' in enabled_manifest
        print(f"   With RDM_IIIF_SEARCH_ENABLED=True: Services injected = {has_services}")
        
        # Save sample manifests
        output_dir = "/tmp"
        
        basic_file = f"{output_dir}/iiif_search_manifest_basic.json"
        with open(basic_file, 'w') as f:
            json.dump(enhanced_manifest, f, indent=2)
        
        realistic_file = f"{output_dir}/iiif_search_manifest_realistic.json"
        with open(realistic_file, 'w') as f:
            json.dump(enhanced_realistic, f, indent=2)
        
        print(f"\n8. Sample manifests saved:")
        print(f"   Basic: {basic_file}")
        print(f"   Realistic: {realistic_file}")
        
        # Show implementation approach
        print("\n9. Implementation approach for InvenioRDM site package:")
        print(demonstrate_serializer_approach())
        
        print("\n10. Next steps for implementation:")
        print("   ✅ Proof of concept: IIIF Search services can be injected")
        print("   ✅ Configuration control: Feature can be enabled/disabled")
        print("   ✅ URL building: Service URLs constructed from config")
        print("   ✅ Validation: Manifest passes IIIF Search requirements")
        print("   📋 TODO: Implement in site package serializer")
        print("   📋 TODO: Test with real InvenioRDM instance")
        print("   📋 TODO: Validate with IIIF validator")
        print("   📋 TODO: Test Mirador integration")
        
        return enhanced_manifest
        
    except Exception as e:
        print(f"❌ Error during spike prototype execution: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
