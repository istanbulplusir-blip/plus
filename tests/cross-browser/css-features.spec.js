// Cross-Browser CSS Features Testing
// Task 15: Implement cross-browser compatibility and testing

const { test, expect } = require('@playwright/test');

test.describe('CSS Features Cross-Browser Compatibility', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for CSS to load
    await page.waitForLoadState('networkidle');
  });

  test('CSS Custom Properties support detection', async ({ page, browserName }) => {
    const supportsCustomProperties = await page.evaluate(() => {
      return window.CSS && CSS.supports && CSS.supports('--css', 'variables');
    });

    // Log support status
    console.log(`${browserName}: CSS Custom Properties supported: ${supportsCustomProperties}`);

    // Check if fallback classes are applied correctly
    const htmlClasses = await page.getAttribute('html', 'class');
    
    if (supportsCustomProperties) {
      expect(htmlClasses).toContain('css-custom-properties');
      expect(htmlClasses).not.toContain('no-css-custom-properties');
    } else {
      expect(htmlClasses).toContain('no-css-custom-properties');
      expect(htmlClasses).not.toContain('css-custom-properties');
    }
  });

  test('CSS Grid support and fallbacks', async ({ page, browserName }) => {
    const supportsGrid = await page.evaluate(() => {
      return window.CSS && CSS.supports && CSS.supports('display', 'grid');
    });

    console.log(`${browserName}: CSS Grid supported: ${supportsGrid}`);

    // Test product grid layout
    const productGrid = page.locator('.product-grid').first();
    if (await productGrid.count() > 0) {
      const gridDisplay = await productGrid.evaluate(el => {
        return window.getComputedStyle(el).display;
      });

      if (supportsGrid) {
        expect(gridDisplay).toBe('grid');
      } else {
        // Should fallback to flex
        expect(gridDisplay).toBe('flex');
      }
    }
  });

  test('Flexbox Gap support and fallbacks', async ({ page, browserName }) => {
    const supportsGap = await page.evaluate(() => {
      return window.CSS && CSS.supports && CSS.supports('gap', '1rem');
    });

    console.log(`${browserName}: Flexbox Gap supported: ${supportsGap}`);

    // Test button group spacing
    const buttonGroup = page.locator('.btn-group').first();
    if (await buttonGroup.count() > 0) {
      const buttons = buttonGroup.locator('.btn-modern');
      const buttonCount = await buttons.count();
      
      if (buttonCount > 1) {
        const firstButton = buttons.first();
        const marginRight = await firstButton.evaluate(el => {
          return window.getComputedStyle(el).marginRight;
        });

        if (supportsGap) {
          // With gap support, margin should be 0
          expect(marginRight).toBe('0px');
        } else {
          // Without gap support, margin should be used for spacing
          expect(marginRight).not.toBe('0px');
        }
      }
    }
  });

  test('Backdrop Filter support and fallbacks', async ({ page, browserName }) => {
    const supportsBackdropFilter = await page.evaluate(() => {
      return window.CSS && CSS.supports && (
        CSS.supports('backdrop-filter', 'blur(1px)') ||
        CSS.supports('-webkit-backdrop-filter', 'blur(1px)')
      );
    });

    console.log(`${browserName}: Backdrop Filter supported: ${supportsBackdropFilter}`);

    // Test glassmorphism cards
    const glassCard = page.locator('.card').first();
    if (await glassCard.count() > 0) {
      const backdropFilter = await glassCard.evaluate(el => {
        const style = window.getComputedStyle(el);
        return style.backdropFilter || style.webkitBackdropFilter;
      });

      const backgroundColor = await glassCard.evaluate(el => {
        return window.getComputedStyle(el).backgroundColor;
      });

      if (supportsBackdropFilter) {
        expect(backdropFilter).toContain('blur');
        // Background should be more transparent with backdrop filter
        expect(backgroundColor).toMatch(/rgba\(\d+,\s*\d+,\s*\d+,\s*0\.[0-3]\)/);
      } else {
        // Fallback should use more opaque background
        expect(backgroundColor).toMatch(/rgba\(\d+,\s*\d+,\s*\d+,\s*0\.[7-9]\)|rgb\(\d+,\s*\d+,\s*\d+\)/);
      }
    }
  });

  test('CSS Aspect Ratio support and fallbacks', async ({ page, browserName }) => {
    const supportsAspectRatio = await page.evaluate(() => {
      return window.CSS && CSS.supports && CSS.supports('aspect-ratio', '1/1');
    });

    console.log(`${browserName}: CSS Aspect Ratio supported: ${supportsAspectRatio}`);

    // Test product card images
    const cardImage = page.locator('.card-img-top').first();
    if (await cardImage.count() > 0) {
      const aspectRatio = await cardImage.evaluate(el => {
        return window.getComputedStyle(el).aspectRatio;
      });

      const paddingBottom = await cardImage.evaluate(el => {
        const container = el.closest('.aspect-ratio-container');
        return container ? window.getComputedStyle(container).paddingBottom : '0px';
      });

      if (supportsAspectRatio) {
        expect(aspectRatio).not.toBe('auto');
      } else {
        // Should use padding-bottom technique
        expect(paddingBottom).not.toBe('0px');
      }
    }
  });

  test('CSS Logical Properties support and fallbacks', async ({ page, browserName }) => {
    const supportsLogicalProperties = await page.evaluate(() => {
      return window.CSS && CSS.supports && CSS.supports('margin-inline-start', '1rem');
    });

    console.log(`${browserName}: CSS Logical Properties supported: ${supportsLogicalProperties}`);

    // Test text alignment
    const textStart = page.locator('.text-start').first();
    if (await textStart.count() > 0) {
      const textAlign = await textStart.evaluate(el => {
        return window.getComputedStyle(el).textAlign;
      });

      if (supportsLogicalProperties) {
        expect(textAlign).toBe('start');
      } else {
        // Should fallback to left/right based on direction
        expect(['left', 'right']).toContain(textAlign);
      }
    }
  });

  test('Modern CSS features graceful degradation', async ({ page, browserName }) => {
    // Test that the page renders correctly even without modern CSS features
    const bodyVisible = await page.locator('body').isVisible();
    expect(bodyVisible).toBe(true);

    // Check that content is readable
    const mainContent = page.locator('main, .main-content, #main-content').first();
    if (await mainContent.count() > 0) {
      const isVisible = await mainContent.isVisible();
      expect(isVisible).toBe(true);
    }

    // Check that navigation is functional
    const navbar = page.locator('nav, .navbar').first();
    if (await navbar.count() > 0) {
      const isVisible = await navbar.isVisible();
      expect(isVisible).toBe(true);
    }

    // Check that buttons are clickable
    const buttons = page.locator('button, .btn');
    const buttonCount = await buttons.count();
    if (buttonCount > 0) {
      const firstButton = buttons.first();
      const isVisible = await firstButton.isVisible();
      const isEnabled = await firstButton.isEnabled();
      expect(isVisible).toBe(true);
      expect(isEnabled).toBe(true);
    }
  });

  test('Progressive enhancement classes applied', async ({ page }) => {
    const htmlClasses = await page.getAttribute('html', 'class');
    
    // Should have JavaScript detection
    expect(htmlClasses).toContain('js');
    expect(htmlClasses).not.toContain('no-js');

    // Should have browser detection
    const browserClasses = ['chrome', 'firefox', 'safari', 'edge', 'webkit'];
    const hasBrowserClass = browserClasses.some(cls => htmlClasses.includes(cls));
    expect(hasBrowserClass).toBe(true);

    // Should have feature detection classes
    const featureClasses = [
      'css-custom-properties', 'no-css-custom-properties',
      'css-grid', 'no-css-grid',
      'flexbox', 'no-flexbox',
      'backdrop-filter', 'no-backdrop-filter'
    ];
    const hasFeatureClasses = featureClasses.some(cls => htmlClasses.includes(cls));
    expect(hasFeatureClasses).toBe(true);
  });

  test('CSS validation - no console errors', async ({ page }) => {
    const consoleErrors = [];
    
    page.on('console', msg => {
      if (msg.type() === 'error' && msg.text().includes('CSS')) {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Should not have CSS-related console errors
    expect(consoleErrors).toHaveLength(0);
  });

  test('CSS performance - no layout shifts', async ({ page }) => {
    await page.goto('/');
    
    // Measure Cumulative Layout Shift (CLS)
    const cls = await page.evaluate(() => {
      return new Promise((resolve) => {
        let clsValue = 0;
        let clsEntries = [];

        const observer = new PerformanceObserver((entryList) => {
          for (const entry of entryList.getEntries()) {
            if (!entry.hadRecentInput) {
              clsValue += entry.value;
              clsEntries.push(entry);
            }
          }
        });

        observer.observe({ type: 'layout-shift', buffered: true });

        // Wait for page to stabilize
        setTimeout(() => {
          observer.disconnect();
          resolve(clsValue);
        }, 3000);
      });
    });

    // CLS should be less than 0.1 (good score)
    expect(cls).toBeLessThan(0.1);
  });

  test('RTL layout support', async ({ page }) => {
    // Test RTL layout
    await page.evaluate(() => {
      document.documentElement.setAttribute('dir', 'rtl');
    });

    await page.waitForTimeout(500); // Allow styles to apply

    // Check that text alignment changes appropriately
    const textElements = page.locator('p, h1, h2, h3, .card-title');
    const elementCount = await textElements.count();
    
    if (elementCount > 0) {
      const firstElement = textElements.first();
      const textAlign = await firstElement.evaluate(el => {
        return window.getComputedStyle(el).textAlign;
      });

      // In RTL, text should align to the right or use logical properties
      expect(['right', 'start', 'end']).toContain(textAlign);
    }

    // Reset to LTR
    await page.evaluate(() => {
      document.documentElement.setAttribute('dir', 'ltr');
    });
  });

  test('Print styles applied correctly', async ({ page }) => {
    // Emulate print media
    await page.emulateMedia({ media: 'print' });

    // Check that interactive elements are hidden in print
    const buttons = page.locator('.btn, button');
    const buttonCount = await buttons.count();
    
    if (buttonCount > 0) {
      const firstButton = buttons.first();
      const display = await firstButton.evaluate(el => {
        return window.getComputedStyle(el).display;
      });
      
      expect(display).toBe('none');
    }

    // Check that backgrounds are removed for print
    const cards = page.locator('.card');
    const cardCount = await cards.count();
    
    if (cardCount > 0) {
      const firstCard = cards.first();
      const backgroundColor = await firstCard.evaluate(el => {
        return window.getComputedStyle(el).backgroundColor;
      });
      
      // Should be transparent or white for print
      expect(['rgba(0, 0, 0, 0)', 'transparent', 'rgb(255, 255, 255)']).toContain(backgroundColor);
    }

    // Reset to screen media
    await page.emulateMedia({ media: 'screen' });
  });

});