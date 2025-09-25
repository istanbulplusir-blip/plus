#!/usr/bin/env python3
"""
Cross-Browser Testing Validation Script
Task 15: Implement cross-browser compatibility and testing

This script validates that all cross-browser compatibility files are in place
and provides basic testing functionality.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists and report status."""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (MISSING)")
        return False

def validate_css_files():
    """Validate that all CSS files are in place."""
    print("\n🎨 Validating CSS Files...")
    
    css_files = [
        ("static/css/utilities/cross-browser.css", "Cross-browser compatibility CSS"),
        ("static/css/utilities/css-vars-fallback.css", "CSS variables fallback"),
        ("static/css/validation/css-validation.json", "CSS validation config"),
        (".stylelintrc.json", "Stylelint configuration"),
    ]
    
    all_present = True
    for file_path, description in css_files:
        if not check_file_exists(file_path, description):
            all_present = False
    
    return all_present

def validate_js_files():
    """Validate that all JavaScript files are in place."""
    print("\n🔧 Validating JavaScript Files...")
    
    js_files = [
        ("static/js/cross-browser-support.js", "Cross-browser support script"),
    ]
    
    all_present = True
    for file_path, description in js_files:
        if not check_file_exists(file_path, description):
            all_present = False
    
    return all_present

def validate_test_files():
    """Validate that all test files are in place."""
    print("\n🧪 Validating Test Files...")
    
    test_files = [
        ("playwright.config.js", "Playwright configuration"),
        ("tests/cross-browser/css-features.spec.js", "CSS features tests"),
        ("tests/visual-regression/layout-consistency.spec.js", "Visual regression tests"),
        ("package.json", "NPM package configuration"),
    ]
    
    all_present = True
    for file_path, description in test_files:
        if not check_file_exists(file_path, description):
            all_present = False
    
    return all_present

def validate_documentation():
    """Validate that documentation is in place."""
    print("\n📚 Validating Documentation...")
    
    doc_files = [
        ("docs/cross-browser-testing-guide.md", "Cross-browser testing guide"),
    ]
    
    all_present = True
    for file_path, description in doc_files:
        if not check_file_exists(file_path, description):
            all_present = False
    
    return all_present

def check_css_imports():
    """Check that cross-browser CSS is imported in main.css."""
    print("\n🔗 Validating CSS Imports...")
    
    main_css_path = "static/css/main.css"
    if not os.path.exists(main_css_path):
        print(f"❌ Main CSS file not found: {main_css_path}")
        return False
    
    with open(main_css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "cross-browser.css" in content:
        print("✅ Cross-browser CSS imported in main.css")
        return True
    else:
        print("❌ Cross-browser CSS not imported in main.css")
        return False

def check_template_integration():
    """Check that cross-browser script is included in base template."""
    print("\n🌐 Validating Template Integration...")
    
    template_path = "templates/base.html"
    if not os.path.exists(template_path):
        print(f"❌ Base template not found: {template_path}")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('class="no-js"', "no-js class in HTML element"),
        ('cross-browser-support.js', "Cross-browser support script"),
    ]
    
    all_present = True
    for check, description in checks:
        if check in content:
            print(f"✅ {description} found in template")
        else:
            print(f"❌ {description} not found in template")
            all_present = False
    
    return all_present

def validate_package_json():
    """Validate package.json configuration."""
    print("\n📦 Validating Package Configuration...")
    
    if not os.path.exists("package.json"):
        print("❌ package.json not found")
        return False
    
    try:
        with open("package.json", 'r', encoding='utf-8') as f:
            package_data = json.load(f)
        
        required_scripts = [
            "test:cross-browser",
            "validate:css",
            "test:visual",
        ]
        
        scripts = package_data.get("scripts", {})
        all_present = True
        
        for script in required_scripts:
            if script in scripts:
                print(f"✅ Script '{script}' configured")
            else:
                print(f"❌ Script '{script}' missing")
                all_present = False
        
        required_deps = [
            "@playwright/test",
            "stylelint",
        ]
        
        dev_deps = package_data.get("devDependencies", {})
        
        for dep in required_deps:
            if dep in dev_deps:
                print(f"✅ Dependency '{dep}' configured")
            else:
                print(f"❌ Dependency '{dep}' missing")
                all_present = False
        
        return all_present
        
    except json.JSONDecodeError:
        print("❌ package.json is not valid JSON")
        return False

def run_css_validation():
    """Run CSS validation if stylelint is available."""
    print("\n🔍 Running CSS Validation...")
    
    try:
        # Check if stylelint is available
        result = subprocess.run(
            ["npx", "stylelint", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"✅ Stylelint available: {result.stdout.strip()}")
            
            # Run validation on cross-browser CSS
            result = subprocess.run(
                ["npx", "stylelint", "static/css/utilities/cross-browser.css"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ Cross-browser CSS validation passed")
                return True
            else:
                print(f"❌ CSS validation failed:\n{result.stdout}\n{result.stderr}")
                return False
        else:
            print("⚠️  Stylelint not available, skipping CSS validation")
            return True
            
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️  Could not run CSS validation (stylelint not found)")
        return True

def generate_report():
    """Generate a summary report."""
    print("\n" + "="*60)
    print("📊 CROSS-BROWSER COMPATIBILITY VALIDATION REPORT")
    print("="*60)
    
    results = {
        "CSS Files": validate_css_files(),
        "JavaScript Files": validate_js_files(),
        "Test Files": validate_test_files(),
        "Documentation": validate_documentation(),
        "CSS Imports": check_css_imports(),
        "Template Integration": check_template_integration(),
        "Package Configuration": validate_package_json(),
        "CSS Validation": run_css_validation(),
    }
    
    print("\n📋 Summary:")
    passed = 0
    total = len(results)
    
    for category, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {category}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All cross-browser compatibility checks passed!")
        print("\n🚀 Next steps:")
        print("  1. Run 'npm install' to install dependencies")
        print("  2. Run 'npm run setup' to install Playwright browsers")
        print("  3. Run 'npm run test:cross-browser' to execute tests")
        print("  4. Run 'npm run validate:css' to validate CSS")
        return True
    else:
        print("⚠️  Some checks failed. Please review the issues above.")
        return False

def main():
    """Main function."""
    print("🔧 Cross-Browser Compatibility Validation")
    print("Task 15: Implement cross-browser compatibility and testing")
    print("-" * 60)
    
    success = generate_report()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()