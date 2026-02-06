"""JS/CSS Webpack bundles for turath-inveniordm."""

from invenio_assets.webpack import WebpackThemeBundle

theme = WebpackThemeBundle(
    __name__,
    "assets",
    default="semantic-ui",
    themes={
        "semantic-ui": dict(
            entry={
                # Add your webpack entrypoints
                "turath-mirador-init": "./js/mirador_init.js",
                "turath-base-theme-rdm": (
                    "./js/turath_inveniordm/turath_base_theme_rdm.js"
                ),
            },
            aliases={
                "@js/invenio_app_rdm/overridableRegistry/mapping": "js/invenio_app_rdm/overridableRegistry/mapping.js",
            },
        ),
    },
)
