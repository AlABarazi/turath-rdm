"""Turath InvenioRDM site package."""

from .iiif_patch import init_iiif_search_patch
from .test_signal_handler import register_test_handlers


def init_app(app):
    """Initialize the Turath site package."""
    # Provide default Mirador configuration; can be overridden by instance config
    app.config.setdefault(
        "MIRADOR_PREVIEW_EXTENSIONS",
        ["pdf", "tif", "tiff", "jpg", "jpeg", "png"],
    )
    app.config.setdefault(
        "MIRADOR_PREVIEW_CONFIG",
        {
            "id": "mirador-viewer",
            "windows": [{}],
            "window": {
                "allowClose": False,
                "allowMaximize": False,
                "allowFullscreen": True,
            },
            "workspaceControlPanel": {"enabled": False},
        },
    )
    # Apply IIIF Search services patch
    init_iiif_search_patch(app)
    
    # Register test signal handlers for T1 research
    register_test_handlers(app)