#!/usr/bin/env python3
"""
CSS Performance Optimization Script for Istanbul Plus

This script handles:
1. CSS minification and compression
2. Critical CSS extraction
3. Unused CSS purging
4. Resource hints generation
"""

import os
import re
import sys
import json
import gzip
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Set
from urllib.parse import urljoin

# Add Django project to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'istanbulplusir.settings.dev')

import django
django.setup()

from django.conf import settings
from django.template.loader import get_template
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser


class CSSOptimizer:
    """CSS Performance Optimization Tool"""
    
    def __init__(self):
        self.base_dir = Path(settings.BASE_DIR)
        self.static_dir = self.base_dir / 'static'
        self.css_dir = self.static_dir / 'css'
        self.build_dir = self.static_dir / 'build'
        self.critical_css_file = self.build_dir / 'critical.css'
        
        # Ensure build directory exists
        self.build_dir.mkdir(exist_ok=True)
        
        # Critical CSS selectors (above-the-fold content)
        self.critical_selectors = [
            'html', 'body', ':root',
            '.modern-background', '.page-loader', '.loader-spinner',
            '.navbar', '.glass-nav', '.navbar-brand', '.navbar-toggler',
            '.container', '.row', '.col-*',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            '.btn', '.btn-primary', '.btn-secondary',
            '.alert', '.messages-container',
            '.hero-section', '.main-content',
            # Animation and transition classes
            '@keyframes', '.fade-in', '.fade-out', '.scroll-fade-up', '.scroll-fade-down',
            # Theme classes
            '[data-theme="light"]', '[data-theme="dark"]',
            '.theme-toggle', '.theme-icon-light', '.theme-icon-dark',
            # Accessibility classes
            '.visually-hidden', '.visually-hidden-focusable', '.sr-only',
            # Bootstrap critical classes
            '.d-none', '.d-block', '.d-flex', '.position-*', '.text-*', '.bg-*',
            '.m-*', '.p-*', '.mt-*', '.mb-*', '.ms-*', '.me-*', '.pt-*', '.pb-*', '.ps-*', '.pe-*'
        ]
        
        # Templates to analyze for used CSS
        self.templates_to_analyze = [
            'base.html',
            'home.html',
            'products/product_list.html',
            'products/product_detail.html',
            'cart/cart_detail.html',
            'users/login.html',
            'users/register.html'
        ]

    def minify_css(self, css_content: str) -> str:
        """Minify CSS content by removing whitespace and comments"""
        # Remove comments
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        
        # Remove unnecessary whitespace
        css_content = re.sub(r'\s+', ' ', css_content)
        css_content = re.sub(r';\s*}', '}', css_content)
        css_content = re.sub(r'{\s*', '{', css_content)
        css_content = re.sub(r'}\s*', '}', css_content)
        css_content = re.sub(r':\s*', ':', css_content)
        css_content = re.sub(r';\s*', ';', css_content)
        css_content = re.sub(r',\s*', ',', css_content)
        
        # Remove trailing semicolons before closing braces
        css_content = re.sub(r';+}', '}', css_content)
        
        return css_content.strip()

    def extract_critical_css(self) -> str:
        """Extract critical CSS for above-the-fold content"""
        critical_css = []
        
        # Read main CSS file
        main_css_path = self.css_dir / 'main.css'
        if not main_css_path.exists():
            print(f"Warning: {main_css_path} not found")
            return ""
        
        # Process each CSS file imported in main.css
        css_files = self._get_css_files_from_imports(main_css_path)
        
        for css_file in css_files:
            if css_file.exists():
                content = css_file.read_text(encoding='utf-8')
                critical_rules = self._extract_critical_rules(content)
                if critical_rules:
                    critical_css.append(f"/* From {css_file.name} */")
                    critical_css.append(critical_rules)
        
        return '\n'.join(critical_css)

    def _get_css_files_from_imports(self, main_css_path: Path) -> List[Path]:
        """Extract CSS file paths from @import statements"""
        css_files = []
        content = main_css_path.read_text(encoding='utf-8')
        
        # Find @import statements
        import_pattern = r"@import\s+url\(['\"]?\./(.*?)['\"]?\);"
        imports = re.findall(import_pattern, content)
        
        for import_path in imports:
            css_file = self.css_dir / import_path
            if css_file.exists():
                css_files.append(css_file)
        
        return css_files

    def _extract_critical_rules(self, css_content: str) -> str:
        """Extract CSS rules that match critical selectors"""
        critical_rules = []
        
        # Split CSS into rules
        rules = re.findall(r'([^{}]+)\s*{([^{}]*)}', css_content, re.MULTILINE | re.DOTALL)
        
        for selector, declarations in rules:
            selector = selector.strip()
            
            # Check if selector matches critical patterns
            if self._is_critical_selector(selector):
                critical_rules.append(f"{selector}{{{declarations}}}")
        
        # Also extract CSS variables and keyframes
        variables = re.findall(r':root\s*{[^}]*}', css_content, re.MULTILINE | re.DOTALL)
        keyframes = re.findall(r'@keyframes[^}]*{[^}]*}', css_content, re.MULTILINE | re.DOTALL)
        
        critical_rules.extend(variables)
        critical_rules.extend(keyframes)
        
        return '\n'.join(critical_rules)

    def _is_critical_selector(self, selector: str) -> bool:
        """Check if a CSS selector is critical for above-the-fold content"""
        for critical_pattern in self.critical_selectors:
            if critical_pattern in selector or selector.startswith(critical_pattern):
                return True
            
            # Handle wildcard patterns
            if '*' in critical_pattern:
                pattern = critical_pattern.replace('*', '.*')
                if re.match(pattern, selector):
                    return True
        
        return False

    def purge_unused_css(self) -> Dict[str, int]:
        """Remove unused CSS selectors based on template analysis"""
        used_classes = self._analyze_templates_for_classes()
        purge_stats = {}
        
        # Process each CSS file
        css_files = list(self.css_dir.rglob('*.css'))
        
        for css_file in css_files:
            if css_file.name.startswith('min.') or 'build' in str(css_file):
                continue
                
            original_content = css_file.read_text(encoding='utf-8')
            purged_content = self._purge_css_content(original_content, used_classes)
            
            # Calculate savings
            original_size = len(original_content)
            purged_size = len(purged_content)
            savings = original_size - purged_size
            
            purge_stats[css_file.name] = {
                'original_size': original_size,
                'purged_size': purged_size,
                'savings': savings,
                'savings_percent': (savings / original_size * 100) if original_size > 0 else 0
            }
            
            # Write purged version
            purged_file = self.build_dir / f"purged-{css_file.name}"
            purged_file.write_text(purged_content, encoding='utf-8')
        
        return purge_stats

    def _analyze_templates_for_classes(self) -> Set[str]:
        """Analyze Django templates to find used CSS classes"""
        used_classes = set()
        
        # Add always-used classes
        used_classes.update([
            'container', 'row', 'col', 'btn', 'navbar', 'footer',
            'd-none', 'd-block', 'd-flex', 'text-center', 'text-end',
            'mt-3', 'mb-3', 'p-3', 'mx-auto', 'w-100', 'h-100'
        ])
        
        # Analyze template files
        template_dir = Path(settings.BASE_DIR) / 'templates'
        
        for template_name in self.templates_to_analyze:
            template_path = template_dir / template_name
            if template_path.exists():
                content = template_path.read_text(encoding='utf-8')
                classes = self._extract_classes_from_template(content)
                used_classes.update(classes)
        
        return used_classes

    def _extract_classes_from_template(self, template_content: str) -> Set[str]:
        """Extract CSS classes from template content"""
        classes = set()
        
        # Find class attributes
        class_patterns = [
            r'class=["\']([^"\']*)["\']',
            r'class:\s*["\']([^"\']*)["\']',  # Vue.js style
        ]
        
        for pattern in class_patterns:
            matches = re.findall(pattern, template_content, re.IGNORECASE)
            for match in matches:
                # Split multiple classes
                class_list = match.split()
                classes.update(class_list)
        
        return classes

    def _purge_css_content(self, css_content: str, used_classes: Set[str]) -> str:
        """Remove unused CSS rules from content"""
        # Keep CSS variables, keyframes, and media queries
        preserved_rules = []
        
        # Extract and preserve important rules
        preserved_patterns = [
            r':root\s*{[^}]*}',  # CSS variables
            r'@keyframes[^{]*{[^}]*}',  # Keyframes
            r'@media[^{]*{[^}]*}',  # Media queries
            r'@supports[^{]*{[^}]*}',  # Feature queries
        ]
        
        for pattern in preserved_patterns:
            matches = re.findall(pattern, css_content, re.MULTILINE | re.DOTALL)
            preserved_rules.extend(matches)
        
        # Process regular CSS rules
        rules = re.findall(r'([^{}]+)\s*{([^{}]*)}', css_content, re.MULTILINE | re.DOTALL)
        kept_rules = []
        
        for selector, declarations in rules:
            selector = selector.strip()
            
            # Keep rule if selector contains used classes or is a pseudo-selector
            if self._should_keep_rule(selector, used_classes):
                kept_rules.append(f"{selector}{{{declarations}}}")
        
        # Combine preserved and kept rules
        all_rules = preserved_rules + kept_rules
        return '\n'.join(all_rules)

    def _should_keep_rule(self, selector: str, used_classes: Set[str]) -> bool:
        """Determine if a CSS rule should be kept"""
        # Always keep element selectors, pseudo-selectors, and attribute selectors
        if (selector.startswith(('::', ':', '[')) or 
            selector in ['html', 'body', '*'] or
            any(tag in selector for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'img', 'div', 'span'])):
            return True
        
        # Check if selector contains any used classes
        for class_name in used_classes:
            if f'.{class_name}' in selector:
                return True
        
        return False

    def compress_css_files(self) -> Dict[str, Dict]:
        """Create minified and gzipped versions of CSS files"""
        compression_stats = {}
        
        css_files = list(self.css_dir.rglob('*.css'))
        
        for css_file in css_files:
            if css_file.name.startswith('min.') or 'build' in str(css_file):
                continue
            
            original_content = css_file.read_text(encoding='utf-8')
            minified_content = self.minify_css(original_content)
            
            # Create minified file
            min_file = css_file.parent / f"{css_file.stem}.min.css"
            min_file.write_text(minified_content, encoding='utf-8')
            
            # Create gzipped version
            gz_file = css_file.parent / f"{css_file.stem}.min.css.gz"
            with gzip.open(gz_file, 'wt', encoding='utf-8') as f:
                f.write(minified_content)
            
            # Calculate compression stats
            original_size = len(original_content.encode('utf-8'))
            minified_size = len(minified_content.encode('utf-8'))
            gzipped_size = gz_file.stat().st_size
            
            compression_stats[css_file.name] = {
                'original_size': original_size,
                'minified_size': minified_size,
                'gzipped_size': gzipped_size,
                'minification_savings': original_size - minified_size,
                'gzip_savings': original_size - gzipped_size,
                'total_savings_percent': ((original_size - gzipped_size) / original_size * 100) if original_size > 0 else 0
            }
        
        return compression_stats

    def generate_resource_hints(self) -> str:
        """Generate resource hints for better performance"""
        hints = []
        
        # DNS prefetch for external resources
        external_domains = [
            'cdn.jsdelivr.net',
            'cdnjs.cloudflare.com',
            'fonts.googleapis.com',
            'fonts.gstatic.com'
        ]
        
        for domain in external_domains:
            hints.append(f'<link rel="dns-prefetch" href="//{domain}">')
        
        # Preconnect for critical external resources
        critical_domains = [
            'fonts.googleapis.com',
            'fonts.gstatic.com'
        ]
        
        for domain in critical_domains:
            hints.append(f'<link rel="preconnect" href="https://{domain}">')
            if domain == 'fonts.gstatic.com':
                hints.append(f'<link rel="preconnect" href="https://{domain}" crossorigin>')
        
        # Preload critical CSS
        hints.append('<link rel="preload" href="{% static \'css/critical.min.css\' %}" as="style" onload="this.onload=null;this.rel=\'stylesheet\'">')
        
        # Preload critical fonts
        hints.append('<link rel="preload" href="{% static \'fonts/inter-var.woff2\' %}" as="font" type="font/woff2" crossorigin>')
        hints.append('<link rel="preload" href="{% static \'fonts/vazir-var.woff2\' %}" as="font" type="font/woff2" crossorigin>')
        
        return '\n    '.join(hints)

    def create_critical_css_file(self):
        """Create the critical CSS file"""
        critical_css = self.extract_critical_css()
        
        if critical_css:
            # Minify critical CSS
            minified_critical = self.minify_css(critical_css)
            
            # Write critical CSS file
            self.critical_css_file.write_text(minified_critical, encoding='utf-8')
            
            # Create gzipped version
            gz_file = self.build_dir / 'critical.min.css.gz'
            with gzip.open(gz_file, 'wt', encoding='utf-8') as f:
                f.write(minified_critical)
            
            print(f"✅ Critical CSS created: {self.critical_css_file}")
            print(f"   Size: {len(minified_critical)} bytes")
        else:
            print("❌ No critical CSS extracted")

    def optimize_all(self):
        """Run all optimization tasks"""
        print("🚀 Starting CSS Performance Optimization...")
        print("=" * 50)
        
        # 1. Create critical CSS
        print("\n1. Extracting Critical CSS...")
        self.create_critical_css_file()
        
        # 2. Compress CSS files
        print("\n2. Compressing CSS Files...")
        compression_stats = self.compress_css_files()
        
        total_original = sum(stats['original_size'] for stats in compression_stats.values())
        total_gzipped = sum(stats['gzipped_size'] for stats in compression_stats.values())
        total_savings = total_original - total_gzipped
        
        print(f"   📊 Compression Results:")
        print(f"   Original size: {total_original:,} bytes")
        print(f"   Gzipped size: {total_gzipped:,} bytes")
        print(f"   Total savings: {total_savings:,} bytes ({total_savings/total_original*100:.1f}%)")
        
        # 3. Purge unused CSS
        print("\n3. Purging Unused CSS...")
        purge_stats = self.purge_unused_css()
        
        total_purge_savings = sum(stats['savings'] for stats in purge_stats.values())
        print(f"   📊 Purge Results:")
        print(f"   Total CSS savings: {total_purge_savings:,} bytes")
        
        # 4. Generate resource hints
        print("\n4. Generating Resource Hints...")
        hints = self.generate_resource_hints()
        hints_file = self.build_dir / 'resource-hints.html'
        hints_file.write_text(hints, encoding='utf-8')
        print(f"   ✅ Resource hints saved to: {hints_file}")
        
        # 5. Create optimization report
        print("\n5. Creating Optimization Report...")
        self._create_optimization_report(compression_stats, purge_stats)
        
        print("\n🎉 CSS Optimization Complete!")
        print("=" * 50)

    def _create_optimization_report(self, compression_stats: Dict, purge_stats: Dict):
        """Create a detailed optimization report"""
        report = {
            'timestamp': str(Path(__file__).stat().st_mtime),
            'compression': compression_stats,
            'purging': purge_stats,
            'summary': {
                'total_files_processed': len(compression_stats),
                'total_compression_savings': sum(stats['gzipped_size'] for stats in compression_stats.values()),
                'total_purge_savings': sum(stats['savings'] for stats in purge_stats.values()),
                'critical_css_size': self.critical_css_file.stat().st_size if self.critical_css_file.exists() else 0
            }
        }
        
        report_file = self.build_dir / 'optimization-report.json'
        report_file.write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(f"   📋 Optimization report saved to: {report_file}")


if __name__ == '__main__':
    optimizer = CSSOptimizer()
    optimizer.optimize_all()