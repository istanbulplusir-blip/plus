// Playwright Configuration for Cross-Browser Testing
// Task 15: Implement cross-browser compatibility and testing

const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  // Test directory
  testDir: './tests/cross-browser',
  
  // Global test timeout
  timeout: 30 * 1000,
  
  // Expect timeout for assertions
  expect: {
    timeout: 5000,
  },
  
  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,
  
  // Retry on CI only
  retries: process.env.CI ? 2 : 0,
  
  // Opt out of parallel tests on CI
  workers: process.env.CI ? 1 : undefined,
  
  // Reporter to use
  reporter: [
    ['html', { outputFolder: 'test-results/html-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['list']
  ],
  
  // Shared settings for all the projects below
  use: {
    // Base URL to use in actions like `await page.goto('/')`
    baseURL: 'http://localhost:8000',
    
    // Collect trace when retrying the failed test
    trace: 'on-first-retry',
    
    // Capture screenshot after each test failure
    screenshot: 'only-on-failure',
    
    // Record video only when retrying a test for the first time
    video: 'retain-on-failure',
    
    // Global test timeout
    actionTimeout: 10 * 1000,
    
    // Navigation timeout
    navigationTimeout: 30 * 1000,
  },

  // Configure projects for major browsers
  projects: [
    // Desktop Browsers
    {
      name: 'chromium-desktop',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
        deviceScaleFactor: 1,
      },
    },
    {
      name: 'firefox-desktop',
      use: { 
        ...devices['Desktop Firefox'],
        viewport: { width: 1280, height: 720 },
        deviceScaleFactor: 1,
      },
    },
    {
      name: 'webkit-desktop',
      use: { 
        ...devices['Desktop Safari'],
        viewport: { width: 1280, height: 720 },
        deviceScaleFactor: 1,
      },
    },
    {
      name: 'edge-desktop',
      use: { 
        ...devices['Desktop Edge'],
        viewport: { width: 1280, height: 720 },
        deviceScaleFactor: 1,
      },
    },

    // Large Desktop Screens
    {
      name: 'chromium-large',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
        deviceScaleFactor: 1,
      },
    },
    {
      name: 'firefox-large',
      use: { 
        ...devices['Desktop Firefox'],
        viewport: { width: 1920, height: 1080 },
        deviceScaleFactor: 1,
      },
    },

    // 4K Screens
    {
      name: 'chromium-4k',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 3840, height: 2160 },
        deviceScaleFactor: 2,
      },
    },

    // Mobile devices
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 12'] },
    },
    {
      name: 'mobile-safari-landscape',
      use: { 
        ...devices['iPhone 12 landscape'],
      },
    },

    // Tablets
    {
      name: 'tablet-chrome',
      use: { ...devices['Galaxy Tab S4'] },
    },
    {
      name: 'tablet-safari',
      use: { ...devices['iPad Pro'] },
    },
    {
      name: 'tablet-safari-landscape',
      use: { 
        ...devices['iPad Pro landscape'],
      },
    },

    // Accessibility Testing
    {
      name: 'accessibility-chrome',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
        // Force prefers-reduced-motion
        reducedMotion: 'reduce',
        // Force high contrast
        forcedColors: 'active',
      },
    },

    // RTL Testing
    {
      name: 'rtl-chrome',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
        locale: 'fa-IR', // Persian locale for RTL testing
      },
    },

    // Slow Network Testing
    {
      name: 'slow-network-chrome',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
        // Simulate slow 3G
        launchOptions: {
          args: ['--force-effective-connection-type=slow-2g']
        }
      },
    },

    // Print Testing
    {
      name: 'print-chrome',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
        // Enable print media emulation
        colorScheme: 'light',
      },
    },
  ],

  // Global setup and teardown
  globalSetup: require.resolve('./tests/global-setup.js'),
  globalTeardown: require.resolve('./tests/global-teardown.js'),

  // Run your local dev server before starting the tests
  webServer: {
    command: 'python manage.py runserver 8000',
    port: 8000,
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },

  // Test match patterns
  testMatch: [
    '**/tests/cross-browser/**/*.spec.js',
    '**/tests/visual-regression/**/*.spec.js',
    '**/tests/accessibility/**/*.spec.js',
    '**/tests/performance/**/*.spec.js',
  ],

  // Global test configuration
  globalTimeout: 60 * 60 * 1000, // 1 hour
  
  // Maximum failures before stopping
  maxFailures: process.env.CI ? 10 : undefined,
  
  // Update snapshots
  updateSnapshots: process.env.UPDATE_SNAPSHOTS ? 'all' : 'missing',
  
  // Metadata
  metadata: {
    'test-type': 'cross-browser-compatibility',
    'environment': process.env.NODE_ENV || 'development',
    'browser-support': 'Chrome 70+, Firefox 65+, Safari 12+, Edge 79+',
  },
});