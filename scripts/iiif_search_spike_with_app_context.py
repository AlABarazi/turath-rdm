#!/usr/bin/env python3
"""
IIIF Search Services Injection Spike Prototype with Flask App Context

This script demonstrates how to inject IIIF Search and Autocomplete services
into InvenioRDM IIIF manifests without forking the core library.

Approach: Site-level serializer extension that adds Search context and services.
"""

import json
import sys
import os
from pathlib import Path

# Add the site package to Python path
site_path = Path(__file__).parent.parent / "site"
sys.path.insert(0, str(site_path))

from flask import Flask
from flask_babel import lazy_gettext as _
from marshmallow import Schema, fields, post_dump
from invenio_rdm_records.resources.serializers.iiif.schema import IIIFManifestV2Schema


class LazyStringEncoder(json.JSONEncoder):
    """JSON encoder that handles Flask-Babel LazyString objects."""
    
    def default(self, obj):
        if hasattr(obj, '__str__'):
            return str(obj)
        return super().default(obj)


class ExtendedIIIFManifestV2Schema(IIIFManifestV2Schema):
    """Extended IIIF manifest schema with Search services injection."""
    
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
    
    def get_search_service_url(self, obj, record_pid):
        """Build search service URL from configuration."""
        from flask import current_app
        base_url = current_app.config.get('IIIF_SEARCH_SERVICE_BASE_URL', 'https://127.0.0.1:5001')
        return f"{base_url}/search/{record_pid}"
    
    def get_autocomplete_service_url(self, obj, record_pid):
        """Build autocomplete service URL from configuration."""
        from flask import current_app
        base_url = current_app.config.get('IIIF_SEARCH_SERVICE_BASE_URL', 'https://127.0.0.1:5001')
        return f"{base_url}/autocomplete/{record_pid}"
    
    @post_dump
    def inject_search_services(self, manifest, many, **kwargs):
        """Inject IIIF Search and Autocomplete services into manifest."""
        from flask import current_app
        
        # First apply the parent's post_dump (sorts canvases)
        manifest = super().sortcanvases(manifest, many, **kwargs)
        
        # Check if IIIF Search services are enabled
        if not current_app.config.get('RDM_IIIF_SEARCH_ENABLED', False):
            return manifest
        
        # Extract record PID from manifest @id
        # Format: https://127.0.0.1:5000/api/iiif/record:PID/manifest
        manifest_id = manifest.get('@id', '')
        if '/record:' in manifest_id:
            record_pid = manifest_id.split('/record:')[1].split('/')[0]
        else:
            # Fallback: try to extract from other sources or skip injection
            return manifest
        
        # Build service URLs
        search_url = self.get_search_service_url(None, record_pid)
        autocomplete_url = self.get_autocomplete_service_url(None, record_pid)
        
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


def create_minimal_flask_app():
    """Create a minimal Flask app with required InvenioRDM config."""
    app = Flask(__name__)
    
    # Add minimal configuration required for IIIF serialization
    app.config.update({
        'RDM_IIIF_SEARCH_ENABLED': True,
        'IIIF_SEARCH_SERVICE_BASE_URL': 'https://127.0.0.1:5001',
        'IIIF_TILES_CONVERTER_PARAMS': {
            'tile_height': 256,
            'tile_width': 256
        },
        'RDM_IIIF_MANIFEST_FORMATS': ['pdf', 'jpg', 'jpeg', 'png', 'tiff']
    })
    
    return app


def create_sample_manifest_with_search():
    """Create a sample manifest with search services for testing."""
    
    # Sample record data (simplified)
    sample_record = {
        "id": "test-record-123",
        "metadata": {
            "title": "Test Document with Search",
            "publication_date": "2024-01-01",
            "description": "A test document for IIIF Search integration"
        },
        "links": {
            "self_iiif_manifest": "https://127.0.0.1:5000/api/iiif/record:test-record-123/manifest",
            "self_iiif_sequence": "https://127.0.0.1:5000/api/iiif/record:test-record-123/sequence/normal"
        },
        "files": {
            "entries": {}
        }
    }
    
    # Serialize using extended schema
    schema = ExtendedIIIFManifestV2Schema()
    result = schema.dump(sample_record)
    
    return result


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


def test_real_manifest_injection():
    """Test injecting search services into a real InvenioRDM manifest structure."""
    
    # Simulate a more realistic record structure
    realistic_record = {
        "id": "d8c9x-57p51",
        "metadata": {
            "title": "History Book Sample",
            "publication_date": "2024-01-15",
            "description": "Sample history book for IIIF Search testing",
            "rights": [{"link": "https://creativecommons.org/licenses/by/4.0/"}]
        },
        "links": {
            "self_iiif_manifest": "https://127.0.0.1:5000/api/iiif/record:d8c9x-57p51/manifest",
            "self_iiif_sequence": "https://127.0.0.1:5000/api/iiif/record:d8c9x-57p51/sequence/normal"
        },
        "files": {
            "entries": {
                "page001.jpg": {
                    "ext": "jpg",
                    "metadata": {"width": 1200, "height": 1600},
                    "key": "page001.jpg",
                    "links": {
                        "iiif_base": "http://localhost:8182/iiif/2/d8c9x-57p51_page001.jpg",
                        "iiif_api": "http://localhost:8182/iiif/2/d8c9x-57p51_page001.jpg/full/full/0/default.jpg",
                        "iiif_canvas": "https://127.0.0.1:5000/api/iiif/record:d8c9x-57p51/canvas/page001",
                        "iiif_annotation": "https://127.0.0.1:5000/api/iiif/record:d8c9x-57p51/annotation/page001"
                    },
                    "mimetype": "image/jpeg"
                }
            }
        }
    }
    
    schema = ExtendedIIIFManifestV2Schema()
    result = schema.dump(realistic_record)
    
    return result


def main():
    """Main function to run the spike prototype."""
    print("IIIF Search Services Injection Spike Prototype")
    print("=" * 50)
    
    # Create Flask app and application context
    app = create_minimal_flask_app()
    
    with app.app_context():
        try:
            # Test 1: Generate sample manifest with search services
            print("1. Generating sample manifest with IIIF Search services...")
            manifest = create_sample_manifest_with_search()
            
            print("2. Generated manifest structure:")
            print(json.dumps(manifest, indent=2, cls=LazyStringEncoder))
            
            # Test 2: Validate the manifest
            print("\n3. Validating IIIF Search integration...")
            validation = validate_iiif_search_manifest(manifest)
            
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
            
            # Test 3: Test with realistic record structure
            print("\n4. Testing with realistic record structure...")
            realistic_manifest = test_real_manifest_injection()
            
            print("5. Realistic manifest with search services:")
            print(json.dumps(realistic_manifest, indent=2, cls=LazyStringEncoder))
            
            # Save sample manifests for external validation
            output_dir = "/tmp"
            
            sample_file = f"{output_dir}/iiif_search_manifest_sample.json"
            with open(sample_file, 'w') as f:
                json.dump(manifest, f, indent=2, cls=LazyStringEncoder)
            
            realistic_file = f"{output_dir}/iiif_search_manifest_realistic.json"
            with open(realistic_file, 'w') as f:
                json.dump(realistic_manifest, f, indent=2, cls=LazyStringEncoder)
            
            print(f"\n6. Sample manifests saved:")
            print(f"   Basic: {sample_file}")
            print(f"   Realistic: {realistic_file}")
            print("\n   Validation options:")
            print("   - IIIF Presentation Validator: https://iiif.io/api/presentation/validator/")
            print("   - Test with Mirador viewer for search UI integration")
            print("   - Validate IIIF Search API compliance")
            
            # Test 4: Demonstrate configuration control
            print("\n7. Testing configuration control...")
            app.config['RDM_IIIF_SEARCH_ENABLED'] = False
            
            disabled_manifest = create_sample_manifest_with_search()
            has_services = 'service' in disabled_manifest
            
            print(f"   With RDM_IIIF_SEARCH_ENABLED=False: Services injected = {has_services}")
            
            app.config['RDM_IIIF_SEARCH_ENABLED'] = True
            enabled_manifest = create_sample_manifest_with_search()
            has_services = 'service' in enabled_manifest
            
            print(f"   With RDM_IIIF_SEARCH_ENABLED=True: Services injected = {has_services}")
            
            return manifest
            
        except Exception as e:
            print(f"❌ Error during spike prototype execution: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    main()
