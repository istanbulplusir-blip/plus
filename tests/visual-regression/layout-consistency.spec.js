// Visual Regression Testing for Cross-Browser Layout Consistency
// Task 15: Implement cross-browser compatibility and testing

const { test, expect } = require('@playwright/test');

test.describe('Visual Regression - Layout Consistency', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    // Wait for fonts to load
    await page.waitForTimeout(1000);
  });

  test('Homepage layout consistency across browsers', async ({ page, browserName }) => {
    // Hide dynamic content that might cause flakiness
    await page.addStyleTag({
      content: `
        .loading, .spinner, .skeleton {
          display: none !important;
        }
        * {
          animation-duration: 0s !important;
          transition-duration: 0s !important;
        }
      `
    });

    await expect(page).toHaveScreenshot(`homepage-${browserName}.png`, {
      fullPage: true,
      threshold: 0.2, // Allow 20% difference for browser rendering variations
    });
  });

  test('Product cards layout consistency', async ({ page, browserName }) => {
    // Navigate to products page or section with product cards
    const productCards = page.locator('.card, .product-card').first();
    
    if (await productCards.count() > 0) {
      await productCards.scrollIntoViewIfNeeded();
      
      await expect(productCards).toHaveScreenshot(`product-card-${browserName}.png`, {
        threshold: 0.15,
      });
    }
  });

  test('Navigation bar consistency', async ({ page, browserName }) => {
    const navbar = page.locator('nav, .navbar').first();
    
    if (await navbar.count() > 0) {
      await expect(navbar).toHaveScreenshot(`navbar-${browserName}.png`, {
        threshold: 0.1,
      });
    }
  });

  test('Button styles consistency', async ({ page, browserName }) => {
    const buttons = page.locator('.btn-modern, .btn-auth').first();
    
    if (await buttons.count() > 0) {
      await buttons.scrollIntoViewIfNeeded();
      
      await expect(buttons).toHaveScreenshot(`buttons-${browserName}.png`, {
        threshold: 0.1,
      });
    }
  });

  test('Form elements consistency', async ({ page, browserName }) => {
    // Look for forms on the page
    const forms = page.locator('form').first();
    
    if (await forms.count() > 0) {
      await forms.scrollIntoViewIfNeeded();
      
      await expect(forms).toHaveScreenshot(`form-${browserName}.png`, {
        threshold: 0.15,
      });
    }
  });

  test('Footer layout consistency', async ({ page, browserName }) => {
    const footer = page.locator('footer').first();
    
    if (await footer.count() > 0) {
      await footer.scrollIntoViewIfNeeded();
      
      await expect(footer).toHaveScreenshot(`footer-${browserName}.png`, {
        threshold: 0.1,
      });
    }
  });

  test('Mobile responsive layout', async ({ page, browserName }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(500); // Allow layout to adjust
    
    await expect(page).toHaveScreenshot(`mobile-layout-${browserName}.png`, {
      fullPage: true,
      threshold: 0.2,
    });
  });

  test('Tablet responsive layout', async ({ page, browserName }) => {
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(500); // Allow layout to adjust
    
    await expect(page).toHaveScreenshot(`tablet-layout-${browserName}.png`, {
      fullPage: true,
      threshold: 0.2,
    });
  });

  test('Large desktop layout', async ({ page, browserName }) => {
    // Test large desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(500); // Allow layout to adjust
    
    await expect(page).toHaveScreenshot(`desktop-large-${browserName}.png`, {
      fullPage: true,
      threshold: 0.2,
    });
  });

  test('Dark theme consistency', async ({ page, browserName }) => {
    // Enable dark theme if available
    await page.evaluate(() => {
      if (window.toggleTheme) {
        window.toggleTheme('dark');
      } else {
        document.documentElement.classList.add('dark-theme');
        document.documentElement.setAttribute('data-theme', 'dark');
      }
    });

    await page.waitForTimeout(500); // Allow theme to apply
    
    await expect(page).toHaveScreenshot(`dark-theme-${browserName}.png`, {
      fullPage: true,
      threshold: 0.25, // Allow more variation for theme differences
    });
  });

  test('RTL layout consistency', async ({ page, browserName }) => {
    // Set RTL direction
    await page.evaluate(() => {
      document.documentElement.setAttribute('dir', 'rtl');
      document.documentElement.setAttribute('lang', 'fa');
    });

    await page.waitForTimeout(500); // Allow RTL styles to apply
    
    await expect(page).toHaveScreenshot(`rtl-layout-${browserName}.png`, {
      fullPage: true,
      threshold: 0.3, // Allow more variation for RTL layout differences
    });
  });

  test('High contrast mode', async ({ page, browserName }) => {
    // Emulate high contrast mode
    await page.emulateMedia({ 
      colorScheme: 'light',
      forcedColors: 'active'
    });

    await page.waitForTimeout(500);
    
    await expect(page).toHaveScreenshot(`high-contrast-${browserName}.png`, {
      fullPage: true,
      threshold: 0.4, // High contrast can vary significantly
    });
  });

  test('Print layout', async ({ page, browserName }) => {
    // Emulate print media
    await page.emulateMedia({ media: 'print' });
    
    await page.waitForTimeout(500);
    
    await expect(page).toHaveScreenshot(`print-layout-${browserName}.png`, {
      fullPage: true,
      threshold: 0.3,
    });
  });

  test('Reduced motion preference', async ({ page, browserName }) => {
    // Emulate reduced motion preference
    await page.emulateMedia({ 
      reducedMotion: 'reduce'
    });

    await page.waitForTimeout(500);
    
    // Check that animations are disabled
    const animatedElements = page.locator('.card, .btn-modern');
    const elementCount = await animatedElements.count();
    
    if (elementCount > 0) {
      const firstElement = animatedElements.first();
      const transitionDuration = await firstElement.evaluate(el => {
        return window.getComputedStyle(el).transitionDuration;
      });
      
      // Transition duration should be very short or 0
      expect(['0s', '0.01ms']).toContain(transitionDuration);
    }
    
    await expect(page).toHaveScreenshot(`reduced-motion-${browserName}.png`, {
      fullPage: true,
      threshold: 0.2,
    });
  });

  test('Focus states visibility', async ({ page, browserName }) => {
    // Focus on interactive elements and capture their focus states
    const focusableElements = page.locator('button, a, input, select, textarea, [tabindex]:not([tabindex="-1"])');
    const elementCount = await focusableElements.count();
    
    if (elementCount > 0) {
      const firstElement = focusableElements.first();
      await firstElement.focus();
      
      await expect(firstElement).toHaveScreenshot(`focus-state-${browserName}.png`, {
        threshold: 0.1,
      });
    }
  });

  test('Hover states consistency', async ({ page, browserName }) => {
    const hoverableElements = page.locator('.card, .btn-modern, .btn').first();
    
    if (await hoverableElements.count() > 0) {
      await hoverableElements.hover();
      await page.waitForTimeout(300); // Allow hover animations to complete
      
      await expect(hoverableElements).toHaveScreenshot(`hover-state-${browserName}.png`, {
        threshold: 0.15,
      });
    }
  });

  test('Loading states consistency', async ({ page, browserName }) => {
    // Add loading state to buttons
    await page.evaluate(() => {
      const buttons = document.querySelectorAll('.btn-modern, .btn');
      buttons.forEach(btn => {
        btn.classList.add('btn-loading');
      });
    });

    await page.waitForTimeout(500);
    
    const loadingButton = page.locator('.btn-loading').first();
    if (await loadingButton.count() > 0) {
      await expect(loadingButton).toHaveScreenshot(`loading-state-${browserName}.png`, {
        threshold: 0.2,
      });
    }
  });

  test('Error states consistency', async ({ page, browserName }) => {
    // Add error states to form elements
    await page.evaluate(() => {
      const inputs = document.querySelectorAll('input, textarea, select');
      inputs.forEach(input => {
        input.classList.add('is-invalid', 'error');
        input.setAttribute('aria-invalid', 'true');
      });
    });

    await page.waitForTimeout(500);
    
    const errorInput = page.locator('.is-invalid, .error').first();
    if (await errorInput.count() > 0) {
      await expect(errorInput).toHaveScreenshot(`error-state-${browserName}.png`, {
        threshold: 0.15,
      });
    }
  });

  test('Empty states consistency', async ({ page, browserName }) => {
    // Navigate to a page that might have empty states
    // This would depend on your application structure
    const emptyState = page.locator('.empty-state, .no-results, .no-content').first();
    
    if (await emptyState.count() > 0) {
      await emptyState.scrollIntoViewIfNeeded();
      
      await expect(emptyState).toHaveScreenshot(`empty-state-${browserName}.png`, {
        threshold: 0.1,
      });
    }
  });

});