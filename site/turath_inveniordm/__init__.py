"""Turath InvenioRDM site package."""

from .iiif_patch import init_iiif_search_patch


def init_app(app):
    """Initialize the Turath site package."""
    # Apply IIIF Search services patch
    init_iiif_search_patch(app)