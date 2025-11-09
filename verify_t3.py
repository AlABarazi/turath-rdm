#!/usr/bin/env python3
"""
Verification script for T3: Create Mirador preview template

Run with: pipenv run python verify_t3.py
"""

import sys
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, DictLoader, ChoiceLoader


def verify_template_exists() -> bool:
    print("\n🧪 Checking template file exists at expected path...")
    tpl_path = Path(
        "site/turath_inveniordm/templates/semantic-ui/"
        "invenio_app_rdm/records/previewers/mirador_preview.html"
    )
    if tpl_path.exists():
        print(f"  ✅ Found: {tpl_path}")
        return True
    print(f"  ❌ Missing: {tpl_path}")
    return False


def verify_template_renders() -> bool:
    print("\n🧪 Rendering template with minimal Jinja environment...")

    # Provide a minimal abstract base so Jinja can resolve the extends
    abstract_name = "previewer_abstract_test.html"
    abstract_src = (
        "{% block panel %}{% endblock %}\n"
        "{% block javascript %}{% endblock %}\n"
    )

    # Load our site templates root
    site_templates_root = (
        Path("site/turath_inveniordm/templates/semantic-ui").resolve()
    )

    env = Environment(
        loader=ChoiceLoader([
            DictLoader({abstract_name: abstract_src}),
            FileSystemLoader(str(site_templates_root)),
        ])
    )

    # Provide a fallback tojson filter (Flask normally provides this)
    env.filters.setdefault("tojson", lambda v: json.dumps(v))

    # Resolve our template
    template_name = (
        "invenio_app_rdm/records/previewers/mirador_preview.html"
    )

    try:
        template = env.get_template(template_name)
    except Exception as e:
        print(f"  ❌ Failed to load template: {e}")
        return False

    context = {
        # Simulate Flask's `config` available in templates
        "config": {"PREVIEWER_ABSTRACT_TEMPLATE": abstract_name},
        # Required context variables used by the template
        "manifest_url": "https://127.0.0.1:5000/api/iiif/record:test/manifest",
        "mirador_config": {"id": "mirador-viewer", "windows": [{}]},
    }

    try:
        html = template.render(**context)
    except Exception as e:
        print(f"  ❌ Rendering error: {e}")
        return False

    # Basic assertions
    checks = [
        ("mirador-viewer" in html, "Contains Mirador container id"),
        ("record:test/manifest" in html, "Contains manifest URL"),
    ]

    all_ok = True
    for ok, msg in checks:
        if ok:
            print(f"  ✅ {msg}")
        else:
            print(f"  ❌ {msg}")
            all_ok = False

    return all_ok


def main():
    print("=" * 60)
    print("🔍 T3 Verification: Mirador Preview Template")
    print("=" * 60)

    tests = [verify_template_exists, verify_template_renders]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    if all(results):
        print("✅ ALL CHECKS PASSED - T3 Template is valid and renderable!")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Review output above")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
