"""
Django management command to validate template syntax and structure.

This command checks for common template issues:
- Unclosed template tags
- Malformed template syntax
- Missing template blocks
- Inconsistent indentation
- Best practice violations
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from django.core.management.base import BaseCommand, CommandError
from django.template import Template, TemplateSyntaxError
from django.template.loader import get_template
from django.conf import settings


class TemplateValidator:
    """Validates Django templates for syntax and best practices."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.template_dirs = self._get_template_dirs()
        
    def _get_template_dirs(self) -> List[Path]:
        """Get all template directories from Django settings."""
        template_dirs = []
        
        # Add TEMPLATES setting directories
        for template_config in settings.TEMPLATES:
            if 'DIRS' in template_config:
                for template_dir in template_config['DIRS']:
                    template_dirs.append(Path(template_dir))
        
        # Add app template directories
        for app_config in settings.INSTALLED_APPS:
            app_path = Path(app_config.replace('.', '/'))
            if app_path.exists():
                templates_path = app_path / 'templates'
                if templates_path.exists():
                    template_dirs.append(templates_path)
        
        return template_dirs
    
    def validate_all_templates(self) -> Dict[str, List[str]]:
        """Validate all templates in the project."""
        results = {'errors': [], 'warnings': []}
        
        for template_dir in self.template_dirs:
            if template_dir.exists():
                for template_file in template_dir.rglob('*.html'):
                    file_errors, file_warnings = self.validate_template_file(template_file)
                    results['errors'].extend(file_errors)
                    results['warnings'].extend(file_warnings)
        
        return results
    
    def validate_template_file(self, template_path: Path) -> Tuple[List[str], List[str]]:
        """Validate a single template file."""
        errors = []
        warnings = []
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for syntax errors
            try:
                Template(content)
            except TemplateSyntaxError as e:
                errors.append(f"{template_path}: {str(e)}")
            
            # Check for common issues
            file_errors, file_warnings = self._check_template_issues(content, template_path)
            errors.extend(file_errors)
            warnings.extend(file_warnings)
            
        except Exception as e:
            errors.append(f"{template_path}: Error reading file - {str(e)}")
        
        return errors, warnings
    
    def _check_template_issues(self, content: str, template_path: Path) -> Tuple[List[str], List[str]]:
        """Check for common template issues."""
        errors = []
        warnings = []
        lines = content.split('\n')
        
        # Check for unclosed tags
        unclosed_errors = self._check_unclosed_tags(content, template_path)
        errors.extend(unclosed_errors)
        
        # Check for malformed template tags
        malformed_errors = self._check_malformed_tags(content, template_path)
        errors.extend(malformed_errors)
        
        # Check for best practices
        best_practice_warnings = self._check_best_practices(content, template_path)
        warnings.extend(best_practice_warnings)
        
        # Check for inconsistent indentation
        indentation_warnings = self._check_indentation(lines, template_path)
        warnings.extend(indentation_warnings)
        
        return errors, warnings
    
    def _check_unclosed_tags(self, content: str, template_path: Path) -> List[str]:
        """Check for unclosed template tags."""
        errors = []
        
        # Tags that need closing
        opening_tags = ['if', 'for', 'with', 'block', 'comment', 'verbatim']
        closing_tags = ['endif', 'endfor', 'endwith', 'endblock', 'endcomment', 'endverbatim']
        
        for i, opening_tag in enumerate(opening_tags):
            closing_tag = closing_tags[i]
            
            # Count opening and closing tags
            opening_count = len(re.findall(rf'{{\%\s*{opening_tag}\b', content))
            closing_count = len(re.findall(rf'{{\%\s*{closing_tag}\b', content))
            
            if opening_count != closing_count:
                errors.append(
                    f"{template_path}: Unclosed '{opening_tag}' tags. "
                    f"Found {opening_count} opening and {closing_count} closing tags."
                )
        
        return errors
    
    def _check_malformed_tags(self, content: str, template_path: Path) -> List[str]:
        """Check for malformed template tags."""
        errors = []
        
        # Check for template tags split across lines incorrectly
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            # Check for template tags that start but don't end on the same line
            if re.search(r'{%\s*(if|for|with|block|comment|verbatim)\b[^%]*$', line):
                # Check if the next line continues the tag
                if line_num < len(lines):
                    next_line = lines[line_num]
                    if not re.search(r'%}', next_line):
                        errors.append(
                            f"{template_path}:{line_num}: Template tag split across lines incorrectly"
                        )
        
        return errors
    
    def _check_best_practices(self, content: str, template_path: Path) -> List[str]:
        """Check for template best practices."""
        warnings = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Check for hardcoded URLs
            if re.search(r'href="(?!{%|#|mailto:|tel:)[^"]*"', line):
                warnings.append(
                    f"{template_path}:{line_num}: Consider using {{% url %}} tag instead of hardcoded URL"
                )
            
            # Check for missing static tag usage
            if re.search(r'src="(?!{%|#|http)[^"]*\.(css|js|png|jpg|jpeg|gif|svg)"', line):
                warnings.append(
                    f"{template_path}:{line_num}: Consider using {{% static %}} tag for static files"
                )
            
            # Check for long lines
            if len(line) > 120:
                warnings.append(
                    f"{template_path}:{line_num}: Line is too long ({len(line)} characters)"
                )
        
        return warnings
    
    def _check_indentation(self, lines: List[str], template_path: Path) -> List[str]:
        """Check for inconsistent indentation."""
        warnings = []
        
        # Check for mixed tabs and spaces
        has_tabs = any('\t' in line for line in lines)
        has_spaces = any(line.startswith(' ') for line in lines)
        
        if has_tabs and has_spaces:
            warnings.append(f"{template_path}: Mixed tabs and spaces in indentation")
        
        return warnings


class Command(BaseCommand):
    help = 'Validate Django templates for syntax and best practices'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--template',
            type=str,
            help='Validate a specific template file'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix common template issues'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )
    
    def handle(self, *args, **options):
        validator = TemplateValidator()
        
        if options['template']:
            # Validate specific template
            template_path = Path(options['template'])
            if not template_path.exists():
                raise CommandError(f"Template file not found: {template_path}")
            
            errors, warnings = validator.validate_template_file(template_path)
        else:
            # Validate all templates
            results = validator.validate_all_templates()
            errors = results['errors']
            warnings = results['warnings']
        
        # Display results
        if errors:
            self.stdout.write(
                self.style.ERROR(f"\nFound {len(errors)} errors:")
            )
            for error in errors:
                self.stdout.write(self.style.ERROR(f"  {error}"))
        
        if warnings:
            self.stdout.write(
                self.style.WARNING(f"\nFound {len(warnings)} warnings:")
            )
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f"  {warning}"))
        
        if not errors and not warnings:
            self.stdout.write(
                self.style.SUCCESS("All templates are valid!")
            )
        
        # Summary
        total_issues = len(errors) + len(warnings)
        if total_issues > 0:
            self.stdout.write(
                f"\nTotal issues found: {total_issues} "
                f"({len(errors)} errors, {len(warnings)} warnings)"
            )
            
            if options['fix']:
                self.stdout.write(
                    self.style.WARNING("\nNote: Automatic fixing is not implemented yet.")
                )
