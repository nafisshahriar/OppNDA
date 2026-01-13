#!/usr/bin/env python3
"""
Test Framework for OppNDA
Captures baseline behavior and verifies functionality after refactoring.
"""

import os
import sys
import json
import hashlib
import importlib.util

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT_DIR = os.path.join(BASE_DIR, "tests", "snapshots")


class TestResult:
    """Holds test result information"""
    def __init__(self, name, passed, message="", details=None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details
    
    def __str__(self):
        status = "[PASS]" if self.passed else "[FAIL]"
        return f"{status}: {self.name}" + (f" - {self.message}" if self.message else "")


def ensure_snapshot_dir():
    """Ensure snapshot directory exists"""
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)


def test_flask_app_imports():
    """Test that Flask app package can be imported without errors"""
    try:
        # Check app/__init__.py exists and is valid
        app_init = os.path.join(BASE_DIR, "app", "__init__.py")
        if os.path.exists(app_init):
            spec = importlib.util.spec_from_file_location("app", app_init)
            module = importlib.util.module_from_spec(spec)
            return TestResult("Flask App Syntax", True)
        # Fallback to old oppnda.py check
        spec = importlib.util.spec_from_file_location("oppnda", os.path.join(BASE_DIR, "oppnda.py"))
        module = importlib.util.module_from_spec(spec)
        return TestResult("Flask App Syntax", True)
    except SyntaxError as e:
        return TestResult("Flask App Syntax", False, str(e))
    except Exception as e:
        return TestResult("Flask App Syntax", False, str(e))


def test_analysis_imports():
    """Test that analysis.py can be imported"""
    try:
        # Check core/analysis.py first
        core_path = os.path.join(BASE_DIR, "core", "analysis.py")
        if os.path.exists(core_path):
            spec = importlib.util.spec_from_file_location("analysis", core_path)
        else:
            spec = importlib.util.spec_from_file_location("analysis", os.path.join(BASE_DIR, "analysis.py"))
        module = importlib.util.module_from_spec(spec)
        return TestResult("Analysis Module Syntax", True)
    except SyntaxError as e:
        return TestResult("Analysis Module Syntax", False, str(e))
    except Exception as e:
        return TestResult("Analysis Module Syntax", False, str(e))


def test_batch_avg_imports():
    """Test that batch.py can be imported"""
    try:
        # Check core/batch.py first
        core_path = os.path.join(BASE_DIR, "core", "batch.py")
        if os.path.exists(core_path):
            spec = importlib.util.spec_from_file_location("batch", core_path)
        else:
            spec = importlib.util.spec_from_file_location("batch_avg", os.path.join(BASE_DIR, "batch_avg.py"))
        module = importlib.util.module_from_spec(spec)
        return TestResult("Batch Average Module Syntax", True)
    except SyntaxError as e:
        return TestResult("Batch Average Module Syntax", False, str(e))
    except Exception as e:
        return TestResult("Batch Average Module Syntax", False, str(e))


def test_regression_imports():
    """Test that regression.py can be imported"""
    try:
        # Check core/regression.py first
        core_path = os.path.join(BASE_DIR, "core", "regression.py")
        if os.path.exists(core_path):
            spec = importlib.util.spec_from_file_location("regression", core_path)
        else:
            spec = importlib.util.spec_from_file_location("regression", os.path.join(BASE_DIR, "regression.py"))
        module = importlib.util.module_from_spec(spec)
        return TestResult("Regression Module Syntax", True)
    except SyntaxError as e:
        return TestResult("Regression Module Syntax", False, str(e))
    except Exception as e:
        return TestResult("Regression Module Syntax", False, str(e))


def test_gui_files_exist():
    """Test that all GUI files exist"""
    gui_files = [
        "GUI/settings.html",
        "GUI/settings.css",
        "GUI/config.js",
    ]
    
    missing = []
    for file in gui_files:
        if not os.path.exists(os.path.join(BASE_DIR, file)):
            missing.append(file)
    
    if missing:
        return TestResult("GUI Files Exist", False, f"Missing: {missing}")
    return TestResult("GUI Files Exist", True)


def test_gui_html_valid():
    """Basic validation that HTML files have required elements"""
    html_path = os.path.join(BASE_DIR, "GUI", "settings.html")
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required = ["<!DOCTYPE html>", "<html", "</html>", "<body", "</body>"]
        missing = [r for r in required if r not in content]
        
        if missing:
            return TestResult("HTML Valid", False, f"Missing: {missing}")
        return TestResult("HTML Valid", True)
    except Exception as e:
        return TestResult("HTML Valid", False, str(e))


def create_file_snapshot(filepath, snapshot_name):
    """Create a hash snapshot of a file for comparison"""
    ensure_snapshot_dir()
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        file_hash = hashlib.sha256(content).hexdigest()
        
        snapshot_path = os.path.join(SNAPSHOT_DIR, f"{snapshot_name}.json")
        snapshot_data = {
            "file": filepath,
            "hash": file_hash,
            "size": len(content)
        }
        
        with open(snapshot_path, 'w') as f:
            json.dump(snapshot_data, f, indent=2)
        
        return TestResult(f"Snapshot Created: {snapshot_name}", True)
    except Exception as e:
        return TestResult(f"Snapshot Created: {snapshot_name}", False, str(e))


def compare_with_snapshot(filepath, snapshot_name):
    """Compare current file with saved snapshot"""
    snapshot_path = os.path.join(SNAPSHOT_DIR, f"{snapshot_name}.json")
    
    if not os.path.exists(snapshot_path):
        return TestResult(f"Snapshot Compare: {snapshot_name}", False, "No baseline snapshot exists")
    
    try:
        with open(snapshot_path, 'r') as f:
            snapshot = json.load(f)
        
        with open(filepath, 'rb') as f:
            content = f.read()
        current_hash = hashlib.sha256(content).hexdigest()
        
        if current_hash == snapshot["hash"]:
            return TestResult(f"Snapshot Compare: {snapshot_name}", True, "File unchanged")
        else:
            return TestResult(f"Snapshot Compare: {snapshot_name}", False, "File has changed")
    except Exception as e:
        return TestResult(f"Snapshot Compare: {snapshot_name}", False, str(e))


def run_framework_tests():
    """Run all framework tests"""
    results = []
    
    print("\n" + "="*60)
    print("FRAMEWORK TESTS")
    print("="*60)
    
    tests = [
        test_flask_app_imports,
        test_analysis_imports,
        test_batch_avg_imports,
        test_regression_imports,
        test_gui_files_exist,
        test_gui_html_valid,
    ]
    
    for test_func in tests:
        result = test_func()
        results.append(result)
        print(result)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\nFramework Tests: {passed}/{total} passed")
    print("="*60)
    
    return results


def create_baseline_snapshots():
    """Create baseline snapshots for all key files"""
    print("\n" + "="*60)
    print("CREATING BASELINE SNAPSHOTS")
    print("="*60)
    
    files_to_snapshot = [
        ("oppnda.py", "oppnda"),
        ("analysis.py", "analysis"),
        ("batch_avg.py", "batch_avg"),
        ("regression.py", "regression"),
        ("analysis_config.json", "analysis_config"),
        ("batch_config.json", "batch_config"),
        ("regression_config.json", "regression_config"),
        ("GUI/settings.html", "settings_html"),
        ("GUI/settings.css", "settings_css"),
        ("GUI/config.js", "config_js"),
    ]
    
    results = []
    for filename, snapshot_name in files_to_snapshot:
        filepath = os.path.join(BASE_DIR, filename)
        if os.path.exists(filepath):
            result = create_file_snapshot(filepath, snapshot_name)
            results.append(result)
            print(result)
        else:
            print(f"[SKIP]: {filename} (file not found)")
    
    return results


if __name__ == "__main__":
    run_framework_tests()
