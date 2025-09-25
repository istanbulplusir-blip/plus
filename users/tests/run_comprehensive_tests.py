#!/usr/bin/env python
"""
Comprehensive test runner for the authentication system.
Runs all integration tests and generates detailed reports.
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'istanbulplusir.settings')

import django
django.setup()

from django.test.utils import get_runner
from django.conf import settings
from django.core.management import call_command


class ComprehensiveTestRunner:
    """Comprehensive test runner with detailed reporting"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
        # Test modules to run
        self.test_modules = [
            'users.tests.test_comprehensive_integration',
            'users.tests.test_advanced_security_scenarios',
            'users.tests.test_comprehensive_performance',
            'users.tests.test_integration',
            'users.tests.test_security_integration',
            'users.tests.test_performance',
            'users.tests.test_browser_compatibility',
            'users.tests.test_verification_integration',
            'users.tests.test_password_reset',
            'users.tests.test_security',
            'users.tests.test_services',
        ]
    
    def run_test_module(self, module_name):
        """Run a specific test module and capture results"""
        print(f"\n{'='*60}")
        print(f"Running {module_name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Run the test module
            result = subprocess.run([
                sys.executable, 'manage.py', 'test', module_name, '--verbosity=2'
            ], capture_output=True, text=True, cwd=project_root)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse results
            success = result.returncode == 0
            output = result.stdout
            errors = result.stderr
            
            # Extract test count from output
            test_count = self._extract_test_count(output)
            
            self.test_results[module_name] = {
                'success': success,
                'duration': duration,
                'test_count': test_count,
                'output': output,
                'errors': errors,
                'return_code': result.returncode
            }
            
            if success:
                print(f"✅ {module_name} - {test_count} tests passed in {duration:.2f}s")
            else:
                print(f"❌ {module_name} - Failed in {duration:.2f}s")
                if errors:
                    print(f"Errors: {errors[:500]}...")
            
            return success
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            self.test_results[module_name] = {
                'success': False,
                'duration': duration,
                'test_count': 0,
                'output': '',
                'errors': str(e),
                'return_code': -1
            }
            
            print(f"❌ {module_name} - Exception: {str(e)}")
            return False
    
    def _extract_test_count(self, output):
        """Extract test count from test output"""
        try:
            # Look for patterns like "Ran 25 tests"
            import re
            match = re.search(r'Ran (\d+) test', output)
            if match:
                return int(match.group(1))
        except:
            pass
        return 0
    
    def run_all_tests(self):
        """Run all test modules"""
        print("🚀 Starting Comprehensive Authentication System Tests")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Test modules: {len(self.test_modules)}")
        
        self.start_time = time.time()
        
        # Run each test module
        successful_modules = 0
        failed_modules = 0
        
        for module in self.test_modules:
            if self.run_test_module(module):
                successful_modules += 1
            else:
                failed_modules += 1
        
        self.end_time = time.time()
        
        # Generate summary report
        self.generate_summary_report(successful_modules, failed_modules)
        
        # Generate detailed report
        self.generate_detailed_report()
        
        return failed_modules == 0
    
    def generate_summary_report(self, successful_modules, failed_modules):
        """Generate summary report"""
        total_duration = self.end_time - self.start_time
        total_tests = sum(result['test_count'] for result in self.test_results.values())
        
        print(f"\n{'='*80}")
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total Duration: {total_duration:.2f} seconds")
        print(f"Total Test Modules: {len(self.test_modules)}")
        print(f"Successful Modules: {successful_modules}")
        print(f"Failed Modules: {failed_modules}")
        print(f"Total Tests Run: {total_tests}")
        print(f"Success Rate: {(successful_modules/len(self.test_modules)*100):.1f}%")
        
        print(f"\n📋 MODULE RESULTS:")
        print(f"{'Module':<50} {'Status':<10} {'Tests':<8} {'Duration':<10}")
        print(f"{'-'*80}")
        
        for module, result in self.test_results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            module_short = module.split('.')[-1]
            print(f"{module_short:<50} {status:<10} {result['test_count']:<8} {result['duration']:.2f}s")
        
        # Performance summary
        print(f"\n⚡ PERFORMANCE SUMMARY:")
        performance_modules = [
            'test_comprehensive_performance',
            'test_performance',
            'test_integration'
        ]
        
        for module_name in performance_modules:
            full_module = f'users.tests.{module_name}'
            if full_module in self.test_results:
                result = self.test_results[full_module]
                if result['success']:
                    print(f"  {module_name}: {result['test_count']} tests in {result['duration']:.2f}s")
        
        # Security summary
        print(f"\n🔒 SECURITY TEST SUMMARY:")
        security_modules = [
            'test_advanced_security_scenarios',
            'test_security_integration',
            'test_security'
        ]
        
        for module_name in security_modules:
            full_module = f'users.tests.{module_name}'
            if full_module in self.test_results:
                result = self.test_results[full_module]
                status = "✅ SECURE" if result['success'] else "⚠️  ISSUES"
                print(f"  {module_name}: {status}")
    
    def generate_detailed_report(self):
        """Generate detailed JSON report"""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'total_duration': self.end_time - self.start_time,
            'summary': {
                'total_modules': len(self.test_modules),
                'successful_modules': sum(1 for r in self.test_results.values() if r['success']),
                'failed_modules': sum(1 for r in self.test_results.values() if not r['success']),
                'total_tests': sum(r['test_count'] for r in self.test_results.values()),
            },
            'modules': {}
        }
        
        for module, result in self.test_results.items():
            report_data['modules'][module] = {
                'success': result['success'],
                'duration': result['duration'],
                'test_count': result['test_count'],
                'return_code': result['return_code'],
                'has_errors': bool(result['errors'])
            }
        
        # Save detailed report
        report_file = project_root / 'test_reports' / f'comprehensive_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Save failed test details
        failed_tests = {k: v for k, v in self.test_results.items() if not v['success']}
        if failed_tests:
            failed_report_file = project_root / 'test_reports' / f'failed_tests_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            
            failed_details = {}
            for module, result in failed_tests.items():
                failed_details[module] = {
                    'duration': result['duration'],
                    'return_code': result['return_code'],
                    'errors': result['errors'],
                    'output': result['output'][-1000:] if result['output'] else ''  # Last 1000 chars
                }
            
            with open(failed_report_file, 'w') as f:
                json.dump(failed_details, f, indent=2)
            
            print(f"❌ Failed test details saved to: {failed_report_file}")
    
    def run_specific_test_categories(self, categories):
        """Run specific categories of tests"""
        category_modules = {
            'integration': [
                'users.tests.test_comprehensive_integration',
                'users.tests.test_integration',
                'users.tests.test_verification_integration'
            ],
            'security': [
                'users.tests.test_advanced_security_scenarios',
                'users.tests.test_security_integration',
                'users.tests.test_security'
            ],
            'performance': [
                'users.tests.test_comprehensive_performance',
                'users.tests.test_performance'
            ],
            'compatibility': [
                'users.tests.test_browser_compatibility'
            ]
        }
        
        modules_to_run = []
        for category in categories:
            if category in category_modules:
                modules_to_run.extend(category_modules[category])
        
        if not modules_to_run:
            print(f"❌ No modules found for categories: {categories}")
            return False
        
        # Temporarily replace test modules
        original_modules = self.test_modules
        self.test_modules = list(set(modules_to_run))  # Remove duplicates
        
        try:
            return self.run_all_tests()
        finally:
            self.test_modules = original_modules


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run comprehensive authentication system tests')
    parser.add_argument('--categories', nargs='+', 
                       choices=['integration', 'security', 'performance', 'compatibility'],
                       help='Run specific test categories')
    parser.add_argument('--module', type=str,
                       help='Run a specific test module')
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner()
    
    if args.module:
        # Run specific module
        success = runner.run_test_module(args.module)
        sys.exit(0 if success else 1)
    elif args.categories:
        # Run specific categories
        success = runner.run_specific_test_categories(args.categories)
        sys.exit(0 if success else 1)
    else:
        # Run all tests
        success = runner.run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()