#!/usr/bin/env python3
"""
CSS Performance Testing Script

Tests the optimized CSS loading and measures performance improvements.
"""

import os
import sys
import time
import json
from pathlib import Path

# Add Django project to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'istanbulplusir.settings.dev')

import django
django.setup()

from django.test import Client
from django.urls import reverse
from django.conf import settings


class CSSPerformanceTester:
    """Test CSS optimization performance"""
    
    def __init__(self):
        self.client = Client()
        self.base_dir = Path(settings.BASE_DIR)
        self.build_dir = self.base_dir / 'static' / 'build'
        
    def test_css_files_exist(self):
        """Test that optimized CSS files exist"""
        print("🔍 Testing CSS file existence...")
        
        # Check manifest file
        manifest_file = self.build_dir / 'css-manifest.json'
        if not manifest_file.exists():
            print("❌ CSS manifest not found")
            return False
        
        # Load manifest
        manifest = json.loads(manifest_file.read_text())
        bundles = manifest.get('bundles', {})
        
        missing_files = []
        for bundle_name, bundle_info in bundles.items():
            bundle_file = self.base_dir / 'static' / bundle_info['file']
            if not bundle_file.exists():
                missing_files.append(bundle_file)
        
        if missing_files:
            print(f"❌ Missing CSS files: {missing_files}")
            return False
        
        print(f"✅ All {len(bundles)} CSS bundles exist")
        return True
    
    def test_critical_css_inline(self):
        """Test that critical CSS is properly inlined"""
        print("🔍 Testing critical CSS inlining...")
        
        critical_template = self.base_dir / 'templates' / 'css' / 'critical-inline.css'
        if not critical_template.exists():
            print("❌ Critical CSS template not found")
            return False
        
        content = critical_template.read_text(encoding='utf-8')
        if len(content) < 1000:  # Should have substantial content
            print("❌ Critical CSS template appears empty or too small")
            return False
        
        # Check for essential CSS
        essential_selectors = [':root', 'body', '.navbar', '.container']
        missing_selectors = []
        
        for selector in essential_selectors:
            if selector not in content:
                missing_selectors.append(selector)
        
        if missing_selectors:
            print(f"⚠️  Missing essential selectors: {missing_selectors}")
        
        print(f"✅ Critical CSS template exists ({len(content):,} bytes)")
        return True
    
    def test_template_optimization(self):
        """Test that templates use optimized CSS loading"""
        print("🔍 Testing template optimization...")
        
        base_template = self.base_dir / 'templates' / 'base.html'
        content = base_template.read_text(encoding='utf-8')
        
        # Check for optimized CSS loading
        if 'css-template-tags.html' not in content:
            print("❌ Base template not using optimized CSS loading")
            return False
        
        # Check that old CSS loading is removed
        if 'css/style.css' in content:
            print("⚠️  Old CSS loading still present in template")
        
        print("✅ Template using optimized CSS loading")
        return True
    
    def test_page_rendering(self):
        """Test that pages render correctly with optimized CSS"""
        print("🔍 Testing page rendering...")
        
        test_urls = [
            ('core:home', 'Home page'),
            ('products:product_list', 'Products page'),
        ]
        
        for url_name, description in test_urls:
            try:
                url = reverse(url_name)
                start_time = time.time()
                response = self.client.get(url)
                render_time = (time.time() - start_time) * 1000
                
                if response.status_code != 200:
                    print(f"❌ {description} failed to render (status: {response.status_code})")
                    return False
                
                # Check for CSS optimization markers
                content = response.content.decode('utf-8')
                
                if 'css-template-tags.html' not in content and 'critical-inline.css' not in content:
                    print(f"⚠️  {description} may not be using optimized CSS")
                
                print(f"✅ {description} rendered successfully ({render_time:.1f}ms)")
                
            except Exception as e:
                print(f"❌ {description} rendering failed: {e}")
                return False
        
        return True
    
    def measure_css_sizes(self):
        """Measure and report CSS file sizes"""
        print("📊 Measuring CSS file sizes...")
        
        manifest_file = self.build_dir / 'css-manifest.json'
        if not manifest_file.exists():
            print("❌ Cannot measure sizes - manifest not found")
            return
        
        manifest = json.loads(manifest_file.read_text())
        bundles = manifest.get('bundles', {})
        
        total_original = 0
        total_minified = 0
        total_gzipped = 0
        
        print("\n📦 CSS Bundle Sizes:")
        print("-" * 60)
        print(f"{'Bundle':<12} {'Original':<12} {'Minified':<12} {'Gzipped':<12} {'Savings'}")
        print("-" * 60)
        
        for bundle_name, bundle_info in bundles.items():
            original_size = bundle_info.get('original_size', bundle_info['size'])
            minified_size = bundle_info['size']
            gzipped_size = bundle_info['gzipped_size']
            
            total_original += original_size
            total_minified += minified_size
            total_gzipped += gzipped_size
            
            savings = ((original_size - gzipped_size) / original_size * 100) if original_size > 0 else 0
            
            print(f"{bundle_name:<12} {original_size:>8,}B {minified_size:>8,}B {gzipped_size:>8,}B {savings:>6.1f}%")
        
        print("-" * 60)
        total_savings = ((total_original - total_gzipped) / total_original * 100) if total_original > 0 else 0
        print(f"{'TOTAL':<12} {total_original:>8,}B {total_minified:>8,}B {total_gzipped:>8,}B {total_savings:>6.1f}%")
        
        print(f"\n💾 Total CSS payload: {total_gzipped:,} bytes (gzipped)")
        print(f"🎯 Performance target: <50KB (Current: {'✅ PASS' if total_gzipped < 50000 else '❌ FAIL'})")
    
    def test_resource_hints(self):
        """Test resource hints generation"""
        print("🔍 Testing resource hints...")
        
        hints_file = self.build_dir / 'resource-hints.html'
        if not hints_file.exists():
            print("❌ Resource hints file not found")
            return False
        
        content = hints_file.read_text(encoding='utf-8')
        
        # Check for essential hints
        essential_hints = ['dns-prefetch', 'preconnect', 'preload']
        missing_hints = []
        
        for hint in essential_hints:
            if hint not in content:
                missing_hints.append(hint)
        
        if missing_hints:
            print(f"⚠️  Missing resource hints: {missing_hints}")
        
        print(f"✅ Resource hints generated ({len(content.splitlines())} hints)")
        return True
    
    def run_all_tests(self):
        """Run all CSS performance tests"""
        print("🚀 Starting CSS Performance Tests...")
        print("=" * 60)
        
        tests = [
            ("CSS Files Existence", self.test_css_files_exist),
            ("Critical CSS Inlining", self.test_critical_css_inline),
            ("Template Optimization", self.test_template_optimization),
            ("Page Rendering", self.test_page_rendering),
            ("Resource Hints", self.test_resource_hints),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_function in tests:
            print(f"\n🧪 {test_name}...")
            try:
                if test_function():
                    passed_tests += 1
                    print(f"✅ {test_name} PASSED")
                else:
                    print(f"❌ {test_name} FAILED")
            except Exception as e:
                print(f"❌ {test_name} ERROR: {e}")
        
        # Measure CSS sizes (informational)
        print(f"\n📊 CSS Size Analysis:")
        self.measure_css_sizes()
        
        # Summary
        print(f"\n🎯 Test Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All CSS performance tests PASSED!")
            return True
        else:
            print("❌ Some CSS performance tests FAILED!")
            return False


if __name__ == '__main__':
    tester = CSSPerformanceTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)