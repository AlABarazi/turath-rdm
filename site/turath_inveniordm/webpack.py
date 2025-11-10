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
            },
        ),
    },
)
