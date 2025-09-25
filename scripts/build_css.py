#!/usr/bin/env python3
"""
CSS Build Script for Production Deployment

This script creates optimized CSS bundles for production:
1. Combines CSS files into bundles
2. Processes CSS with PostCSS (autoprefixer, cssnano)
3. Creates critical CSS inline styles
4. Generates manifest for cache busting
"""

import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List

# Add Django project to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'istanbulplusir.settings.dev')

import django
django.setup()

from django.conf import settings


class CSSBuilder:
    """CSS Build System for Production"""
    
    def __init__(self):
        self.base_dir = Path(settings.BASE_DIR)
        self.static_dir = self.base_dir / 'static'
        self.css_dir = self.static_dir / 'css'
        self.build_dir = self.static_dir / 'build'
        self.dist_dir = self.build_dir / 'dist'
        
        # Ensure directories exist
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)
        
        # CSS bundles configuration
        self.bundles = {
            'critical': {
                'files': [
                    'base/reset.css',
                    'base/variables.css',
                    'base/typography.css',
                    'components/base-template.css',
                    'components/navigation.css',
                    'utilities/accessibility.css'
                ],
                'inline': True,  # This bundle will be inlined
                'priority': 'critical'
            },
            'main': {
                'files': [
                    'themes/light.css',
                    'themes/dark.css',
                    'components/buttons.css',
                    'components/forms.css',
                    'components/cards.css',
                    'components/footer.css',
                    'layouts/grid.css',
                    'layouts/containers.css',
                    'utilities/spacing.css',
                    'utilities/colors.css',
                    'utilities/animations.css',
                    'utilities/helpers.css'
                ],
                'inline': False,
                'priority': 'high'
            },
            'pages': {
                'files': [
                    'layouts/home.css',
                    'legacy.css'
                ],
                'inline': False,
                'priority': 'low'
            }
        }

    def read_css_file(self, file_path: str) -> str:
        """Read CSS file content with error handling"""
        css_file = self.css_dir / file_path
        
        if not css_file.exists():
            print(f"⚠️  Warning: CSS file not found: {css_file}")
            return ""
        
        try:
            return css_file.read_text(encoding='utf-8')
        except Exception as e:
            print(f"❌ Error reading {css_file}: {e}")
            return ""

    def process_css_imports(self, css_content: str) -> str:
        """Process @import statements and inline imported CSS"""
        import re
        
        def replace_import(match):
            import_path = match.group(1)
            # Remove leading './' if present
            import_path = import_path.lstrip('./')
            imported_content = self.read_css_file(import_path)
            return imported_content
        
        # Process @import url('./path/to/file.css');
        import_pattern = r"@import\s+url\(['\"]?\./(.*?)['\"]?\);"
        processed_content = re.sub(import_pattern, replace_import, css_content)
        
        return processed_content

    def create_bundle(self, bundle_name: str, bundle_config: Dict) -> Dict:
        """Create a CSS bundle from multiple files"""
        print(f"📦 Creating bundle: {bundle_name}")
        
        bundle_content = []
        bundle_content.append(f"/* Bundle: {bundle_name} */")
        bundle_content.append(f"/* Generated: {Path(__file__).stat().st_mtime} */")
        
        for file_path in bundle_config['files']:
            css_content = self.read_css_file(file_path)
            if css_content:
                bundle_content.append(f"\n/* From: {file_path} */")
                # Process any @import statements
                processed_content = self.process_css_imports(css_content)
                bundle_content.append(processed_content)
        
        # Combine all content
        combined_content = '\n'.join(bundle_content)
        
        # Create bundle file
        bundle_file = self.build_dir / f"{bundle_name}.css"
        bundle_file.write_text(combined_content, encoding='utf-8')
        
        # Create hash for cache busting
        content_hash = hashlib.md5(combined_content.encode('utf-8')).hexdigest()[:8]
        
        return {
            'file': bundle_file,
            'content': combined_content,
            'hash': content_hash,
            'size': len(combined_content),
            'config': bundle_config
        }

    def minify_css(self, css_content: str) -> str:
        """Minify CSS content"""
        import re
        
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

    def add_autoprefixer(self, css_content: str) -> str:
        """Add vendor prefixes to CSS (simplified version)"""
        # This is a simplified autoprefixer - in production, use PostCSS
        prefixes = {
            'backdrop-filter': ['-webkit-backdrop-filter'],
            'user-select': ['-webkit-user-select', '-moz-user-select', '-ms-user-select'],
            'transform': ['-webkit-transform', '-moz-transform', '-ms-transform'],
            'transition': ['-webkit-transition', '-moz-transition', '-ms-transition'],
            'animation': ['-webkit-animation', '-moz-animation', '-ms-animation'],
            'box-shadow': ['-webkit-box-shadow', '-moz-box-shadow'],
            'border-radius': ['-webkit-border-radius', '-moz-border-radius'],
            'appearance': ['-webkit-appearance', '-moz-appearance'],
            'flex': ['-webkit-flex', '-ms-flex'],
            'display: flex': ['display: -webkit-flex', 'display: -ms-flexbox']
        }
        
        for property_name, vendor_prefixes in prefixes.items():
            if property_name in css_content:
                for prefix in vendor_prefixes:
                    if property_name == 'display: flex':
                        css_content = css_content.replace('display:flex', f'{prefix};display:flex')
                        css_content = css_content.replace('display: flex', f'{prefix};display: flex')
                    else:
                        css_content = css_content.replace(f'{property_name}:', f'{prefix}:{property_name.split(":")[0] if ":" in property_name else property_name}:')
        
        return css_content

    def create_production_bundles(self) -> Dict:
        """Create all production CSS bundles"""
        print("🏗️  Building CSS bundles for production...")
        
        bundles_info = {}
        
        for bundle_name, bundle_config in self.bundles.items():
            # Create bundle
            bundle_info = self.create_bundle(bundle_name, bundle_config)
            
            # Add vendor prefixes
            prefixed_content = self.add_autoprefixer(bundle_info['content'])
            
            # Minify CSS
            minified_content = self.minify_css(prefixed_content)
            
            # Create production file with hash
            prod_filename = f"{bundle_name}.{bundle_info['hash']}.min.css"
            prod_file = self.dist_dir / prod_filename
            prod_file.write_text(minified_content, encoding='utf-8')
            
            # Create gzipped version
            import gzip
            gz_file = self.dist_dir / f"{prod_filename}.gz"
            with gzip.open(gz_file, 'wt', encoding='utf-8') as f:
                f.write(minified_content)
            
            bundles_info[bundle_name] = {
                'original_file': str(bundle_info['file']),
                'production_file': str(prod_file),
                'gzipped_file': str(gz_file),
                'hash': bundle_info['hash'],
                'original_size': bundle_info['size'],
                'minified_size': len(minified_content),
                'gzipped_size': gz_file.stat().st_size,
                'config': bundle_config,
                'savings': {
                    'minification': bundle_info['size'] - len(minified_content),
                    'gzip': bundle_info['size'] - gz_file.stat().st_size
                }
            }
            
            print(f"   ✅ {bundle_name}: {bundle_info['size']:,} → {len(minified_content):,} → {gz_file.stat().st_size:,} bytes")
        
        return bundles_info

    def create_css_manifest(self, bundles_info: Dict):
        """Create CSS manifest for cache busting and loading"""
        manifest = {
            'version': '1.0.0',
            'timestamp': str(Path(__file__).stat().st_mtime),
            'bundles': {}
        }
        
        for bundle_name, bundle_info in bundles_info.items():
            manifest['bundles'][bundle_name] = {
                'file': f"build/dist/{Path(bundle_info['production_file']).name}",
                'hash': bundle_info['hash'],
                'size': bundle_info['minified_size'],
                'gzipped_size': bundle_info['gzipped_size'],
                'inline': bundle_info['config']['inline'],
                'priority': bundle_info['config']['priority']
            }
        
        # Save manifest
        manifest_file = self.build_dir / 'css-manifest.json'
        manifest_file.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        
        print(f"📋 CSS manifest created: {manifest_file}")
        return manifest

    def create_django_template_tags(self, manifest: Dict):
        """Create Django template tags for optimized CSS loading"""
        template_tags = []
        
        template_tags.append("{% load static %}")
        template_tags.append("<!-- Optimized CSS Loading -->")
        
        # Critical CSS (inline)
        critical_bundle = manifest['bundles'].get('critical')
        if critical_bundle and critical_bundle['inline']:
            template_tags.append("<!-- Critical CSS (Inline) -->")
            template_tags.append("<style>")
            template_tags.append("/* Critical CSS will be inlined here */")
            template_tags.append("{% include 'css/critical-inline.css' %}")
            template_tags.append("</style>")
        
        # Non-critical CSS (async loading)
        for bundle_name, bundle_info in manifest['bundles'].items():
            if not bundle_info['inline']:
                priority = bundle_info['priority']
                css_file = bundle_info['file']
                
                if priority == 'high':
                    template_tags.append(f"<!-- {bundle_name.title()} CSS (High Priority) -->")
                    template_tags.append(f'<link rel="preload" href="{{% static \'{css_file}\' %}}" as="style" onload="this.onload=null;this.rel=\'stylesheet\'">')
                    template_tags.append(f'<noscript><link rel="stylesheet" href="{{% static \'{css_file}\' %}}"></noscript>')
                else:
                    template_tags.append(f"<!-- {bundle_name.title()} CSS (Low Priority) -->")
                    template_tags.append(f'<link rel="prefetch" href="{{% static \'{css_file}\' %}}" as="style">')
                    template_tags.append(f'<link rel="stylesheet" href="{{% static \'{css_file}\' %}}" media="print" onload="this.media=\'all\'">')
        
        # Save template tags
        tags_file = self.build_dir / 'css-template-tags.html'
        tags_file.write_text('\n'.join(template_tags), encoding='utf-8')
        
        print(f"🏷️  Template tags created: {tags_file}")

    def create_critical_css_inline(self, bundles_info: Dict):
        """Create inline critical CSS template"""
        critical_bundle = bundles_info.get('critical')
        if not critical_bundle:
            return
        
        # Read the minified critical CSS
        critical_file = Path(critical_bundle['production_file'])
        if critical_file.exists():
            critical_content = critical_file.read_text(encoding='utf-8')
            
            # Create inline template
            inline_template = self.base_dir / 'templates' / 'css' / 'critical-inline.css'
            inline_template.parent.mkdir(exist_ok=True)
            inline_template.write_text(critical_content, encoding='utf-8')
            
            print(f"💉 Critical CSS inline template created: {inline_template}")

    def build_all(self):
        """Run complete CSS build process"""
        print("🚀 Starting CSS Build Process...")
        print("=" * 50)
        
        # 1. Create bundles
        bundles_info = self.create_production_bundles()
        
        # 2. Create manifest
        manifest = self.create_css_manifest(bundles_info)
        
        # 3. Create template tags
        self.create_django_template_tags(manifest)
        
        # 4. Create critical CSS inline template
        self.create_critical_css_inline(bundles_info)
        
        # 5. Print summary
        total_original = sum(info['original_size'] for info in bundles_info.values())
        total_minified = sum(info['minified_size'] for info in bundles_info.values())
        total_gzipped = sum(info['gzipped_size'] for info in bundles_info.values())
        
        print("\n📊 Build Summary:")
        print(f"   Original size: {total_original:,} bytes")
        print(f"   Minified size: {total_minified:,} bytes ({(total_original-total_minified)/total_original*100:.1f}% savings)")
        print(f"   Gzipped size: {total_gzipped:,} bytes ({(total_original-total_gzipped)/total_original*100:.1f}% total savings)")
        
        print("\n🎉 CSS Build Complete!")
        print("=" * 50)


if __name__ == '__main__':
    builder = CSSBuilder()
    builder.build_all()