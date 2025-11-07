"""Mirador IIIF viewer previewer for InvenioRDM.

This previewer displays PDF and TIFF files using the Mirador viewer,
leveraging InvenioRDM's built-in dynamic IIIF manifest generation.

Based on Zenodo RDM's image_previewer.py implementation.
"""

from flask import current_app, render_template


def can_preview(file):
    """Check if file can be previewed with Mirador.
    
    Args:
        file: File object from InvenioRDM record
        
    Returns:
        bool: True if file extension is supported for Mirador preview
        
    Supported extensions are defined in config.MIRADOR_PREVIEW_EXTENSIONS
    """
    # Get supported extensions from config (default to PDF and TIFF)
    supported_exts = current_app.config.get(
        'MIRADOR_PREVIEW_EXTENSIONS',
        ['pdf', 'tif', 'tiff', 'jpg', 'jpeg', 'png']
    )
    
    # Check if file extension matches any supported extension
    file_ext = file.get('key', '').split('.')[-1].lower()
    return file_ext in supported_exts


def preview(file):
    """Render Mirador viewer for the file.
    
    Args:
        file: File object from InvenioRDM record
        
    Returns:
        str: Rendered HTML template with Mirador viewer
        
    The template receives:
    - file: The file object
    - manifest_url: Dynamic IIIF manifest URL from InvenioRDM
    - mirador_config: Configuration dictionary for Mirador viewer
    """
    # Get the dynamic IIIF manifest URL from the record
    # InvenioRDM v13 provides this in file.record["links"]["self_iiif_manifest"]
    manifest_url = file.record.get("links", {}).get("self_iiif_manifest")
    
    # Get Mirador configuration from app config
    mirador_config = current_app.config.get('MIRADOR_PREVIEW_CONFIG', {
        'id': 'mirador-viewer',
        'windows': [{
            'manifestId': manifest_url,
        }],
        'window': {
            'allowClose': False,
            'allowMaximize': False,
            'allowFullscreen': True,
        },
        'workspaceControlPanel': {
            'enabled': False,
        },
    })
    
    # Ensure manifest URL is in the config
    if manifest_url and mirador_config.get('windows'):
        mirador_config['windows'][0]['manifestId'] = manifest_url
    
    # Render the Mirador preview template
    # Template path: templates/semantic-ui/invenio_app_rdm/records/previewers/mirador_preview.html
    return render_template(
        'invenio_app_rdm/records/previewers/mirador_preview.html',
        file=file,
        manifest_url=manifest_url,
        mirador_config=mirador_config,
    )
