#!/usr/bin/env python3
"""
SmartGallery Configuration System Test Suite
Tests the GalleryConfigManager class in isolation
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Inline GalleryConfigManager for testing (copy from __init__.py)
class GalleryConfigManager:
    """
    Manages SmartGallery configuration with validation and path detection.
    """
    
    DEFAULT_CONFIG = {
        "base_output_path": "",
        "base_input_path": "",
        "server_port": 8008,
        "ffprobe_manual_path": "",
        "auto_detect_paths": True,
        "enable_upload": True,
        "max_upload_size_mb": 100,
        "thumbnail_quality": 85
    }
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load config from file with fallback to defaults"""
        if not self.config_path.exists():
            print(f"## Config file not found, using defaults")
            return self.DEFAULT_CONFIG.copy()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults to handle new keys in updates
                merged = self.DEFAULT_CONFIG.copy()
                merged.update(config)
                return merged
        except Exception as e:
            print(f"!! Failed to load config: {e}")
            return self.DEFAULT_CONFIG.copy()
    
    def save_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and save configuration
        Returns: {"success": bool, "errors": List[str], "warnings": List[str], "message": str}
        """
        validation = self.validate_config(new_config)
        
        if not validation["success"]:
            validation["message"] = "Configuration validation failed"
            return validation
        
        try:
            # Create backup of existing config
            if self.config_path.exists():
                backup_path = self.config_path.with_suffix('.json.bak')
                self.config_path.replace(backup_path)
            
            # Write new config
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=4, ensure_ascii=False)
            
            self.config = new_config
            validation["message"] = "Configuration saved successfully"
            return validation
            
        except Exception as e:
            return {
                "success": False,
                "errors": [f"Failed to save config: {str(e)}"],
                "warnings": [],
                "message": "Save failed"
            }
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive validation with detailed feedback
        Returns: {"success": bool, "errors": List[str], "warnings": List[str]}
        """
        import os
        
        errors = []
        warnings = []
        
        # Validate port
        port = config.get("server_port", 8008)
        if not isinstance(port, int):
            try:
                port = int(port)
                config["server_port"] = port
            except (ValueError, TypeError):
                errors.append("Port must be a valid integer")
        
        if isinstance(port, int) and (port < 1024 or port > 65535):
            errors.append("Port must be between 1024 and 65535")
        
        # Validate paths if auto-detect is disabled
        auto_detect = config.get("auto_detect_paths", True)
        if not auto_detect:
            output_path = config.get("base_output_path", "")
            if output_path:
                output_dir = Path(output_path)
                if not output_dir.exists():
                    warnings.append(f"Output path does not exist: {output_path}")
                elif not output_dir.is_dir():
                    errors.append(f"Output path is not a directory: {output_path}")
                elif not os.access(output_path, os.R_OK):
                    errors.append(f"Output path is not readable: {output_path}")
            else:
                warnings.append("Output path is empty with auto-detect disabled")
            
            input_path = config.get("base_input_path", "")
            if input_path:
                input_dir = Path(input_path)
                if not input_dir.exists():
                    warnings.append(f"Input path does not exist: {input_path}")
                elif not input_dir.is_dir():
                    errors.append(f"Input path is not a directory: {input_path}")
        
        # Validate FFprobe path (optional)
        ffprobe = config.get("ffprobe_manual_path", "")
        if ffprobe:
            ffprobe_path = Path(ffprobe)
            if not ffprobe_path.exists():
                warnings.append(f"FFprobe not found at: {ffprobe}")
            elif not os.access(ffprobe, os.X_OK):
                if sys.platform != 'win32':
                    warnings.append(f"FFprobe exists but may not be executable: {ffprobe}")
        
        # Validate upload settings
        if config.get("enable_upload", True):
            max_size = config.get("max_upload_size_mb", 100)
            if not isinstance(max_size, (int, float)):
                try:
                    max_size = float(max_size)
                    config["max_upload_size_mb"] = max_size
                except (ValueError, TypeError):
                    errors.append("Max upload size must be a number")
            
            if isinstance(max_size, (int, float)) and max_size <= 0:
                errors.append("Max upload size must be greater than 0")
        
        # Validate thumbnail quality
        quality = config.get("thumbnail_quality", 85)
        if not isinstance(quality, int):
            try:
                quality = int(quality)
                config["thumbnail_quality"] = quality
            except (ValueError, TypeError):
                errors.append("Thumbnail quality must be an integer")
        
        if isinstance(quality, int) and (quality < 1 or quality > 100):
            errors.append("Thumbnail quality must be between 1 and 100")
        
        return {
            "success": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def get_detected_paths(self) -> Dict[str, Optional[str]]:
        """Mock path detection for testing"""
        # In real implementation, this would use folder_paths module
        # For testing, return mock values
        return {
            "output_path": "C:/.ai/ComfyUI/output",
            "input_path": "C:/.ai/ComfyUI/input"
        }
    
    def get_effective_config(self) -> Dict[str, Any]:
        """
        Get the effective configuration with auto-detected paths applied
        """
        effective = self.config.copy()
        
        if effective.get("auto_detect_paths", True):
            detected = self.get_detected_paths()
            if detected["output_path"]:
                effective["base_output_path"] = detected["output_path"]
            if detected["input_path"]:
                effective["base_input_path"] = detected["input_path"]
        
        return effective

def print_test_header(test_name):
    """Print a formatted test header"""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print('='*60)

def test_config_manager_initialization():
    """Test GalleryConfigManager initialization"""
    print_test_header("Configuration Manager Initialization")
    
    # Test with non-existent config file
    test_config_path = Path("test_config_temp.json")
    if test_config_path.exists():
        test_config_path.unlink()
    
    manager = GalleryConfigManager(str(test_config_path))
    
    # Should have default config
    assert manager.config is not None, "❌ Config should not be None"
    assert manager.config["server_port"] == 8008, "❌ Default port should be 8008"
    assert manager.config["auto_detect_paths"] == True, "❌ Auto-detect should be enabled by default"
    
    print("✅ Manager initializes with defaults when config.json doesn't exist")
    
    # Test with existing config file
    test_data = {
        "server_port": 8009,
        "base_output_path": "/custom/output",
        "auto_detect_paths": False
    }
    
    with open(test_config_path, 'w') as f:
        json.dump(test_data, f)
    
    manager2 = GalleryConfigManager(str(test_config_path))
    assert manager2.config["server_port"] == 8009, "❌ Should load custom port"
    assert manager2.config["base_output_path"] == "/custom/output", "❌ Should load custom path"
    
    print("✅ Manager loads existing configuration correctly")
    
    # Cleanup
    if test_config_path.exists():
        test_config_path.unlink()
    
    return True

def test_config_validation():
    """Test configuration validation logic"""
    print_test_header("Configuration Validation")
    
    test_config_path = Path("test_config_temp.json")
    manager = GalleryConfigManager(str(test_config_path))
    
    # Test valid configuration
    valid_config = {
        "server_port": 8008,
        "base_output_path": "",
        "base_input_path": "",
        "auto_detect_paths": True,
        "enable_upload": True,
        "max_upload_size_mb": 100,
        "thumbnail_quality": 85,
        "ffprobe_manual_path": ""
    }
    
    result = manager.validate_config(valid_config)
    assert result["success"] == True, f"❌ Valid config should pass: {result['errors']}"
    assert len(result["errors"]) == 0, "❌ Should have no errors"
    print("✅ Valid configuration passes validation")
    
    # Test invalid port
    invalid_port_config = valid_config.copy()
    invalid_port_config["server_port"] = 80
    
    result = manager.validate_config(invalid_port_config)
    assert result["success"] == False, "❌ Invalid port should fail validation"
    assert any("Port must be between" in err for err in result["errors"]), "❌ Should have port error"
    print("✅ Invalid port (80) fails validation correctly")
    
    # Test invalid port (too high)
    invalid_port_config["server_port"] = 70000
    result = manager.validate_config(invalid_port_config)
    assert result["success"] == False, "❌ Port 70000 should fail"
    print("✅ Port out of range (70000) fails validation correctly")
    
    # Test invalid thumbnail quality
    invalid_quality_config = valid_config.copy()
    invalid_quality_config["thumbnail_quality"] = 150
    
    result = manager.validate_config(invalid_quality_config)
    assert result["success"] == False, "❌ Quality 150 should fail"
    assert any("quality" in err.lower() for err in result["errors"]), "❌ Should have quality error"
    print("✅ Invalid thumbnail quality (150) fails validation correctly")
    
    # Test invalid upload size
    invalid_size_config = valid_config.copy()
    invalid_size_config["max_upload_size_mb"] = -10
    
    result = manager.validate_config(invalid_size_config)
    assert result["success"] == False, "❌ Negative upload size should fail"
    print("✅ Negative upload size fails validation correctly")
    
    # Test path validation with auto-detect disabled
    manual_path_config = valid_config.copy()
    manual_path_config["auto_detect_paths"] = False
    manual_path_config["base_output_path"] = "/definitely/nonexistent/path"
    
    result = manager.validate_config(manual_path_config)
    # Should succeed but have warnings
    assert result["success"] == True, "❌ Non-existent path should warn, not error"
    assert len(result["warnings"]) > 0, "❌ Should have warnings about non-existent path"
    print("✅ Non-existent path generates warning (not error)")
    
    # Cleanup
    if test_config_path.exists():
        test_config_path.unlink()
    
    return True

def test_config_save_and_load():
    """Test saving and loading configuration"""
    print_test_header("Configuration Save and Load")
    
    test_config_path = Path("test_config_temp.json")
    if test_config_path.exists():
        test_config_path.unlink()
    
    manager = GalleryConfigManager(str(test_config_path))
    
    # Create test configuration
    test_config = {
        "server_port": 8010,
        "base_output_path": "/test/output",
        "base_input_path": "/test/input",
        "auto_detect_paths": False,
        "enable_upload": True,
        "max_upload_size_mb": 150,
        "thumbnail_quality": 90,
        "ffprobe_manual_path": "/usr/bin/ffprobe"
    }
    
    # Save configuration
    result = manager.save_config(test_config)
    assert result["success"] == True, f"❌ Save should succeed: {result.get('errors')}"
    print("✅ Configuration saved successfully")
    
    # Verify file was created
    assert test_config_path.exists(), "❌ Config file should exist after save"
    print("✅ Config file created on disk")
    
    # Verify backup was created
    backup_path = test_config_path.with_suffix('.json.bak')
    # First save won't have backup
    
    # Load configuration again
    manager2 = GalleryConfigManager(str(test_config_path))
    assert manager2.config["server_port"] == 8010, "❌ Port should be loaded correctly"
    assert manager2.config["thumbnail_quality"] == 90, "❌ Quality should be loaded correctly"
    print("✅ Configuration loaded correctly from file")
    
    # Test backup creation on second save
    test_config["server_port"] = 8011
    result = manager2.save_config(test_config)
    assert result["success"] == True, "❌ Second save should succeed"
    
    # Now backup should exist
    assert backup_path.exists(), "❌ Backup should be created on second save"
    print("✅ Backup created on subsequent save")
    
    # Cleanup
    if test_config_path.exists():
        test_config_path.unlink()
    if backup_path.exists():
        backup_path.unlink()
    
    return True

def test_path_detection():
    """Test automatic path detection"""
    print_test_header("Path Detection")
    
    test_config_path = Path("test_config_temp.json")
    manager = GalleryConfigManager(str(test_config_path))
    
    # Get detected paths
    detected = manager.get_detected_paths()
    
    # Should return dict with output_path and input_path keys
    assert "output_path" in detected, "❌ Should have output_path key"
    assert "input_path" in detected, "❌ Should have input_path key"
    print(f"✅ Path detection returns expected structure")
    print(f"   Detected output: {detected['output_path']}")
    print(f"   Detected input: {detected['input_path']}")
    
    # Test effective config
    config_with_auto = {
        "auto_detect_paths": True,
        "base_output_path": "",
        "base_input_path": "",
        "server_port": 8008
    }
    
    manager.config = config_with_auto
    effective = manager.get_effective_config()
    
    # When auto-detect is enabled, effective config should use detected paths
    if detected["output_path"]:
        assert effective["base_output_path"] == detected["output_path"], \
            "❌ Effective config should use detected output path"
        print("✅ Effective config uses auto-detected output path")
    
    # Test with manual paths
    config_manual = {
        "auto_detect_paths": False,
        "base_output_path": "/manual/output",
        "base_input_path": "/manual/input",
        "server_port": 8008
    }
    
    manager.config = config_manual
    effective2 = manager.get_effective_config()
    
    assert effective2["base_output_path"] == "/manual/output", \
        "❌ Effective config should use manual path when auto-detect disabled"
    print("✅ Effective config uses manual paths when auto-detect is off")
    
    # Cleanup
    if test_config_path.exists():
        test_config_path.unlink()
    
    return True

def test_edge_cases():
    """Test edge cases and error handling"""
    print_test_header("Edge Cases and Error Handling")
    
    test_config_path = Path("test_config_temp.json")
    manager = GalleryConfigManager(str(test_config_path))
    
    # Test with string port (should convert)
    config_string_port = {
        "server_port": "8008",
        "auto_detect_paths": True,
        "enable_upload": True,
        "max_upload_size_mb": 100,
        "thumbnail_quality": 85
    }
    
    result = manager.validate_config(config_string_port)
    assert result["success"] == True, "❌ Should convert string port to int"
    assert config_string_port["server_port"] == 8008, "❌ Port should be converted to int"
    print("✅ String port converted to integer during validation")
    
    # Test with missing keys (should use defaults)
    incomplete_config = {
        "server_port": 8008
    }
    
    result = manager.validate_config(incomplete_config)
    # Validation doesn't add missing keys, that happens during merge
    print("✅ Incomplete config handled gracefully")
    
    # Test type conversions for quality
    config_string_quality = {
        "server_port": 8008,
        "thumbnail_quality": "85",
        "auto_detect_paths": True,
        "enable_upload": True,
        "max_upload_size_mb": 100
    }
    
    result = manager.validate_config(config_string_quality)
    assert result["success"] == True, "❌ Should convert string quality to int"
    print("✅ String thumbnail quality converted to integer")
    
    # Test corrupted config file
    with open(test_config_path, 'w') as f:
        f.write("{ invalid json }")
    
    manager_bad = GalleryConfigManager(str(test_config_path))
    # Should fall back to defaults
    assert manager_bad.config["server_port"] == 8008, "❌ Should use defaults on corrupted file"
    print("✅ Corrupted config file falls back to defaults")
    
    # Cleanup
    if test_config_path.exists():
        test_config_path.unlink()
    
    return True

def run_all_tests():
    """Run all test suites"""
    print("\n" + "="*60)
    print("SMARTGALLERY CONFIGURATION SYSTEM TEST SUITE")
    print("="*60)
    
    tests = [
        ("Initialization", test_config_manager_initialization),
        ("Validation", test_config_validation),
        ("Save & Load", test_config_save_and_load),
        ("Path Detection", test_path_detection),
        ("Edge Cases", test_edge_cases)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {test_name} TEST FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} TEST FAILED WITH EXCEPTION:")
            print(f"   {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Configuration system is working correctly.")
        return 0
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
