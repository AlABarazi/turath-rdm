#!/usr/bin/env python3
"""
Verification script for T2: Register previewer entry point

Run with: pipenv run python verify_t2.py
"""

import sys


def test_entry_point_registered():
    """Verify entry point is registered in the system."""
    print("\n🧪 Testing entry point registration...")
    
    try:
        from importlib.metadata import entry_points
        
        # Get all previewer entry points
        previewer_eps = list(entry_points().select(group='invenio_previewer.previewers'))
        
        # Check if our previewer is in the list
        mirador_ep = None
        for ep in previewer_eps:
            if ep.name == 'mirador_previewer':
                mirador_ep = ep
                break
        
        if mirador_ep:
            print(f"  ✅ Entry point 'mirador_previewer' found")
            print(f"     Name: {mirador_ep.name}")
            print(f"     Value: {mirador_ep.value}")
            
            # Verify it points to correct module
            expected_value = "turath_inveniordm.previewer.mirador_previewer"
            if mirador_ep.value == expected_value:
                print(f"  ✅ Points to correct module: {expected_value}")
                return True
            else:
                print(f"  ❌ Points to wrong module: {mirador_ep.value}")
                print(f"     Expected: {expected_value}")
                return False
        else:
            print(f"  ❌ Entry point 'mirador_previewer' not found")
            print(f"     Available previewers: {[ep.name for ep in previewer_eps]}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error checking entry points: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_module_can_be_loaded():
    """Verify the entry point can load the module."""
    print("\n🧪 Testing module can be loaded via entry point...")
    
    try:
        from importlib.metadata import entry_points
        
        # Get the entry point
        previewer_eps = list(entry_points().select(group='invenio_previewer.previewers'))
        mirador_ep = None
        for ep in previewer_eps:
            if ep.name == 'mirador_previewer':
                mirador_ep = ep
                break
        
        if not mirador_ep:
            print("  ❌ Entry point not found (run test 1 first)")
            return False
        
        # Try to load the module
        module = mirador_ep.load()
        print(f"  ✅ Module loaded successfully: {module}")
        
        # Check for required functions
        if hasattr(module, 'can_preview'):
            print(f"  ✅ Function 'can_preview' exists")
        else:
            print(f"  ❌ Function 'can_preview' missing")
            return False
        
        if hasattr(module, 'preview'):
            print(f"  ✅ Function 'preview' exists")
        else:
            print(f"  ❌ Function 'preview' missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error loading module: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_site_package_installed():
    """Verify turath-inveniordm package is installed."""
    print("\n🧪 Testing site package installation...")
    
    try:
        import importlib.metadata
        
        # Check if package is installed
        dist = importlib.metadata.distribution('turath-inveniordm')
        print(f"  ✅ Package 'turath-inveniordm' installed")
        print(f"     Version: {dist.version}")
        print(f"     Location: {dist.locate_file('')}")
        
        return True
        
    except importlib.metadata.PackageNotFoundError:
        print(f"  ❌ Package 'turath-inveniordm' not found")
        print(f"     Run: pipenv install -e site")
        return False
    except Exception as e:
        print(f"  ❌ Error checking package: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("🔍 T2 Verification: Entry Point Registration")
    print("=" * 60)
    
    tests = [
        test_site_package_installed,
        test_entry_point_registered,
        test_module_can_be_loaded,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ ALL CHECKS PASSED - T2 Entry Point is Registered!")
        print("=" * 60)
        print("\n🎯 Next: InvenioRDM will now discover the Mirador previewer")
        print("   When you restart InvenioRDM, it will load automatically.")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Review output above")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
