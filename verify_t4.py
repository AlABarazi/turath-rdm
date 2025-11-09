#!/usr/bin/env python3
"""
Verification script for T4: Add Mirador configuration to site config

Run with: pipenv run python verify_t4.py
"""

import sys


def test_app_config_has_mirador_keys():
    print("\n🧪 Loading app and checking Mirador config keys...")
    try:
        from invenio_app.factory import create_app
    except Exception as e:
        print(f"  ❌ Could not import create_app: {e}")
        return False

    try:
        app = create_app()
        with app.app_context():
            exts = app.config.get('MIRADOR_PREVIEW_EXTENSIONS')
            cfg = app.config.get('MIRADOR_PREVIEW_CONFIG')
            if not isinstance(exts, (list, tuple)):
                print(f"  ❌ MIRADOR_PREVIEW_EXTENSIONS not list/tuple: {type(exts)}")
                return False
            if not isinstance(cfg, dict):
                print(f"  ❌ MIRADOR_PREVIEW_CONFIG not dict: {type(cfg)}")
                return False
            if 'pdf' not in [str(x).lower() for x in exts]:
                print(f"  ❌ 'pdf' not in MIRADOR_PREVIEW_EXTENSIONS: {exts}")
                return False
            if cfg.get('id') != 'mirador-viewer':
                print(f"  ❌ MIRADOR_PREVIEW_CONFIG.id unexpected: {cfg.get('id')} ")
                return False
            print("  ✅ MIRADOR_PREVIEW_EXTENSIONS and MIRADOR_PREVIEW_CONFIG loaded correctly")
            return True
    except Exception as e:
        print(f"  ❌ Error creating app or reading config: {e}")
        return False


def main():
    print("=" * 60)
    print("🔍 T4 Verification: Mirador Configuration in App Config")
    print("=" * 60)

    results = [test_app_config_has_mirador_keys()]

    print("\n" + "=" * 60)
    if all(results):
        print("✅ ALL CHECKS PASSED - T4 Config is loaded and valid!")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Review output above")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
