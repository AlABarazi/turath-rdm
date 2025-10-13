"""Turath InvenioRDM site package."""

from .iiif_patch import init_iiif_search_patch
from .test_signal_handler import register_test_handlers


def init_app(app):
    """Initialize the Turath site package."""
    # Apply IIIF Search services patch
    init_iiif_search_patch(app)
    
    # Register test signal handlers for T1 research
    register_test_handlers(app)