/**
 * Accessibility Testing and Validation Script
 * Task 11: Implement accessibility improvements
 * 
 * This script provides automated accessibility testing and validation
 * for WCAG 2.1 AA compliance
 */

class AccessibilityTester {
  constructor() {
    this.issues = [];
    this.init();
  }

  init() {
    // Only run in development mode
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      this.runTests();
    }
  }

  runTests() {
    console.log('🔍 Running Accessibility Tests...');
    
    this.testColorContrast();
    this.testAriaLabels();
    this.testKeyboardNavigation();
    this.testSemanticMarkup();
    this.testFormAccessibility();
    this.testImageAltText();
    this.testHeadingHierarchy();
    
    this.reportResults();
  }

  testColorContrast() {
    // Test color contrast ratios
    const elements = document.querySelectorAll('*');
    
    elements.forEach(element => {
      const styles = window.getComputedStyle(element);
      const color = styles.color;
      const backgroundColor = styles.backgroundColor;
      
      // Skip elements with transparent backgrounds
      if (backgroundColor === 'rgba(0, 0, 0, 0)' || backgroundColor === 'transparent') {
        return;
      }
      
      // Calculate contrast ratio (simplified)
      const contrast = this.calculateContrastRatio(color, backgroundColor);
      
      if (contrast < 4.5) {
        this.addIssue('color-contrast', element, `Low contrast ratio: ${contrast.toFixed(2)}`);
      }
    });
  }

  testAriaLabels() {
    // Test for missing ARIA labels on interactive elements
    const interactiveElements = document.querySelectorAll('button, a, input, select, textarea');
    
    interactiveElements.forEach(element => {
      const hasLabel = element.getAttribute('aria-label') || 
                      element.getAttribute('aria-labelledby') ||
                      element.getAttribute('title') ||
                      element.textContent.trim() ||
                      (element.tagName === 'INPUT' && element.getAttribute('placeholder'));
      
      if (!hasLabel) {
        this.addIssue('missing-label', element, 'Interactive element missing accessible label');
      }
    });
  }

  testKeyboardNavigation() {
    // Test for keyboard accessibility
    const focusableElements = document.querySelectorAll(
      'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    focusableElements.forEach(element => {
      // Check if element is focusable
      if (element.tabIndex < 0 && !element.hasAttribute('tabindex')) {
        this.addIssue('keyboard-nav', element, 'Element may not be keyboard accessible');
      }
      
      // Check for focus indicators
      const styles = window.getComputedStyle(element, ':focus');
      if (!styles.outline || styles.outline === 'none') {
        this.addIssue('focus-indicator', element, 'Missing focus indicator');
      }
    });
  }

  testSemanticMarkup() {
    // Test for proper semantic markup
    const landmarks = document.querySelectorAll('main, nav, header, footer, aside, section');
    
    if (landmarks.length === 0) {
      this.addIssue('semantic-markup', document.body, 'No semantic landmarks found');
    }
    
    // Check for proper heading hierarchy
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    let previousLevel = 0;
    
    headings.forEach(heading => {
      const level = parseInt(heading.tagName.charAt(1));
      
      if (level > previousLevel + 1) {
        this.addIssue('heading-hierarchy', heading, `Heading level jumps from h${previousLevel} to h${level}`);
      }
      
      previousLevel = level;
    });
  }

  testFormAccessibility() {
    // Test form accessibility
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
      const inputs = form.querySelectorAll('input, select, textarea');
      
      inputs.forEach(input => {
        const hasLabel = form.querySelector(`label[for="${input.id}"]`) ||
                        input.getAttribute('aria-label') ||
                        input.getAttribute('aria-labelledby');
        
        if (!hasLabel && input.type !== 'hidden' && input.type !== 'submit') {
          this.addIssue('form-label', input, 'Form input missing label');
        }
        
        // Check for required field indicators
        if (input.required && !input.getAttribute('aria-required')) {
          input.setAttribute('aria-required', 'true');
        }
      });
    });
  }

  testImageAltText() {
    // Test for missing alt text on images
    const images = document.querySelectorAll('img');
    
    images.forEach(img => {
      if (!img.getAttribute('alt') && !img.getAttribute('aria-hidden')) {
        this.addIssue('missing-alt', img, 'Image missing alt text');
      }
    });
  }

  testHeadingHierarchy() {
    // Test heading hierarchy
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    
    if (headings.length === 0) {
      this.addIssue('no-headings', document.body, 'No headings found on page');
      return;
    }
    
    const h1Count = document.querySelectorAll('h1').length;
    if (h1Count === 0) {
      this.addIssue('no-h1', document.body, 'No h1 heading found');
    } else if (h1Count > 1) {
      this.addIssue('multiple-h1', document.body, 'Multiple h1 headings found');
    }
  }

  calculateContrastRatio(color1, color2) {
    // Simplified contrast ratio calculation
    // In a real implementation, you'd use a proper color contrast library
    const rgb1 = this.parseColor(color1);
    const rgb2 = this.parseColor(color2);
    
    if (!rgb1 || !rgb2) return 21; // Assume good contrast if can't parse
    
    const l1 = this.getLuminance(rgb1);
    const l2 = this.getLuminance(rgb2);
    
    const lighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);
    
    return (lighter + 0.05) / (darker + 0.05);
  }

  parseColor(color) {
    // Simple RGB color parser
    const match = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
    if (match) {
      return {
        r: parseInt(match[1]),
        g: parseInt(match[2]),
        b: parseInt(match[3])
      };
    }
    return null;
  }

  getLuminance(rgb) {
    // Calculate relative luminance
    const { r, g, b } = rgb;
    const [rs, gs, bs] = [r, g, b].map(c => {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  }

  addIssue(type, element, message) {
    this.issues.push({
      type,
      element,
      message,
      selector: this.getSelector(element)
    });
    
    // Add visual indicator in development
    if (element && element.style) {
      element.classList.add('a11y-warning');
    }
  }

  getSelector(element) {
    if (element.id) return `#${element.id}`;
    if (element.className) return `.${element.className.split(' ')[0]}`;
    return element.tagName.toLowerCase();
  }

  reportResults() {
    if (this.issues.length === 0) {
      console.log('✅ No accessibility issues found!');
      return;
    }
    
    console.log(`⚠️ Found ${this.issues.length} accessibility issues:`);
    
    this.issues.forEach((issue, index) => {
      console.log(`${index + 1}. ${issue.type}: ${issue.message}`);
      console.log(`   Element: ${issue.selector}`);
      console.log(`   `, issue.element);
    });
    
    // Create summary report
    const summary = this.createSummaryReport();
    console.table(summary);
  }

  createSummaryReport() {
    const summary = {};
    
    this.issues.forEach(issue => {
      if (!summary[issue.type]) {
        summary[issue.type] = 0;
      }
      summary[issue.type]++;
    });
    
    return summary;
  }

  // Manual testing helpers
  static testKeyboardNavigation() {
    console.log('🎹 Testing keyboard navigation...');
    console.log('Use Tab to navigate, Enter/Space to activate, Escape to close');
    
    // Highlight focusable elements
    const focusable = document.querySelectorAll(
      'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    focusable.forEach((el, index) => {
      el.style.outline = '2px solid lime';
      el.title = `Focusable element ${index + 1}`;
    });
    
    setTimeout(() => {
      focusable.forEach(el => {
        el.style.outline = '';
        el.title = '';
      });
    }, 5000);
  }

  static testScreenReader() {
    console.log('🔊 Testing screen reader compatibility...');
    
    // Check for ARIA live regions
    const liveRegions = document.querySelectorAll('[aria-live]');
    console.log(`Found ${liveRegions.length} ARIA live regions`);
    
    // Test announcements
    const testRegion = document.getElementById('aria-live-polite');
    if (testRegion) {
      testRegion.textContent = 'تست اعلان برای صفحه‌خوان';
      setTimeout(() => {
        testRegion.textContent = '';
      }, 3000);
    }
  }

  static simulateColorBlindness() {
    console.log('🎨 Simulating color blindness...');
    
    // Add CSS filter to simulate color blindness
    const style = document.createElement('style');
    style.textContent = `
      html {
        filter: grayscale(100%);
      }
    `;
    document.head.appendChild(style);
    
    setTimeout(() => {
      document.head.removeChild(style);
    }, 5000);
  }
}

// Initialize accessibility tester
document.addEventListener('DOMContentLoaded', () => {
  new AccessibilityTester();
});

// Export for manual testing
window.AccessibilityTester = AccessibilityTester;