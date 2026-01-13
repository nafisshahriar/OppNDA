#!/usr/bin/env python3
"""
Config File Validation Tests
Tests that all JSON config files are valid and have expected structure.
"""

import os
import sys
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Expected schema structures (required keys)
ANALYSIS_CONFIG_SCHEMA = {
    "directories": ["report_dir", "plots_dir"],
    "metrics": ["include", "ignore"],
    "enabled_plots": [],
    "plot_settings": []
}

BATCH_CONFIG_SCHEMA = {
    "folder": None,
    "filename_pattern": ["delimiter", "components"],
    "average_groups": []
}

REGRESSION_CONFIG_SCHEMA = {
    "input": ["csv_directory"],
    "features": ["target", "predictors"],
    "model_settings": ["enabled_models"],
    "output": ["directory"]
}


class ConfigTestResult:
    """Holds test result information"""
    def __init__(self, name, passed, message=""):
        self.name = name
        self.passed = passed
        self.message = message
    
    def __str__(self):
        status = "[PASS]" if self.passed else "[FAIL]"
        return f"{status}: {self.name}" + (f" - {self.message}" if self.message else "")


def test_json_valid(filepath):
    """Test that a JSON file is valid"""
    try:
        with open(filepath, 'r') as f:
            json.load(f)
        return ConfigTestResult(f"JSON Valid: {os.path.basename(filepath)}", True)
    except json.JSONDecodeError as e:
        return ConfigTestResult(f"JSON Valid: {os.path.basename(filepath)}", False, str(e))
    except FileNotFoundError:
        return ConfigTestResult(f"JSON Valid: {os.path.basename(filepath)}", False, "File not found")


def test_schema(filepath, schema, config_name):
    """Test that a config file has required keys"""
    try:
        with open(filepath, 'r') as f:
            config = json.load(f)
        
        missing_keys = []
        for key, subkeys in schema.items():
            if key not in config:
                missing_keys.append(key)
            elif subkeys and isinstance(subkeys, list):
                for subkey in subkeys:
                    if subkey not in config[key]:
                        missing_keys.append(f"{key}.{subkey}")
        
        if missing_keys:
            return ConfigTestResult(f"Schema: {config_name}", False, f"Missing: {missing_keys}")
        return ConfigTestResult(f"Schema: {config_name}", True)
    except Exception as e:
        return ConfigTestResult(f"Schema: {config_name}", False, str(e))


def test_config_read_write(filepath):
    """Test that config can be read, modified, and written back"""
    try:
        # Read
        with open(filepath, 'r') as f:
            original = json.load(f)
        
        # Write back (without modification)
        temp_path = filepath + ".test"
        with open(temp_path, 'w') as f:
            json.dump(original, f, indent=2)
        
        # Verify
        with open(temp_path, 'r') as f:
            reloaded = json.load(f)
        
        # Cleanup
        os.remove(temp_path)
        
        if original == reloaded:
            return ConfigTestResult(f"Read/Write: {os.path.basename(filepath)}", True)
        else:
            return ConfigTestResult(f"Read/Write: {os.path.basename(filepath)}", False, "Data mismatch after write")
    except Exception as e:
        if os.path.exists(filepath + ".test"):
            os.remove(filepath + ".test")
        return ConfigTestResult(f"Read/Write: {os.path.basename(filepath)}", False, str(e))


def run_config_tests():
    """Run all config file tests"""
    results = []
    
    # Updated paths to config/ directory
    config_dir = os.path.join(BASE_DIR, "config")
    config_files = [
        (os.path.join(config_dir, "analysis_config.json"), ANALYSIS_CONFIG_SCHEMA, "analysis_config"),
        (os.path.join(config_dir, "batch_config.json"), BATCH_CONFIG_SCHEMA, "batch_config"),
        (os.path.join(config_dir, "regression_config.json"), REGRESSION_CONFIG_SCHEMA, "regression_config"),
    ]
    
    print("\n" + "="*60)
    print("CONFIG FILE TESTS")
    print("="*60)
    
    for filepath, schema, name in config_files:
        # Test JSON validity
        result = test_json_valid(filepath)
        results.append(result)
        print(result)
        
        # Test schema
        if result.passed:
            result = test_schema(filepath, schema, name)
            results.append(result)
            print(result)
            
            # Test read/write
            result = test_config_read_write(filepath)
            results.append(result)
            print(result)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\nConfig Tests: {passed}/{total} passed")
    print("="*60)
    
    return results


if __name__ == "__main__":
    run_config_tests()
