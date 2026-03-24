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
    # Ensure Mirador previewer has highest priority
    try:
        pref = list(app.config.get("PREVIEWER_PREFERENCE") or [])
        pref = [p for p in pref if p != "mirador_previewer"]
        app.config["PREVIEWER_PREFERENCE"] = ["mirador_previewer"] + pref
    except Exception:
        pass
    # Apply IIIF Search services patch
    init_iiif_search_patch(app)
    
    # Register test signal handlers for T1 research
    register_test_handlers(app)
    
    # Register HOCR sync signal handlers
    try:
        from . import signals as hocr_signals  # noqa: F401
        app.logger.info("✅ HOCR sync signal handlers registered")
    except Exception as e:
        app.logger.error(f"Failed to register HOCR signals: {e}")

    # Import tasks so Celery worker discovers process_record_files at startup
    try:
        from . import tasks as _tasks  # noqa: F401
    except Exception as e:
        app.logger.error(f"Failed to import Celery tasks: {e}")