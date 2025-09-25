/**
 * Theme Debug and Testing Script
 * For debugging theme switching issues
 */

(function() {
    'use strict';

    // Debug theme functionality
    const ThemeDebugger = {
        init: function() {
            this.logCurrentTheme();
            this.checkThemeVariables();
            this.addDebugControls();
            this.monitorThemeChanges();
        },

        logCurrentTheme: function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const savedTheme = localStorage.getItem('theme');
            const systemPreference = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
            
            console.group('🎨 Theme Debug Info');
            console.log('Current theme attribute:', currentTheme);
            console.log('Saved theme in localStorage:', savedTheme);
            console.log('System preference:', systemPreference);
            console.log('HTML classes:', document.documentElement.className);
            console.groupEnd();
        },

        checkThemeVariables: function() {
            const testElement = document.createElement('div');
            testElement.style.position = 'absolute';
            testElement.style.left = '-9999px';
            document.body.appendChild(testElement);

            const computedStyle = window.getComputedStyle(testElement);
            const variables = [
                '--color-background',
                '--color-text-primary',
                '--color-nav-background',
                '--color-card-background',
                '--glass-background'
            ];

            console.group('🔧 CSS Variables Check');
            variables.forEach(variable => {
                const value = computedStyle.getPropertyValue(variable);
                console.log(`${variable}:`, value || 'NOT DEFINED');
            });
            console.groupEnd();

            document.body.removeChild(testElement);
        },

        addDebugControls: function() {
            // Add debug panel
            const debugPanel = document.createElement('div');
            debugPanel.id = 'theme-debug-panel';
            debugPanel.innerHTML = `
                <div style="
                    position: fixed;
                    top: 10px;
                    right: 10px;
                    background: rgba(0, 0, 0, 0.8);
                    color: white;
                    padding: 10px;
                    border-radius: 5px;
                    font-family: monospace;
                    font-size: 12px;
                    z-index: 10000;
                    max-width: 300px;
                ">
                    <div><strong>Theme Debug Panel</strong></div>
                    <div>Current: <span id="debug-current-theme">-</span></div>
                    <div>Background: <span id="debug-bg-color">-</span></div>
                    <div>Text: <span id="debug-text-color">-</span></div>
                    <button onclick="window.themeDebugger.toggleTheme()" style="margin-top: 5px;">Toggle Theme</button>
                    <button onclick="window.themeDebugger.forceLight()" style="margin-top: 5px;">Force Light</button>
                    <button onclick="window.themeDebugger.forceDark()" style="margin-top: 5px;">Force Dark</button>
                    <button onclick="window.themeDebugger.close()" style="margin-top: 5px;">Close</button>
                </div>
            `;
            document.body.appendChild(debugPanel);

            // Update debug info
            this.updateDebugInfo();
        },

        updateDebugInfo: function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const bodyStyle = window.getComputedStyle(document.body);
            
            const currentThemeEl = document.getElementById('debug-current-theme');
            const bgColorEl = document.getElementById('debug-bg-color');
            const textColorEl = document.getElementById('debug-text-color');

            if (currentThemeEl) currentThemeEl.textContent = currentTheme || 'none';
            if (bgColorEl) bgColorEl.textContent = bodyStyle.backgroundColor;
            if (textColorEl) textColorEl.textContent = bodyStyle.color;
        },

        monitorThemeChanges: function() {
            // Monitor attribute changes
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
                        console.log('🔄 Theme changed to:', document.documentElement.getAttribute('data-theme'));
                        this.updateDebugInfo();
                        this.checkThemeApplication();
                    }
                });
            });

            observer.observe(document.documentElement, {
                attributes: true,
                attributeFilter: ['data-theme']
            });

            // Monitor localStorage changes
            window.addEventListener('storage', (e) => {
                if (e.key === 'theme') {
                    console.log('💾 Theme localStorage changed:', e.newValue);
                }
            });
        },

        checkThemeApplication: function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const bodyBg = window.getComputedStyle(document.body).backgroundColor;
            const bodyColor = window.getComputedStyle(document.body).color;

            console.group(`🎯 Theme Application Check (${currentTheme})`);
            console.log('Body background:', bodyBg);
            console.log('Body color:', bodyColor);

            // Check if colors match expected theme
            if (currentTheme === 'dark') {
                const isDarkBg = this.isColorDark(bodyBg);
                const isLightText = this.isColorLight(bodyColor);
                console.log('Is background dark?', isDarkBg);
                console.log('Is text light?', isLightText);
                
                if (!isDarkBg || !isLightText) {
                    console.warn('⚠️ Dark theme not properly applied!');
                }
            } else if (currentTheme === 'light') {
                const isLightBg = this.isColorLight(bodyBg);
                const isDarkText = this.isColorDark(bodyColor);
                console.log('Is background light?', isLightBg);
                console.log('Is text dark?', isDarkText);
                
                if (!isLightBg || !isDarkText) {
                    console.warn('⚠️ Light theme not properly applied!');
                }
            }
            console.groupEnd();
        },

        isColorDark: function(color) {
            // Convert color to RGB and check brightness
            const rgb = color.match(/\d+/g);
            if (!rgb) return false;
            const brightness = (parseInt(rgb[0]) * 299 + parseInt(rgb[1]) * 587 + parseInt(rgb[2]) * 114) / 1000;
            return brightness < 128;
        },

        isColorLight: function(color) {
            return !this.isColorDark(color);
        },

        toggleTheme: function() {
            if (window.themeManager) {
                window.themeManager.toggleTheme();
            } else {
                console.error('ThemeManager not found');
            }
        },

        forceLight: function() {
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
            console.log('🌞 Forced light theme');
        },

        forceDark: function() {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            console.log('🌙 Forced dark theme');
        },

        close: function() {
            const panel = document.getElementById('theme-debug-panel');
            if (panel) {
                panel.remove();
            }
        },

        testThemeSwitching: function() {
            console.log('🧪 Testing theme switching...');
            
            const originalTheme = document.documentElement.getAttribute('data-theme');
            
            // Test switching to dark
            this.forceDark();
            setTimeout(() => {
                this.checkThemeApplication();
                
                // Test switching to light
                this.forceLight();
                setTimeout(() => {
                    this.checkThemeApplication();
                    
                    // Restore original theme
                    document.documentElement.setAttribute('data-theme', originalTheme);
                    localStorage.setItem('theme', originalTheme);
                    console.log('✅ Theme switching test completed');
                }, 1000);
            }, 1000);
        }
    };

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            ThemeDebugger.init();
        });
    } else {
        ThemeDebugger.init();
    }

    // Expose globally for console access
    window.themeDebugger = ThemeDebugger;

    // Add keyboard shortcut for debug panel
    document.addEventListener('keydown', (e) => {
        // Ctrl+Shift+T to toggle debug panel
        if (e.ctrlKey && e.shiftKey && e.key === 'T') {
            e.preventDefault();
            if (document.getElementById('theme-debug-panel')) {
                ThemeDebugger.close();
            } else {
                ThemeDebugger.addDebugControls();
            }
        }
    });

    console.log('🎨 Theme Debugger loaded. Press Ctrl+Shift+T for debug panel or use window.themeDebugger in console.');

})();