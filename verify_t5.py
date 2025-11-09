#!/usr/bin/env python3
"""
Verification script for T5: Add Mirador assets (JS/CSS)

Run with: pipenv run python verify_t5.py
"""

import sys
from pathlib import Path


def verify_template_includes_assets() -> bool:
    print("\n🧪 Checking template includes Mirador CDN assets...")
    tpl_path = Path(
        "site/turath_inveniordm/templates/semantic-ui/"
        "invenio_app_rdm/records/previewers/mirador_preview.html"
    )
    if not tpl_path.exists():
        print(f"  ❌ Missing template: {tpl_path}")
        return False

    src = tpl_path.read_text(encoding="utf-8")

    checks = [
        ("mirador.min.css" in src, "Contains Mirador CSS link"),
        ("mirador.min.js" in src, "Contains Mirador JS script"),
        ("{% block css %}" in src, "Uses css block for styles"),
        ("{% block javascript %}" in src, "Uses javascript block for scripts"),
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
    print("🔍 T5 Verification: Mirador Assets in Template")
    print("=" * 60)

    results = [verify_template_includes_assets()]

    print("\n" + "=" * 60)
    if all(results):
        print("✅ ALL CHECKS PASSED - T5 Assets are referenced correctly!")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Review output above")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
