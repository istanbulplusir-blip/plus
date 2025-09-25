"""
Django management command for CSS optimization

Usage:
    python manage.py optimize_css
    python manage.py optimize_css --build-only
    python manage.py optimize_css --critical-only
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import sys
import os
from pathlib import Path


class Command(BaseCommand):
    help = 'Optimize CSS files for production deployment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--build-only',
            action='store_true',
            help='Only run CSS build process (bundles, minification)',
        )
        parser.add_argument(
            '--critical-only',
            action='store_true',
            help='Only extract and optimize critical CSS',
        )
        parser.add_argument(
            '--purge',
            action='store_true',
            help='Enable CSS purging (remove unused styles)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting CSS Optimization...')
        )

        # Add scripts directory to Python path
        scripts_dir = Path(settings.BASE_DIR) / 'scripts'
        sys.path.insert(0, str(scripts_dir))

        try:
            if options['build_only']:
                self.run_build_only()
            elif options['critical_only']:
                self.run_critical_only()
            else:
                self.run_full_optimization(options)

        except ImportError as e:
            raise CommandError(f'Failed to import optimization modules: {e}')
        except Exception as e:
            raise CommandError(f'CSS optimization failed: {e}')

        self.stdout.write(
            self.style.SUCCESS('✅ CSS Optimization completed successfully!')
        )

    def run_build_only(self):
        """Run only CSS build process"""
        self.stdout.write('📦 Running CSS build process...')
        
        try:
            from build_css import CSSBuilder
            builder = CSSBuilder()
            builder.build_all()
        except Exception as e:
            raise CommandError(f'CSS build failed: {e}')

    def run_critical_only(self):
        """Run only critical CSS extraction"""
        self.stdout.write('⚡ Extracting critical CSS...')
        
        try:
            from css_optimizer import CSSOptimizer
            optimizer = CSSOptimizer()
            optimizer.create_critical_css_file()
        except Exception as e:
            raise CommandError(f'Critical CSS extraction failed: {e}')

    def run_full_optimization(self, options):
        """Run complete CSS optimization"""
        self.stdout.write('🔧 Running full CSS optimization...')
        
        # Step 1: Build CSS bundles
        self.stdout.write('1️⃣  Building CSS bundles...')
        try:
            from build_css import CSSBuilder
            builder = CSSBuilder()
            builder.build_all()
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'CSS build warning: {e}')
            )

        # Step 2: Run CSS optimization
        self.stdout.write('2️⃣  Optimizing CSS files...')
        try:
            from css_optimizer import CSSOptimizer
            optimizer = CSSOptimizer()
            
            if options['purge']:
                self.stdout.write('   🧹 Purging unused CSS...')
                optimizer.purge_unused_css()
            
            optimizer.optimize_all()
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'CSS optimization warning: {e}')
            )

        # Step 3: Update templates with optimized CSS loading
        self.stdout.write('3️⃣  Updating templates...')
        self.update_base_template()

    def update_base_template(self):
        """Update base template with optimized CSS loading"""
        base_template_path = Path(settings.BASE_DIR) / 'templates' / 'base.html'
        
        if not base_template_path.exists():
            self.stdout.write(
                self.style.WARNING('Base template not found, skipping template update')
            )
            return

        try:
            # Read current template
            content = base_template_path.read_text(encoding='utf-8')
            
            # Check if already optimized
            if 'css-template-tags.html' in content:
                self.stdout.write('   ✅ Template already optimized')
                return

            # Create backup
            backup_path = base_template_path.with_suffix('.html.backup')
            backup_path.write_text(content, encoding='utf-8')
            
            # Add optimized CSS loading
            css_loading_comment = '<!-- Main CSS -->'
            if css_loading_comment in content:
                # Replace existing CSS loading with optimized version
                optimized_css = '''<!-- Optimized CSS Loading -->
    {% include "css/css-template-tags.html" %}'''
                
                content = content.replace(
                    css_loading_comment + '\n    <link rel="stylesheet" href="{% static \'css/style.css\' %}" />',
                    optimized_css
                )
                
                # Write updated template
                base_template_path.write_text(content, encoding='utf-8')
                
                self.stdout.write('   ✅ Base template updated with optimized CSS loading')
            else:
                self.stdout.write(
                    self.style.WARNING('   ⚠️  Could not find CSS loading section in template')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Failed to update template: {e}')
            )

    def create_optimization_summary(self):
        """Create and display optimization summary"""
        build_dir = Path(settings.BASE_DIR) / 'static' / 'build'
        
        # Check for optimization report
        report_file = build_dir / 'optimization-report.json'
        if report_file.exists():
            import json
            try:
                report = json.loads(report_file.read_text())
                summary = report.get('summary', {})
                
                self.stdout.write('\n📊 Optimization Summary:')
                self.stdout.write(f"   Files processed: {summary.get('total_files_processed', 0)}")
                self.stdout.write(f"   Compression savings: {summary.get('total_compression_savings', 0):,} bytes")
                self.stdout.write(f"   Purge savings: {summary.get('total_purge_savings', 0):,} bytes")
                self.stdout.write(f"   Critical CSS size: {summary.get('critical_css_size', 0):,} bytes")
                
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Could not read optimization report: {e}')
                )

        # Check for CSS manifest
        manifest_file = build_dir / 'css-manifest.json'
        if manifest_file.exists():
            import json
            try:
                manifest = json.loads(manifest_file.read_text())
                bundles = manifest.get('bundles', {})
                
                self.stdout.write('\n📦 CSS Bundles:')
                for bundle_name, bundle_info in bundles.items():
                    size = bundle_info.get('size', 0)
                    gzipped_size = bundle_info.get('gzipped_size', 0)
                    savings = ((size - gzipped_size) / size * 100) if size > 0 else 0
                    
                    self.stdout.write(f"   {bundle_name}: {size:,} → {gzipped_size:,} bytes ({savings:.1f}% savings)")
                
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Could not read CSS manifest: {e}')
                )