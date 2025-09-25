# Theme Switching Functionality Guide

## Overview

The Istanbul Plus e-commerce platform features a comprehensive theme switching system that allows users to toggle between light and dark themes with smooth transitions, accessibility support, and localStorage persistence.

## Features

### ✨ Core Features

- **Smooth Theme Transitions**: 0.3s smooth transitions between light and dark themes
- **localStorage Persistence**: User's theme preference is saved and restored
- **System Theme Detection**: Automatically detects user's system preference
- **Accessibility Support**: Full WCAG 2.1 AA compliance with screen reader support
- **Performance Optimized**: Hardware-accelerated transitions with reduced motion support
- **RTL Support**: Full right-to-left language support

### 🎨 Visual Features

- **Modern UI Components**: Glassmorphism theme toggle buttons
- **Animated Icons**: Smooth icon transitions between sun (light) and moon (dark)
- **Flash Effect**: Subtle visual feedback during theme changes
- **Responsive Design**: Works seamlessly across all device sizes

## Implementation

### 1. JavaScript Theme Manager

The theme switching functionality is powered by the `ThemeManager` class located in `static/js/theme-manager.js`.

#### Key Methods:

```javascript
// Initialize theme manager
const themeManager = new ThemeManager();

// Toggle between themes
themeManager.toggleTheme();

// Set specific theme
themeManager.setTheme("light"); // or 'dark'

// Get current theme
const currentTheme = themeManager.getCurrentTheme();
```

#### Features:

- Automatic initialization on page load
- System theme detection fallback
- Smooth transition effects
- Accessibility announcements
- Performance optimizations

### 2. CSS Architecture

The theme system uses CSS custom properties for consistent theming across all components.

#### Theme Files:

- `static/css/themes/light.css` - Light theme variables
- `static/css/themes/dark.css` - Dark theme variables
- `static/css/utilities/theme-transitions.css` - Smooth transition styles

#### Key CSS Variables:

```css
:root {
  /* Light Theme */
  --color-background: #ffffff;
  --color-text-primary: #212529;
  --surface-glass: rgba(255, 255, 255, 0.1);
}

[data-theme="dark"] {
  /* Dark Theme */
  --color-background: #0a0a0a;
  --color-text-primary: #f8f9fa;
  --surface-glass: rgba(0, 0, 0, 0.1);
}
```

### 3. HTML Structure

The theme is controlled by the `data-theme` attribute on the `<html>` element:

```html
<html lang="fa" dir="rtl" data-theme="light"></html>
```

#### Theme Toggle Button:

```html
<button type="button" class="theme-toggle" aria-label="تغییر تم">
  <i class="bi bi-sun-fill theme-icon-light"></i>
  <i class="bi bi-moon-fill theme-icon-dark"></i>
</button>
```

## Usage

### Basic Implementation

1. **Include Required Files**:

```html
<!-- CSS -->
<link rel="stylesheet" href="{% static 'css/main.css' %}" />

<!-- JavaScript -->
<script src="{% static 'js/theme-manager.js' %}"></script>
```

2. **Add Theme Toggle Button**:

```html
{% include "components/theme-toggle.html" with size="md" position="navbar" %}
```

3. **Initialize Theme Manager**:

```javascript
document.addEventListener("DOMContentLoaded", () => {
  window.themeManager = new ThemeManager();
});
```

### Advanced Usage

#### Custom Theme Toggle Component:

```html
<!-- Different sizes: sm, md, lg -->
{% include "components/theme-toggle.html" with size="lg" %}

<!-- Different positions: navbar, floating, inline -->
{% include "components/theme-toggle.html" with position="floating" %}
```

#### Programmatic Theme Control:

```javascript
// Listen for theme changes
window.addEventListener("themeChanged", (e) => {
  console.log("Theme changed to:", e.detail.theme);
});

// Set theme based on user preference
if (userPreference === "dark") {
  themeManager.setTheme("dark");
}
```

## Customization

### Adding New Theme Variables

1. **Add to Light Theme** (`static/css/themes/light.css`):

```css
[data-theme="light"] {
  --my-custom-color: #ffffff;
}
```

2. **Add to Dark Theme** (`static/css/themes/dark.css`):

```css
[data-theme="dark"] {
  --my-custom-color: #000000;
}
```

3. **Use in Components**:

```css
.my-component {
  background-color: var(--my-custom-color);
  transition: background-color 0.3s ease;
}
```

### Creating Custom Theme Toggle

```html
<button class="my-theme-toggle" onclick="window.themeManager.toggleTheme()">
  <span class="theme-icon-light">☀️</span>
  <span class="theme-icon-dark">🌙</span>
</button>
```

## Accessibility

### Screen Reader Support

- Proper ARIA labels and descriptions
- Live region announcements for theme changes
- Keyboard navigation support

### Reduced Motion Support

- Respects `prefers-reduced-motion` setting
- Disables animations for sensitive users
- Maintains functionality without animations

### High Contrast Support

- Enhanced borders and outlines in high contrast mode
- Improved focus indicators
- Better color contrast ratios

## Performance

### Optimizations

- Hardware-accelerated transitions using `transform` and `opacity`
- Efficient CSS custom property updates
- Minimal DOM manipulation
- Debounced theme switching

### Performance Metrics

- Theme switch time: < 50ms average
- Smooth 60fps transitions
- Minimal layout thrashing
- Optimized for mobile devices

## Testing

### Automated Testing

Run the built-in test suite in development mode:

```javascript
// Available in browser console (development only)
themeTest.runAllTests(); // Run all tests
themeTest.testPerformance(); // Test performance
```

### Manual Testing Checklist

- [ ] Theme toggle buttons work correctly
- [ ] Theme persists after page reload
- [ ] System theme detection works
- [ ] Smooth transitions between themes
- [ ] Accessibility features work
- [ ] Mobile responsiveness
- [ ] RTL layout support

## Browser Support

### Supported Browsers

- Chrome 88+
- Firefox 85+
- Safari 14+
- Edge 88+

### Fallbacks

- Graceful degradation for older browsers
- CSS custom property fallbacks
- JavaScript feature detection

## Troubleshooting

### Common Issues

1. **Theme not persisting**:

   - Check localStorage permissions
   - Verify theme manager initialization

2. **Transitions not smooth**:

   - Check for CSS conflicts
   - Verify transition properties are set

3. **Icons not switching**:

   - Check CSS theme icon visibility rules
   - Verify icon classes are correct

4. **Accessibility issues**:
   - Test with screen readers
   - Check ARIA labels and descriptions

### Debug Mode

Enable debug logging in development:

```javascript
// Add to theme-manager.js
const DEBUG = true;

if (DEBUG) {
  console.log("Theme changed to:", this.theme);
}
```

## Migration Guide

### From Previous Version

If upgrading from an older theme system:

1. Update CSS custom properties
2. Replace old theme toggle buttons
3. Update JavaScript initialization
4. Test all components

### Breaking Changes

- Theme attribute changed from `class` to `data-theme`
- CSS variable names updated for consistency
- JavaScript API methods renamed

## Contributing

### Adding New Features

1. Update theme CSS files
2. Modify theme manager JavaScript
3. Add tests for new functionality
4. Update documentation

### Code Style

- Use CSS custom properties for theming
- Follow BEM naming convention
- Add accessibility attributes
- Include performance optimizations

## Resources

### Related Files

- `static/js/theme-manager.js` - Main theme functionality
- `static/css/themes/` - Theme CSS files
- `templates/components/theme-toggle.html` - Theme toggle component
- `static/js/theme-test.js` - Testing utilities

### External Resources

- [CSS Custom Properties](https://developer.mozilla.org/en-US/docs/Web/CSS/--*)
- [prefers-color-scheme](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-color-scheme)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Bootstrap Icons](https://icons.getbootstrap.com/)

---

**Last Updated**: December 2024  
**Version**: 2.0.0  
**Maintainer**: Istanbul Plus Development Team
