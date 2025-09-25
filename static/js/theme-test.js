/**
 * Theme Switching Test Suite
 * Tests all aspects of the theme switching functionality
 */

class ThemeTest {
  constructor() {
    this.tests = [];
    this.results = {
      passed: 0,
      failed: 0,
      total: 0
    };
  }
  
  // Test theme manager initialization
  testThemeManagerInit() {
    const test = {
      name: 'Theme Manager Initialization',
      passed: false,
      message: ''
    };
    
    try {
      if (window.themeManager && typeof window.themeManager.getCurrentTheme === 'function') {
        const currentTheme = window.themeManager.getCurrentTheme();
        if (['light', 'dark'].includes(currentTheme)) {
          test.passed = true;
          test.message = `Theme manager initialized with theme: ${currentTheme}`;
        } else {
          test.message = `Invalid theme returned: ${currentTheme}`;
        }
      } else {
        test.message = 'Theme manager not found or missing methods';
      }
    } catch (error) {
      test.message = `Error: ${error.message}`;
    }
    
    this.tests.push(test);
    return test.passed;
  }
  
  // Test localStorage persistence
  testLocalStoragePersistence() {
    const test = {
      name: 'LocalStorage Persistence',
      passed: false,
      message: ''
    };
    
    try {
      const originalTheme = localStorage.getItem('theme');
      const testTheme = originalTheme === 'light' ? 'dark' : 'light';
      
      // Set test theme
      window.themeManager.setTheme(testTheme);
      
      // Check if it was saved
      const savedTheme = localStorage.getItem('theme');
      if (savedTheme === testTheme) {
        // Restore original theme
        window.themeManager.setTheme(originalTheme || 'light');
        test.passed = true;
        test.message = 'Theme persistence working correctly';
      } else {
        test.message = `Theme not saved correctly. Expected: ${testTheme}, Got: ${savedTheme}`;
      }
    } catch (error) {
      test.message = `Error: ${error.message}`;
    }
    
    this.tests.push(test);
    return test.passed;
  }
  
  // Test theme toggle buttons
  testThemeToggleButtons() {
    const test = {
      name: 'Theme Toggle Buttons',
      passed: false,
      message: ''
    };
    
    try {
      const themeButtons = document.querySelectorAll('.theme-toggle');
      if (themeButtons.length > 0) {
        let allButtonsWorking = true;
        let buttonCount = 0;
        
        themeButtons.forEach(button => {
          if (button.getAttribute('aria-label') && 
              button.querySelector('.theme-icon-light') && 
              button.querySelector('.theme-icon-dark')) {
            buttonCount++;
          } else {
            allButtonsWorking = false;
          }
        });
        
        if (allButtonsWorking && buttonCount > 0) {
          test.passed = true;
          test.message = `${buttonCount} theme toggle button(s) found and properly configured`;
        } else {
          test.message = `Some theme buttons are missing required elements. Found: ${buttonCount}`;
        }
      } else {
        test.message = 'No theme toggle buttons found';
      }
    } catch (error) {
      test.message = `Error: ${error.message}`;
    }
    
    this.tests.push(test);
    return test.passed;
  }
  
  // Test CSS custom properties
  testCSSCustomProperties() {
    const test = {
      name: 'CSS Custom Properties',
      passed: false,
      message: ''
    };
    
    try {
      const computedStyle = getComputedStyle(document.documentElement);
      const requiredProperties = [
        '--color-background',
        '--color-text-primary',
        '--color-primary',
        '--surface-glass',
        '--backdrop-blur'
      ];
      
      let missingProperties = [];
      
      requiredProperties.forEach(prop => {
        const value = computedStyle.getPropertyValue(prop);
        if (!value || value.trim() === '') {
          missingProperties.push(prop);
        }
      });
      
      if (missingProperties.length === 0) {
        test.passed = true;
        test.message = 'All required CSS custom properties are defined';
      } else {
        test.message = `Missing CSS properties: ${missingProperties.join(', ')}`;
      }
    } catch (error) {
      test.message = `Error: ${error.message}`;
    }
    
    this.tests.push(test);
    return test.passed;
  }
  
  // Test theme attribute changes
  testThemeAttributeChanges() {
    const test = {
      name: 'Theme Attribute Changes',
      passed: false,
      message: ''
    };
    
    try {
      const originalTheme = document.documentElement.getAttribute('data-theme');
      const testTheme = originalTheme === 'light' ? 'dark' : 'light';
      
      // Change theme
      window.themeManager.setTheme(testTheme);
      
      // Check if attribute changed
      const newTheme = document.documentElement.getAttribute('data-theme');
      if (newTheme === testTheme) {
        // Restore original theme
        window.themeManager.setTheme(originalTheme || 'light');
        test.passed = true;
        test.message = 'Theme attribute changes working correctly';
      } else {
        test.message = `Theme attribute not updated. Expected: ${testTheme}, Got: ${newTheme}`;
      }
    } catch (error) {
      test.message = `Error: ${error.message}`;
    }
    
    this.tests.push(test);
    return test.passed;
  }
  
  // Test system theme detection
  testSystemThemeDetection() {
    const test = {
      name: 'System Theme Detection',
      passed: false,
      message: ''
    };
    
    try {
      if (window.matchMedia) {
        const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        const systemPrefersDark = darkModeQuery.matches;
        
        // Clear localStorage to test system detection
        const originalTheme = localStorage.getItem('theme');
        localStorage.removeItem('theme');
        
        // Create new theme manager instance to test system detection
        const testThemeManager = new ThemeManager();
        const detectedTheme = testThemeManager.getCurrentTheme();
        
        // Restore original theme
        if (originalTheme) {
          localStorage.setItem('theme', originalTheme);
        }
        
        const expectedTheme = systemPrefersDark ? 'dark' : 'light';
        if (detectedTheme === expectedTheme) {
          test.passed = true;
          test.message = `System theme detection working. Detected: ${detectedTheme}`;
        } else {
          test.message = `System theme detection failed. Expected: ${expectedTheme}, Got: ${detectedTheme}`;
        }
      } else {
        test.message = 'matchMedia not supported in this browser';
        test.passed = true; // Not a failure, just not supported
      }
    } catch (error) {
      test.message = `Error: ${error.message}`;
    }
    
    this.tests.push(test);
    return test.passed;
  }
  
  // Test accessibility features
  testAccessibilityFeatures() {
    const test = {
      name: 'Accessibility Features',
      passed: false,
      message: ''
    };
    
    try {
      const themeButtons = document.querySelectorAll('.theme-toggle');
      let accessibilityScore = 0;
      let totalChecks = 0;
      
      themeButtons.forEach(button => {
        // Check for aria-label
        if (button.getAttribute('aria-label')) accessibilityScore++;
        totalChecks++;
        
        // Check for keyboard support
        if (button.getAttribute('tabindex') !== '-1') accessibilityScore++;
        totalChecks++;
        
        // Check for screen reader status
        const statusElement = document.querySelector(`#${button.getAttribute('aria-describedby')}`);
        if (statusElement) accessibilityScore++;
        totalChecks++;
      });
      
      // Check for reduced motion support
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (prefersReducedMotion) {
        // Check if transitions are disabled
        const computedStyle = getComputedStyle(document.body);
        const transitionDuration = computedStyle.getPropertyValue('transition-duration');
        if (transitionDuration.includes('0.01ms') || transitionDuration === 'none') {
          accessibilityScore++;
        }
      } else {
        accessibilityScore++; // Not reduced motion, so this check passes
      }
      totalChecks++;
      
      const accessibilityPercentage = (accessibilityScore / totalChecks) * 100;
      
      if (accessibilityPercentage >= 80) {
        test.passed = true;
        test.message = `Accessibility features: ${accessibilityPercentage.toFixed(0)}% compliant`;
      } else {
        test.message = `Accessibility features: ${accessibilityPercentage.toFixed(0)}% compliant (needs improvement)`;
      }
    } catch (error) {
      test.message = `Error: ${error.message}`;
    }
    
    this.tests.push(test);
    return test.passed;
  }
  
  // Test theme transitions
  testThemeTransitions() {
    const test = {
      name: 'Theme Transitions',
      passed: false,
      message: ''
    };
    
    try {
      const testElement = document.body;
      const computedStyle = getComputedStyle(testElement);
      const transition = computedStyle.getPropertyValue('transition');
      
      if (transition && transition !== 'none' && transition.includes('background-color')) {
        test.passed = true;
        test.message = 'Theme transitions are properly configured';
      } else {
        test.message = 'Theme transitions not found or improperly configured';
      }
    } catch (error) {
      test.message = `Error: ${error.message}`;
    }
    
    this.tests.push(test);
    return test.passed;
  }
  
  // Run all tests
  runAllTests() {
    console.log('🎨 Running Theme Switching Tests...\n');
    
    this.tests = [];
    this.results = { passed: 0, failed: 0, total: 0 };
    
    // Run individual tests
    this.testThemeManagerInit();
    this.testLocalStoragePersistence();
    this.testThemeToggleButtons();
    this.testCSSCustomProperties();
    this.testThemeAttributeChanges();
    this.testSystemThemeDetection();
    this.testAccessibilityFeatures();
    this.testThemeTransitions();
    
    // Calculate results
    this.tests.forEach(test => {
      this.results.total++;
      if (test.passed) {
        this.results.passed++;
        console.log(`✅ ${test.name}: ${test.message}`);
      } else {
        this.results.failed++;
        console.log(`❌ ${test.name}: ${test.message}`);
      }
    });
    
    // Summary
    console.log(`\n📊 Test Results:`);
    console.log(`   Passed: ${this.results.passed}/${this.results.total}`);
    console.log(`   Failed: ${this.results.failed}/${this.results.total}`);
    console.log(`   Success Rate: ${((this.results.passed / this.results.total) * 100).toFixed(1)}%`);
    
    if (this.results.failed === 0) {
      console.log(`\n🎉 All theme switching tests passed!`);
    } else {
      console.log(`\n⚠️  Some tests failed. Please check the implementation.`);
    }
    
    return this.results;
  }
  
  // Test theme switching performance
  testPerformance() {
    console.log('⚡ Testing Theme Switching Performance...\n');
    
    const iterations = 10;
    const times = [];
    
    for (let i = 0; i < iterations; i++) {
      const startTime = performance.now();
      
      // Toggle theme
      window.themeManager.toggleTheme();
      
      const endTime = performance.now();
      times.push(endTime - startTime);
    }
    
    const averageTime = times.reduce((a, b) => a + b, 0) / times.length;
    const minTime = Math.min(...times);
    const maxTime = Math.max(...times);
    
    console.log(`📈 Performance Results (${iterations} iterations):`);
    console.log(`   Average: ${averageTime.toFixed(2)}ms`);
    console.log(`   Min: ${minTime.toFixed(2)}ms`);
    console.log(`   Max: ${maxTime.toFixed(2)}ms`);
    
    if (averageTime < 50) {
      console.log(`✅ Performance: Excellent (< 50ms)`);
    } else if (averageTime < 100) {
      console.log(`✅ Performance: Good (< 100ms)`);
    } else {
      console.log(`⚠️  Performance: Needs optimization (> 100ms)`);
    }
    
    return { averageTime, minTime, maxTime };
  }
}

// Auto-run tests when script loads (only in development)
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
  document.addEventListener('DOMContentLoaded', () => {
    // Wait a bit for theme manager to initialize
    setTimeout(() => {
      const themeTest = new ThemeTest();
      window.themeTest = themeTest; // Make available globally for manual testing
      
      // Run tests automatically in development
      themeTest.runAllTests();
      
      console.log('\n💡 Manual Testing Commands:');
      console.log('   themeTest.runAllTests() - Run all tests');
      console.log('   themeTest.testPerformance() - Test performance');
      console.log('   themeManager.toggleTheme() - Toggle theme');
      console.log('   themeManager.setTheme("light"|"dark") - Set specific theme');
    }, 1000);
  });
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ThemeTest;
}