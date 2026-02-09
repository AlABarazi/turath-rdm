"""
IIIF Manifest Monkey Patch for Turath InvenioRDM.

Adds:
- IIIF Search + Autocomplete services
- Per-page canvases for PDFs using the app's /iiif proxy
- Per-canvas HOCR seeAlso and top-level related PDF

This avoids forking core code while meeting our manifest schema requirements.
"""

import os
import re
import json
from urllib.parse import quote

import requests
from flask import current_app
from invenio_rdm_records.resources.serializers.iiif.schema import IIIFManifestV2Schema

from .cantaloupe_mirror import get_cantaloupe_files_base


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
        # Ensure @context includes Search API context
        ctx = manifest.get("@context")
        if isinstance(ctx, str):
            ctx_list = [ctx]
        elif isinstance(ctx, list):
            ctx_list = ctx[:]
        else:
            ctx_list = []
        pres_ctx = "http://iiif.io/api/presentation/2/context.json"
        search_ctx = "http://iiif.io/api/search/0/context.json"
        if pres_ctx not in ctx_list:
            ctx_list.insert(0, pres_ctx)
        if search_ctx not in ctx_list:
            ctx_list.append(search_ctx)
        manifest["@context"] = ctx_list

        # =============================
        # Build canvases for PDF pages with HOCR seeAlso
        # =============================
        try:
            app_base = (
                current_app.config.get('APP_BASE')
                or os.environ.get('APP_BASE')
                or 'https://127.0.0.1:5000'
            )
            app_api_base = (
                current_app.config.get('APP_API_BASE')
                or os.environ.get('APP_API_BASE')
                or app_base
            )
        except Exception:
            app_base = 'https://127.0.0.1:5000'
            app_api_base = app_base

        # Fetch record files metadata from REST API to find the PDF & HOCR files
        pdf_key = None
        hocr_keys = []
        try:
            api_url = f"{app_api_base}/api/records/{record_pid}"
            r = requests.get(api_url, timeout=10, verify=False)
            if r.ok:
                data = r.json()
                entries = (data.get('files') or {}).get('entries') or {}
                # entries can be a dict mapping filename -> file obj, or a list of file objs
                if isinstance(entries, dict):
                    for map_key, e in entries.items():
                        key = e.get('key') or map_key or ''
                        key_l = key.lower()
                        if key_l.endswith('.pdf'):
                            pdf_key = key
                        elif key_l.endswith('.hocr'):
                            hocr_keys.append(key)
                elif isinstance(entries, list):
                    for e in entries:
                        key = (e or {}).get('key') or (e or {}).get('id') or ''
                        key_l = key.lower()
                        if key_l.endswith('.pdf'):
                            pdf_key = key
                        elif key_l.endswith('.hocr'):
                            hocr_keys.append(key)
        except Exception:
            # If API call fails, keep manifest as-is
            return manifest

        if not pdf_key:
            # No PDF found; nothing to do
            return manifest

        # Determine page count: prefer HOCR count, fallback to dimensions.json, then 1
        page_nums = []
        for key in hocr_keys:
            m = re.search(r"(\d{3})\.hocr$", key)
            if m:
                try:
                    page_nums.append(int(m.group(1)))
                except Exception:
                    continue
        hocr_page_count = max(page_nums) if page_nums else 0

        enc_id = quote(f"{record_pid}!{pdf_key}", safe="!")

        # Load dimensions cache (generated during PDF mirroring)
        cached_dims = []
        try:
            dims_path = get_cantaloupe_files_base() / record_pid / "dimensions.json"
            if dims_path.exists():
                with open(dims_path, "r") as f:
                    cached_dims = json.load(f)
        except Exception:
            pass

        page_count = max(hocr_page_count, len(cached_dims), 1)

        # Helper to fetch per-page dimensions
        def get_dims(page: int):
            # Use cached dimensions if available (page is 1-indexed)
            if cached_dims and 0 <= page - 1 < len(cached_dims):
                d = cached_dims[page - 1]
                return d["w"], d["h"]
            
            # Fallback to standard A4 if no cache (fast but maybe misaligned)
            return 1240, 1754

        # Construct sequence and canvases
        seq_id = f"{app_base}/records/{record_pid}/sequence/normal"
        canvases = []
        proxy_base = f"{app_base}/iiif/2/{enc_id}"

        for page in range(1, page_count + 1):
            w, h = get_dims(page)
            pstr = f"{page:03d}"
            canvas_uri = f"{app_base}/records/{record_pid}/canvas/p{pstr}"
            # Use page-qualified image service base so viewer requests '/pN/...' tiles
            page_service_base = f"{proxy_base}/p{page}"
            image_api_id = f"{page_service_base}/full/full/0/default.jpg"
            image_service_id = page_service_base

            canvas = {
                "@id": canvas_uri,
                "@type": "sc:Canvas",
                "label": f"p. {pstr}",
                "width": w,
                "height": h,
                "images": [
                    {
                        "@type": "oa:Annotation",
                        "motivation": "sc:painting",
                        "on": canvas_uri,
                        "resource": {
                            "@id": image_api_id,
                            "@type": "dctypes:Image",
                            "format": "image/jpeg",
                            "service": {
                                "@context": "http://iiif.io/api/image/2/context.json",
                                "@id": image_service_id,
                                "profile": "http://iiif.io/api/image/2/level2.json",
                            },
                            "width": w,
                            "height": h,
                        },
                    }
                ],
                "otherContent": [
                    {
                        "@id": f"{base_url}/annotations/{record_pid}/p{pstr}",
                        "@type": "sc:AnnotationList",
                        "label": f"Text of page {pstr}",
                    }
                ],
                "seeAlso": [
                    {
                        "@id": f"{app_base}/records/{record_pid}/files/{pstr}.hocr",
                        "format": "text/vnd.hocr+html",
                        "profile": "http://kba.github.io/hocr-spec/1.2/",
                        "label": "HOCR OCR text",
                    }
                ],
            }
            canvases.append(canvas)

        manifest["sequences"] = [
            {
                "@id": seq_id,
                "@type": "sc:Sequence",
                "label": "Current Page Order",
                "viewingDirection": "left-to-right",
                "viewingHint": "paged",
                "canvases": canvases,
            }
        ]

        # Top-level related PDF link (actual filename)
        manifest["related"] = {
            "@id": f"{app_base}/records/{record_pid}/files/{pdf_key}",
            "format": "application/pdf",
            "label": "Download full PDF",
        }

        return manifest
    
    # Apply the monkey patch
    IIIFManifestV2Schema.sortcanvases = enhanced_sortcanvases


def init_iiif_search_patch(app):
    """Initialize the IIIF Search services patch."""
    with app.app_context():
        patch_iiif_manifest_schema()
        app.logger.info("IIIF Search services patch applied successfully")
