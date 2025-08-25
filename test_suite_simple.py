#!/usr/bin/env python3
"""
Simple test suite for AI Voice Policy Assistant.
Tests all Python files for basic syntax and import errors.
"""

import sys
import os
import ast
from pathlib import Path
from typing import Dict

class SimpleFileTester:
    def __init__(self):
        self.results = {}
        self.errors = []
        
    def test_syntax(self, file_path: str) -> bool:
        """Test if a Python file has valid syntax."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            ast.parse(source)
            return True
        except SyntaxError as e:
            self.errors.append(f"Syntax error in {file_path}: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading {file_path}: {e}")
            return False
    
    def test_basic_imports(self, file_path: str) -> bool:
        """Test if a Python file has basic import issues."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Check for common import issues
            lines = source.split('\n')
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    # Basic syntax check for import statements
                    try:
                        ast.parse(line)
                    except SyntaxError as e:
                        self.errors.append(f"Import syntax error in {file_path}:{i}: {e}")
                        return False
            
            return True
        except Exception as e:
            self.errors.append(f"Error checking imports in {file_path}: {e}")
            return False
    
    def test_file(self, file_path: str) -> Dict[str, bool]:
        """Test a single Python file."""
        print(f"🔍 Testing {file_path}...")
        
        # Test syntax first
        syntax_ok = self.test_syntax(file_path)
        
        # Test basic imports if syntax is ok
        imports_ok = False
        if syntax_ok:
            imports_ok = self.test_basic_imports(file_path)
        
        result = {
            'syntax': syntax_ok,
            'imports': imports_ok,
            'overall': syntax_ok and imports_ok
        }
        
        status = "✅" if result['overall'] else "❌"
        print(f"   {status} Syntax: {'OK' if syntax_ok else 'FAIL'}")
        print(f"   {status} Imports: {'OK' if imports_ok else 'FAIL'}")
        
        return result
    
    def run_tests(self) -> Dict[str, Dict[str, bool]]:
        """Run tests on all Python files in the project."""
        print("🧪 Running simple test suite...")
        print("=" * 60)
        
        # Define all Python files to test
        python_files = [
            # Main application files
            'api/app.py',
            'worker/main.py',
            
            # Models
            'api/models/entities.py',
            'api/models/db.py',
            'api/models/schemas.py',
            
            # Routes
            'api/routes/auth.py',
            'api/routes/chat.py',
            'api/routes/corpus.py',
            'api/routes/admin.py',
            'api/routes/ws_audio.py',
            
            # Services
            'api/services/orchestrator.py',
            'api/services/stt.py',
            'api/services/llm.py',
            'api/services/vectorizer.py',
            'api/services/search.py',
            'api/services/rate_limit.py',
            'api/services/cache.py',
            
            # Utils
            'api/utils/config.py',
        ]
        
        # Test each file
        for file_path in python_files:
            if os.path.exists(file_path):
                self.results[file_path] = self.test_file(file_path)
                print()  # Empty line for readability
            else:
                print(f"⚠️  File not found: {file_path}")
                self.results[file_path] = {'syntax': False, 'imports': False, 'overall': False}
        
        return self.results
    
    def print_summary(self):
        """Print a summary of test results."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_files = len(self.results)
        syntax_ok = sum(1 for r in self.results.values() if r['syntax'])
        imports_ok = sum(1 for r in self.results.values() if r['imports'])
        overall_ok = sum(1 for r in self.results.values() if r['overall'])
        
        print(f"Total files tested: {total_files}")
        print(f"Syntax OK: {syntax_ok}/{total_files}")
        print(f"Imports OK: {imports_ok}/{total_files}")
        print(f"Overall OK: {overall_ok}/{total_files}")
        
        if self.errors:
            print(f"\n❌ ERRORS FOUND ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        else:
            print("\n🎉 All tests passed! No errors found.")
        
        print(f"\nOverall Status: {'✅ PASSED' if overall_ok == total_files else '❌ FAILED'}")

def main():
    """Run the test suite."""
    tester = SimpleFileTester()
    results = tester.run_tests()
    tester.print_summary()
    
    # Exit with appropriate code
    total_files = len(results)
    overall_ok = sum(1 for r in results.values() if r['overall'])
    
    if overall_ok == total_files:
        print("\n🎉 All files have valid syntax!")
        return True
    else:
        print(f"\n⚠️  {total_files - overall_ok} files have issues that need fixing.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
