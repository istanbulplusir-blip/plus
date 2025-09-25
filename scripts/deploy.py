#!/usr/bin/env python3
"""
Production Deployment Script with CSS Optimization

This script handles the complete deployment process including:
1. CSS optimization and bundling
2. Static files collection
3. Database migrations
4. Cache warming
5. Performance validation
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Add Django project to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'istanbulplusir.settings.dev')

import django
django.setup()

from django.core.management import call_command
from django.conf import settings


class DeploymentManager:
    """Production Deployment Manager"""
    
    def __init__(self):
        self.base_dir = Path(settings.BASE_DIR)
        self.start_time = time.time()
        
    def log(self, message: str, level: str = "INFO"):
        """Log deployment messages"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def run_command(self, command: str, description: str = None):
        """Run shell command with error handling"""
        if description:
            self.log(f"Running: {description}")
        
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout:
                self.log(f"Output: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {command}", "ERROR")
            self.log(f"Error: {e.stderr}", "ERROR")
            return False
    
    def optimize_css(self):
        """Run CSS optimization"""
        self.log("🎨 Starting CSS optimization...")
        
        try:
            # Run full CSS optimization with purging
            call_command('optimize_css', '--purge', verbosity=2)
            self.log("✅ CSS optimization completed")
            return True
        except Exception as e:
            self.log(f"❌ CSS optimization failed: {e}", "ERROR")
            return False
    
    def collect_static_files(self):
        """Collect static files"""
        self.log("📦 Collecting static files...")
        
        try:
            call_command('collectstatic', '--noinput', verbosity=2)
            self.log("✅ Static files collected")
            return True
        except Exception as e:
            self.log(f"❌ Static files collection failed: {e}", "ERROR")
            return False
    
    def run_migrations(self):
        """Run database migrations"""
        self.log("🗄️  Running database migrations...")
        
        try:
            call_command('migrate', verbosity=2)
            self.log("✅ Database migrations completed")
            return True
        except Exception as e:
            self.log(f"❌ Database migrations failed: {e}", "ERROR")
            return False
    
    def compress_static_files(self):
        """Compress static files with gzip"""
        self.log("🗜️  Compressing static files...")
        
        static_root = Path(settings.STATIC_ROOT)
        if not static_root.exists():
            self.log("Static root directory not found", "WARNING")
            return False
        
        # Find CSS and JS files to compress
        files_to_compress = []
        for ext in ['*.css', '*.js']:
            files_to_compress.extend(static_root.rglob(ext))
        
        compressed_count = 0
        for file_path in files_to_compress:
            if file_path.suffix == '.gz':
                continue  # Skip already compressed files
            
            try:
                # Create gzipped version
                import gzip
                with open(file_path, 'rb') as f_in:
                    with gzip.open(f"{file_path}.gz", 'wb') as f_out:
                        f_out.writelines(f_in)
                compressed_count += 1
            except Exception as e:
                self.log(f"Failed to compress {file_path}: {e}", "WARNING")
        
        self.log(f"✅ Compressed {compressed_count} static files")
        return True
    
    def validate_css_optimization(self):
        """Validate CSS optimization results"""
        self.log("🔍 Validating CSS optimization...")
        
        build_dir = self.base_dir / 'static' / 'build'
        
        # Check for required files
        required_files = [
            'css-manifest.json',
            'optimization-report.json',
            'dist/critical.min.css',
            'dist/main.min.css'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not (build_dir / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.log(f"❌ Missing optimization files: {missing_files}", "ERROR")
            return False
        
        # Check CSS manifest
        try:
            import json
            manifest_file = build_dir / 'css-manifest.json'
            manifest = json.loads(manifest_file.read_text())
            
            bundles = manifest.get('bundles', {})
            if not bundles:
                self.log("❌ No CSS bundles found in manifest", "ERROR")
                return False
            
            # Validate bundle files exist
            for bundle_name, bundle_info in bundles.items():
                bundle_file = self.base_dir / 'static' / bundle_info['file']
                if not bundle_file.exists():
                    self.log(f"❌ Bundle file not found: {bundle_file}", "ERROR")
                    return False
            
            self.log(f"✅ CSS optimization validated ({len(bundles)} bundles)")
            return True
            
        except Exception as e:
            self.log(f"❌ CSS validation failed: {e}", "ERROR")
            return False
    
    def warm_cache(self):
        """Warm up application cache"""
        self.log("🔥 Warming up cache...")
        
        try:
            # Warm up CSS cache
            from django.core.cache import cache
            
            # Cache CSS manifest
            build_dir = self.base_dir / 'static' / 'build'
            manifest_file = build_dir / 'css-manifest.json'
            
            if manifest_file.exists():
                import json
                manifest = json.loads(manifest_file.read_text())
                cache.set('css_manifest', manifest, timeout=86400)  # 24 hours
            
            self.log("✅ Cache warmed up")
            return True
            
        except Exception as e:
            self.log(f"❌ Cache warming failed: {e}", "ERROR")
            return False
    
    def create_deployment_report(self):
        """Create deployment report"""
        self.log("📋 Creating deployment report...")
        
        deployment_time = time.time() - self.start_time
        
        report = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'duration': f"{deployment_time:.2f} seconds",
            'django_version': django.get_version(),
            'python_version': sys.version,
            'settings_module': os.environ.get('DJANGO_SETTINGS_MODULE'),
            'static_root': str(settings.STATIC_ROOT),
            'css_optimization': getattr(settings, 'CSS_OPTIMIZATION', {}),
        }
        
        # Add CSS optimization stats
        build_dir = self.base_dir / 'static' / 'build'
        optimization_report = build_dir / 'optimization-report.json'
        
        if optimization_report.exists():
            try:
                import json
                css_stats = json.loads(optimization_report.read_text())
                report['css_optimization_stats'] = css_stats.get('summary', {})
            except Exception:
                pass
        
        # Save deployment report
        report_file = self.base_dir / 'deployment-report.json'
        import json
        report_file.write_text(json.dumps(report, indent=2), encoding='utf-8')
        
        self.log(f"✅ Deployment report saved: {report_file}")
        self.log(f"🎉 Deployment completed in {deployment_time:.2f} seconds")
    
    def deploy(self):
        """Run complete deployment process"""
        self.log("🚀 Starting production deployment...")
        self.log("=" * 60)
        
        steps = [
            ("CSS Optimization", self.optimize_css),
            ("Database Migrations", self.run_migrations),
            ("Static Files Collection", self.collect_static_files),
            ("Static Files Compression", self.compress_static_files),
            ("CSS Validation", self.validate_css_optimization),
            ("Cache Warming", self.warm_cache),
        ]
        
        failed_steps = []
        
        for step_name, step_function in steps:
            self.log(f"\n📋 Step: {step_name}")
            if not step_function():
                failed_steps.append(step_name)
                self.log(f"❌ Step failed: {step_name}", "ERROR")
            else:
                self.log(f"✅ Step completed: {step_name}")
        
        # Create deployment report
        self.create_deployment_report()
        
        if failed_steps:
            self.log(f"\n❌ Deployment completed with errors in: {', '.join(failed_steps)}", "ERROR")
            return False
        else:
            self.log("\n🎉 Deployment completed successfully!")
            return True


if __name__ == '__main__':
    deployment = DeploymentManager()
    success = deployment.deploy()
    sys.exit(0 if success else 1)