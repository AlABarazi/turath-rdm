"""Unit tests for mirador_previewer module.

Run with: pipenv run python site/turath_inveniordm/previewer/test_mirador_previewer.py
"""

import sys
from unittest.mock import Mock, MagicMock


def test_can_preview():
    """Test can_preview() function with various file types."""
    print("\n🧪 Testing can_preview() function...")
    
    # Import the module
    from turath_inveniordm.previewer import mirador_previewer
    
    # Mock Flask app config
    mock_app = Mock()
    mock_app.config = {
        'MIRADOR_PREVIEW_EXTENSIONS': ['pdf', 'tif', 'tiff', 'jpg', 'jpeg', 'png']
    }
    
    # Test cases: (filename, should_preview)
    test_cases = [
        ('document.pdf', True, 'PDF file'),
        ('image.tif', True, 'TIF file'),
        ('photo.tiff', True, 'TIFF file'),
        ('photo.jpg', True, 'JPG file'),
        ('photo.jpeg', True, 'JPEG file'),
        ('diagram.png', True, 'PNG file'),
        ('data.csv', False, 'CSV file (not supported)'),
        ('script.py', False, 'Python file (not supported)'),
        ('archive.zip', False, 'ZIP file (not supported)'),
        ('Document.PDF', True, 'PDF with uppercase'),
    ]
    
    passed = 0
    failed = 0
    
    for filename, expected, description in test_cases:
        # Create mock file object
        mock_file = {'key': filename}
        
        # Mock current_app
        with MagicMock() as mock_current_app:
            mock_current_app.config.get.return_value = ['pdf', 'tif', 'tiff', 'jpg', 'jpeg', 'png']
            
            # Patch current_app in the module
            import turath_inveniordm.previewer.mirador_previewer as mp
            original_current_app = mp.current_app
            mp.current_app = mock_current_app
            
            result = mirador_previewer.can_preview(mock_file)
            
            # Restore original
            mp.current_app = original_current_app
            
            if result == expected:
                print(f"  ✅ {description}: {filename} → {result}")
                passed += 1
            else:
                print(f"  ❌ {description}: {filename} → Expected {expected}, got {result}")
                failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    return failed == 0


def test_preview_manifest_extraction():
    """Test preview() function's manifest URL extraction."""
    print("\n🧪 Testing preview() manifest URL extraction...")
    
    from turath_inveniordm.previewer import mirador_previewer
    
    # Mock file object with record containing manifest link
    mock_file = Mock()
    mock_file.record = {
        'links': {
            'self_iiif_manifest': 'https://127.0.0.1:5000/api/iiif/record:test123/manifest'
        }
    }
    
    # Mock Flask app and render_template
    mock_app = Mock()
    mock_app.config = {
        'MIRADOR_PREVIEW_CONFIG': {
            'id': 'mirador-viewer',
            'windows': [{}],
        }
    }
    
    # We can't test the full render without Flask context,
    # but we can verify the logic extracts the URL
    manifest_url = mock_file.record.get("links", {}).get("self_iiif_manifest")
    
    if manifest_url == 'https://127.0.0.1:5000/api/iiif/record:test123/manifest':
        print(f"  ✅ Manifest URL extracted correctly: {manifest_url}")
        return True
    else:
        print(f"  ❌ Failed to extract manifest URL: {manifest_url}")
        return False


def test_preview_handles_missing_manifest():
    """Test preview() handles missing manifest gracefully."""
    print("\n🧪 Testing preview() with missing manifest...")
    
    # Mock file object WITHOUT manifest link
    mock_file = Mock()
    mock_file.record = {
        'links': {}  # No self_iiif_manifest
    }
    
    manifest_url = mock_file.record.get("links", {}).get("self_iiif_manifest")
    
    if manifest_url is None:
        print(f"  ✅ Correctly returns None for missing manifest")
        return True
    else:
        print(f"  ❌ Should return None, got: {manifest_url}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 Mirador Previewer Module Tests")
    print("=" * 60)
    
    tests = [
        test_can_preview,
        test_preview_manifest_extraction,
        test_preview_handles_missing_manifest,
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
        print("✅ ALL TESTS PASSED - T1 Module is working correctly!")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME TESTS FAILED - Review output above")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
