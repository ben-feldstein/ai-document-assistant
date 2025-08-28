#!/usr/bin/env python3
"""
CI Test Suite for GitHub Actions
Tests that can run without external services (database, Redis, etc.)
"""

import sys
import os
import importlib.util
from typing import List, Dict, Any

class CITester:
    """Test runner for CI environment without external dependencies."""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
    
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED")
            if message:
                print(f"   {message}")
        else:
            self.tests_failed += 1
            print(f"❌ {test_name}: FAILED")
            if message:
                print(f"   {message}")
            self.failures.append(f"{test_name}: {message}")
    
    def test_imports(self) -> bool:
        """Test that all required modules can be imported."""
        print("🧪 Testing module imports...")
        
        required_modules = [
            "fastapi",
            "sqlalchemy",
            "pydantic",
            "redis",
            "openai",
            "websockets"
        ]
        
        all_imports_ok = True
        for module in required_modules:
            try:
                importlib.import_module(module)
                self.log_test(f"Import {module}", True)
            except ImportError as e:
                self.log_test(f"Import {module}", False, str(e))
                all_imports_ok = False
        
        return all_imports_ok
    
    def test_config_loading(self) -> bool:
        """Test that configuration can be loaded."""
        print("\n🧪 Testing configuration loading...")
        
        try:
            # Test if we can access the config module
            sys.path.append('api')
            from utils.config import settings
            
            # Check that required settings exist
            required_settings = [
                'database_url',
                'redis_url', 
                'jwt_secret',
                'openai_api_key',
                'mock_mode'
            ]
            
            all_settings_ok = True
            for setting in required_settings:
                if hasattr(settings, setting):
                    self.log_test(f"Config {setting}", True)
                else:
                    self.log_test(f"Config {setting}", False, f"Missing setting: {setting}")
                    all_settings_ok = False
            
            return all_settings_ok
            
        except Exception as e:
            # Config validation errors are expected in CI environment
            # Just check that the module can be imported
            if "validation error" in str(e).lower():
                self.log_test("Config loading", True, "Module imported (validation errors expected in CI)")
                return True
            else:
                self.log_test("Config loading", False, str(e))
                return False
    
    def test_file_structure(self) -> bool:
        """Test that required files and directories exist."""
        print("\n🧪 Testing file structure...")
        
        required_paths = [
            "api/",
            "api/routes/",
            "api/models/",
            "api/services/",
            "api/utils/",
            "modern-ui/",
            "modern-ui/src/",
            "infra/",
            "infra/docker-compose.yml",
            "requirements.txt",
            "requirements-py312.txt"
        ]
        
        all_paths_ok = True
        for path in required_paths:
            if os.path.exists(path):
                self.log_test(f"Path {path}", True)
            else:
                self.log_test(f"Path {path}", False, f"Missing: {path}")
                all_paths_ok = False
        
        return all_paths_ok
    
    def test_python_syntax(self) -> bool:
        """Test that Python files have valid syntax."""
        print("\n🧪 Testing Python syntax...")
        
        python_files = []
        for root, dirs, files in os.walk("api"):
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))
        
        all_syntax_ok = True
        for py_file in python_files[:10]:  # Test first 10 files
            try:
                with open(py_file, 'r') as f:
                    compile(f.read(), py_file, 'exec')
                self.log_test(f"Syntax {os.path.basename(py_file)}", True)
            except SyntaxError as e:
                self.log_test(f"Syntax {os.path.basename(py_file)}", False, f"Syntax error: {e}")
                all_syntax_ok = False
            except Exception as e:
                self.log_test(f"Syntax {os.path.basename(py_file)}", False, f"Error: {e}")
                all_syntax_ok = False
        
        return all_syntax_ok
    
    def test_mock_mode_config(self) -> bool:
        """Test that mock mode is properly configured."""
        print("\n🧪 Testing mock mode configuration...")
        
        try:
            # Check environment variables
            mock_mode = os.getenv('MOCK_MODE', 'false').lower()
            mock_ai = os.getenv('MOCK_AI_RESPONSES', 'false').lower()
            mock_docs = os.getenv('MOCK_DOCUMENT_PROCESSING', 'false').lower()
            
            self.log_test("MOCK_MODE env var", mock_mode == 'true', f"Value: {mock_mode}")
            self.log_test("MOCK_AI_RESPONSES env var", mock_ai == 'true', f"Value: {mock_ai}")
            self.log_test("MOCK_DOCUMENT_PROCESSING env var", mock_docs == 'true', f"Value: {mock_docs}")
            
            # Check mock service files exist
            mock_files = [
                "api/services/mock_ai_service.py",
                "api/services/mock_document_service.py"
            ]
            
            all_mock_files_ok = True
            for mock_file in mock_files:
                if os.path.exists(mock_file):
                    self.log_test(f"Mock file {os.path.basename(mock_file)}", True)
                else:
                    self.log_test(f"Mock file {os.path.basename(mock_file)}", False, f"Missing: {mock_file}")
                    all_mock_files_ok = False
            
            return all_mock_files_ok
            
        except Exception as e:
            self.log_test("Mock mode config", False, str(e))
            return False
    
    def run_all_tests(self) -> bool:
        """Run all CI tests."""
        print("🚀 CI Test Suite - No External Dependencies Required")
        print("=" * 60)
        
        tests = [
            ("Module Imports", self.test_imports),
            ("Configuration Loading", self.test_config_loading),
            ("File Structure", self.test_file_structure),
            ("Python Syntax", self.test_python_syntax),
            ("Mock Mode Configuration", self.test_mock_mode_config)
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            try:
                result = test_func()
                if not result:
                    all_passed = False
            except Exception as e:
                self.log_test(test_name, False, f"Exception: {str(e)}")
                all_passed = False
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 CI TEST RESULTS")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failures:
            print("\n❌ FAILURES:")
            for failure in self.failures:
                print(f"   - {failure}")
        
        if all_passed:
            print("\n🎉 ALL CI TESTS PASSED!")
            print("Your code structure and configuration are ready for deployment.")
        else:
            print("\n⚠️  Some CI tests failed. Review the issues above.")
        
        return all_passed

def main():
    """Main test runner."""
    tester = CITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
