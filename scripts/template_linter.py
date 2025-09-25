#!/usr/bin/env python3
"""
Advanced Django Template Linter

This script provides comprehensive template validation and linting for Django projects.
It checks for syntax errors, best practices, and provides suggestions for improvement.

Usage:
    python scripts/template_linter.py [options]
    python scripts/template_linter.py --file templates/components/navbar.html
    python scripts/template_linter.py --fix --verbose
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum


class IssueType(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class TemplateIssue:
    file_path: Path
    line_number: int
    column: int
    issue_type: IssueType
    message: str
    suggestion: Optional[str] = None
    code: Optional[str] = None


class DjangoTemplateLinter:
    """Advanced Django template linter with comprehensive checks."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues: List[TemplateIssue] = []
        self.template_dirs = self._find_template_dirs()
        
        # Template tag patterns
        self.template_tag_pattern = re.compile(r'{%\s*(\w+)(?:\s+([^%]+))?\s*%}')
        self.template_var_pattern = re.compile(r'{{\s*([^}]+)\s*}}')
        
        # Common template tags that need closing
        self.opening_tags = {
            'if': 'endif',
            'for': 'endfor', 
            'with': 'endwith',
            'block': 'endblock',
            'comment': 'endcomment',
            'verbatim': 'endverbatim',
            'filter': 'endfilter',
            'spaceless': 'endspaceless',
            'autoescape': 'endautoescape',
        }
    
    def _find_template_dirs(self) -> List[Path]:
        """Find all template directories in the project."""
        template_dirs = []
        
        # Look for templates directory in project root
        templates_dir = self.project_root / 'templates'
        if templates_dir.exists():
            template_dirs.append(templates_dir)
        
        # Look for templates in apps
        for item in self.project_root.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                app_templates = item / 'templates'
                if app_templates.exists():
                    template_dirs.append(app_templates)
        
        return template_dirs
    
    def lint_all_templates(self) -> List[TemplateIssue]:
        """Lint all templates in the project."""
        self.issues = []
        
        for template_dir in self.template_dirs:
            for template_file in template_dir.rglob('*.html'):
                self._lint_template_file(template_file)
        
        return self.issues
    
    def lint_template_file(self, file_path: Path) -> List[TemplateIssue]:
        """Lint a specific template file."""
        self.issues = []
        self._lint_template_file(file_path)
        return self.issues
    
    def _lint_template_file(self, file_path: Path):
        """Internal method to lint a template file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # Check for various issues
            self._check_syntax_errors(content, file_path)
            self._check_unclosed_tags(content, file_path)
            self._check_malformed_tags(lines, file_path)
            self._check_best_practices(lines, file_path)
            self._check_accessibility(lines, file_path)
            self._check_performance(lines, file_path)
            self._check_security(lines, file_path)
            self._check_consistency(lines, file_path)
            
        except Exception as e:
            self._add_issue(
                file_path, 1, 1, IssueType.ERROR,
                f"Error reading file: {str(e)}"
            )
    
    def _check_syntax_errors(self, content: str, file_path: Path):
        """Check for basic template syntax errors."""
        try:
            from django.template import Template
            Template(content)
        except Exception as e:
            # Try to extract line number from error
            line_match = re.search(r'line (\d+)', str(e))
            line_number = int(line_match.group(1)) if line_match else 1
            
            self._add_issue(
                file_path, line_number, 1, IssueType.ERROR,
                f"Template syntax error: {str(e)}"
            )
    
    def _check_unclosed_tags(self, content: str, file_path: Path):
        """Check for unclosed template tags."""
        for opening_tag, closing_tag in self.opening_tags.items():
            opening_count = len(re.findall(rf'{{\%\s*{opening_tag}\b', content))
            closing_count = len(re.findall(rf'{{\%\s*{closing_tag}\b', content))
            
            if opening_count != closing_count:
                self._add_issue(
                    file_path, 1, 1, IssueType.ERROR,
                    f"Unclosed '{opening_tag}' tags. Found {opening_count} opening and {closing_count} closing tags.",
                    f"Add {opening_count - closing_count} missing '{closing_tag}' tags"
                )
    
    def _check_malformed_tags(self, lines: List[str], file_path: Path):
        """Check for malformed template tags."""
        for line_num, line in enumerate(lines, 1):
            # Check for template tags split across lines incorrectly
            if re.search(r'{%\s*(if|for|with|block|comment|verbatim)\b[^%]*$', line):
                if line_num < len(lines):
                    next_line = lines[line_num]
                    if not re.search(r'%}', next_line):
                        self._add_issue(
                            file_path, line_num, 1, IssueType.ERROR,
                            "Template tag split across lines incorrectly",
                            "Keep template tags on single lines or use proper line continuation"
                        )
            
            # Check for incomplete template tags
            if re.search(r'{%[^%]*$', line) and not re.search(r'%}', line):
                self._add_issue(
                    file_path, line_num, 1, IssueType.ERROR,
                    "Incomplete template tag",
                    "Complete the template tag with %}"
                )
    
    def _check_best_practices(self, lines: List[str], file_path: Path):
        """Check for Django template best practices."""
        for line_num, line in enumerate(lines, 1):
            # Check for hardcoded URLs
            if re.search(r'href="(?!{%|#|mailto:|tel:|javascript:)[^"]*"', line):
                self._add_issue(
                    file_path, line_num, 1, IssueType.WARNING,
                    "Hardcoded URL found",
                    "Use {% url 'view_name' %} instead of hardcoded URLs"
                )
            
            # Check for missing static tag usage
            if re.search(r'src="(?!{%|#|http)[^"]*\.(css|js|png|jpg|jpeg|gif|svg|ico|woff|woff2)"', line):
                self._add_issue(
                    file_path, line_num, 1, IssueType.WARNING,
                    "Static file without {% static %} tag",
                    "Use {% static 'path/to/file' %} for static files"
                )
            
            # Check for long lines
            if len(line) > 120:
                self._add_issue(
                    file_path, line_num, 1, IssueType.INFO,
                    f"Line too long ({len(line)} characters)",
                    "Consider breaking long lines for better readability"
                )
            
            # Check for missing load static
            if re.search(r'{%\s*static\s+', line) and '{% load static %}' not in '\n'.join(lines[:line_num]):
                self._add_issue(
                    file_path, line_num, 1, IssueType.ERROR,
                    "Using {% static %} without loading static template tags",
                    "Add {% load static %} at the top of the template"
                )
    
    def _check_accessibility(self, lines: List[str], file_path: Path):
        """Check for accessibility issues."""
        for line_num, line in enumerate(lines, 1):
            # Check for images without alt text
            if re.search(r'<img[^>]*(?!alt=)[^>]*>', line):
                self._add_issue(
                    file_path, line_num, 1, IssueType.WARNING,
                    "Image without alt attribute",
                    "Add alt attribute for accessibility"
                )
            
            # Check for buttons without accessible text
            if re.search(r'<button[^>]*>(?!.*[^<]+.*</button>)', line):
                self._add_issue(
                    file_path, line_num, 1, IssueType.WARNING,
                    "Button without accessible text content",
                    "Add text content or aria-label to button"
                )
    
    def _check_performance(self, lines: List[str], file_path: Path):
        """Check for performance issues."""
        for line_num, line in enumerate(lines, 1):
            # Check for multiple database queries in loops
            if re.search(r'{%\s*for\s+', line):
                # Look for potential N+1 queries in the next few lines
                for i in range(line_num, min(line_num + 10, len(lines))):
                    if re.search(r'{{\s*\w+\.\w+\.\w+', lines[i]):
                        self._add_issue(
                            file_path, line_num, 1, IssueType.WARNING,
                            "Potential N+1 query in loop",
                            "Consider using select_related() or prefetch_related()"
                        )
                        break
    
    def _check_security(self, lines: List[str], file_path: Path):
        """Check for security issues."""
        for line_num, line in enumerate(lines, 1):
            # Check for unescaped user input
            if re.search(r'{{\s*[^|]*user\.[^|]*[^|]\s*}}', line):
                self._add_issue(
                    file_path, line_num, 1, IssueType.WARNING,
                    "Unescaped user input",
                    "Consider using |escape filter for user input"
                )
            
            # Check for potential XSS
            if re.search(r'{{\s*[^|]*\|safe\s*}}', line):
                self._add_issue(
                    file_path, line_num, 1, IssueType.WARNING,
                    "Using |safe filter",
                    "Ensure content is safe before using |safe filter"
                )
    
    def _check_consistency(self, lines: List[str], file_path: Path):
        """Check for consistency issues."""
        # Check for mixed indentation
        has_tabs = any('\t' in line for line in lines)
        has_spaces = any(line.startswith(' ') for line in lines)
        
        if has_tabs and has_spaces:
            self._add_issue(
                file_path, 1, 1, IssueType.WARNING,
                "Mixed tabs and spaces in indentation",
                "Use consistent indentation (preferably spaces)"
            )
        
        # Check for trailing whitespace
        for line_num, line in enumerate(lines, 1):
            if line.rstrip() != line:
                self._add_issue(
                    file_path, line_num, 1, IssueType.INFO,
                    "Trailing whitespace",
                    "Remove trailing whitespace"
                )
    
    def _add_issue(self, file_path: Path, line_number: int, column: int, 
                   issue_type: IssueType, message: str, suggestion: str = None):
        """Add an issue to the list."""
        issue = TemplateIssue(
            file_path=file_path,
            line_number=line_number,
            column=column,
            issue_type=issue_type,
            message=message,
            suggestion=suggestion
        )
        self.issues.append(issue)
    
    def get_issues_by_type(self, issue_type: IssueType) -> List[TemplateIssue]:
        """Get issues filtered by type."""
        return [issue for issue in self.issues if issue.issue_type == issue_type]
    
    def get_issues_by_file(self, file_path: Path) -> List[TemplateIssue]:
        """Get issues for a specific file."""
        return [issue for issue in self.issues if issue.file_path == file_path]


def main():
    """Main function for the template linter."""
    parser = argparse.ArgumentParser(description='Django Template Linter')
    parser.add_argument('--file', type=str, help='Lint specific template file')
    parser.add_argument('--fix', action='store_true', help='Attempt to fix issues')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).parent.parent
    linter = DjangoTemplateLinter(project_root)
    
    if args.file:
        # Lint specific file
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
        
        issues = linter.lint_template_file(file_path)
    else:
        # Lint all templates
        issues = linter.lint_all_templates()
    
    # Display results
    if args.format == 'json':
        import json
        issues_data = []
        for issue in issues:
            issues_data.append({
                'file': str(issue.file_path),
                'line': issue.line_number,
                'column': issue.column,
                'type': issue.issue_type.value,
                'message': issue.message,
                'suggestion': issue.suggestion
            })
        print(json.dumps(issues_data, indent=2))
    else:
        # Group issues by type
        errors = linter.get_issues_by_type(IssueType.ERROR)
        warnings = linter.get_issues_by_type(IssueType.WARNING)
        infos = linter.get_issues_by_type(IssueType.INFO)
        
        if errors:
            print(f"\n❌ {len(errors)} Errors:")
            for issue in errors:
                print(f"  {issue.file_path}:{issue.line_number}: {issue.message}")
                if issue.suggestion and args.verbose:
                    print(f"    💡 {issue.suggestion}")
        
        if warnings:
            print(f"\n⚠️  {len(warnings)} Warnings:")
            for issue in warnings:
                print(f"  {issue.file_path}:{issue.line_number}: {issue.message}")
                if issue.suggestion and args.verbose:
                    print(f"    💡 {issue.suggestion}")
        
        if infos:
            print(f"\nℹ️  {len(infos)} Info:")
            for issue in infos:
                print(f"  {issue.file_path}:{issue.line_number}: {issue.message}")
                if issue.suggestion and args.verbose:
                    print(f"    💡 {issue.suggestion}")
        
        if not issues:
            print("✅ All templates are clean!")
        else:
            print(f"\nTotal issues: {len(issues)}")
    
    # Exit with error code if there are errors
    if errors:
        sys.exit(1)


if __name__ == '__main__':
    main()
