#!/usr/bin/env python3
"""
Integration tests for new OppNDA modern UI features.
Run with: python tests/test_modern_ui.py
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.path_utils import (
    resolve_absolute_path,
    validate_path,
    safe_path_join,
    normalize_path_separators,
    get_relative_path,
    is_path_within
)


class TestPathUtils(unittest.TestCase):
    """Test path utility functions."""
    
    def setUp(self):
        """Create temporary test directory."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, 'test.txt')
        with open(self.test_file, 'w') as f:
            f.write('test content')
    
    def tearDown(self):
        """Clean up test directory."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)
    
    def test_resolve_absolute_path_relative(self):
        """Test resolving relative paths."""
        path = './test.txt'
        result = resolve_absolute_path(path)
        self.assertTrue(os.path.isabs(result))
    
    def test_resolve_absolute_path_tilde(self):
        """Test resolving ~ paths."""
        path = '~/test'
        result = resolve_absolute_path(path)
        self.assertNotIn('~', result)
        self.assertTrue(os.path.isabs(result))
    
    def test_resolve_absolute_path_absolute(self):
        """Test resolving absolute paths."""
        result = resolve_absolute_path(self.test_file)
        self.assertEqual(result, os.path.abspath(self.test_file))
    
    def test_validate_path_exists(self):
        """Test validating existing paths."""
        is_valid, error = validate_path(self.test_file, must_exist=True)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_path_not_exists(self):
        """Test validating non-existing paths."""
        fake_path = os.path.join(self.test_dir, 'fake_file.txt')
        is_valid, error = validate_path(fake_path, must_exist=True)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_validate_path_is_dir(self):
        """Test validating directory requirement."""
        is_valid, error = validate_path(self.test_dir, must_be_dir=True)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_path_file_not_dir(self):
        """Test that files fail directory validation."""
        is_valid, error = validate_path(self.test_file, must_be_dir=True)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_safe_path_join(self):
        """Test safe path joining."""
        result = safe_path_join(self.test_dir, 'subfolder', 'file.txt')
        self.assertTrue(os.path.isabs(result))
        self.assertIn('subfolder', result)
        self.assertIn('file.txt', result)
    
    def test_normalize_path_separators(self):
        """Test path separator normalization."""
        path = 'folder\\subfolder\\file.txt'
        result = normalize_path_separators(path)
        self.assertNotIn('\\', result)
        self.assertIn('/', result)
    
    def test_get_relative_path(self):
        """Test getting relative paths."""
        base = self.test_dir
        target = self.test_file
        result = get_relative_path(target, base)
        self.assertNotIn('..', result)
        self.assertIn('test.txt', result)
    
    def test_is_path_within(self):
        """Test path containment check."""
        base = self.test_dir
        target = self.test_file
        
        # File is within directory
        self.assertTrue(is_path_within(target, base))
        
        # Directory is not within file
        self.assertFalse(is_path_within(base, target))


class TestAPIEndpoints(unittest.TestCase):
    """Test API endpoint functionality (requires Flask app)."""
    
    @classmethod
    def setUpClass(cls):
        """Set up Flask test client."""
        try:
            from app import create_app
            app = create_app()
            cls.client = app.test_client()
            cls.app = app
            cls.available = True
        except ImportError:
            cls.available = False
            print("Warning: Flask app not available, skipping API tests")
    
    @unittest.skipIf(not hasattr(unittest.TestCase, 'setUpClass'), "Skip API tests")
    def test_browse_directory_home(self):
        """Test browsing home directory."""
        if not self.available:
            self.skipTest("Flask app not available")
        
        response = self.client.post('/api/browse-directory', 
            json={'path': '', 'filter_type': 'dirs'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertIn('current_path', data)
        self.assertIn('directories', data)
    
    @unittest.skipIf(not hasattr(unittest.TestCase, 'setUpClass'), "Skip API tests")
    def test_resolve_path_tilde(self):
        """Test path resolution endpoint."""
        if not self.available:
            self.skipTest("Flask app not available")
        
        response = self.client.post('/api/resolve-path',
            json={'path': '~/test'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertIn('absolute_path', data)
        self.assertNotIn('~', data['absolute_path'])
    
    @unittest.skipIf(not hasattr(unittest.TestCase, 'setUpClass'), "Skip API tests")
    def test_auto_save_config(self):
        """Test auto-save endpoint."""
        if not self.available:
            self.skipTest("Flask app not available")
        
        response = self.client.post('/api/save-config',
            json={
                'config': 'analysis',
                'changes': {'test_field': 'test_value'}
            }
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))


class TestUIComponents(unittest.TestCase):
    """Test UI component functionality."""
    
    def test_pattern_builder_js_exists(self):
        """Test pattern builder JavaScript exists."""
        path = Path('GUI/pattern-builder.js')
        self.assertTrue(path.exists(), "pattern-builder.js not found")
    
    def test_directory_browser_js_exists(self):
        """Test directory browser JavaScript exists."""
        path = Path('GUI/directory-browser.js')
        self.assertTrue(path.exists(), "directory-browser.js not found")
    
    def test_auto_save_js_exists(self):
        """Test auto-save JavaScript exists."""
        path = Path('GUI/auto-save.js')
        self.assertTrue(path.exists(), "auto-save.js not found")
    
    def test_settings_modern_css_exists(self):
        """Test modern CSS exists."""
        path = Path('GUI/settings-modern.css')
        self.assertTrue(path.exists(), "settings-modern.css not found")
    
    def test_directory_browser_css_exists(self):
        """Test directory browser CSS exists."""
        path = Path('GUI/directory-browser.css')
        self.assertTrue(path.exists(), "directory-browser.css not found")
    
    def test_path_utils_py_exists(self):
        """Test path utilities Python module exists."""
        path = Path('core/path_utils.py')
        self.assertTrue(path.exists(), "path_utils.py not found")
    
    def test_settings_html_has_scripts(self):
        """Test settings.html includes new scripts."""
        with open('GUI/settings.html', 'r') as f:
            content = f.read()
        
        self.assertIn('pattern-builder.js', content)
        self.assertIn('directory-browser.js', content)
        self.assertIn('auto-save.js', content)
        self.assertIn('settings-modern.css', content)
        self.assertIn('directory-browser.css', content)


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestPathUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestUIComponents))
    
    # Only add API tests if Flask is available
    try:
        from app import create_app
        suite.addTests(loader.loadTestsFromTestCase(TestAPIEndpoints))
    except ImportError:
        print("Note: Flask tests skipped (Flask app not available)")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
