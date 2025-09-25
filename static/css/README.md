# Modern CSS Architecture

This directory contains the modernized CSS architecture for the Istanbul Plus e-commerce platform, implementing 2025 design trends while maintaining backward compatibility.

## Structure

```
static/css/
├── README.md                 # This documentation
├── style.css                 # Main entry point (imports main.css)
├── main.css                  # Modern architecture entry point
├── legacy.css                # Legacy styles for backward compatibility
├── base/                     # Foundation styles
│   ├── reset.css            # Modern CSS reset
│   ├── variables.css        # Design tokens and CSS custom properties
│   └── typography.css       # Typography system
├── themes/                   # Theme variations
│   ├── light.css            # Light theme
│   └── dark.css             # Dark theme
├── components/               # Reusable UI components
│   ├── buttons.css          # Button components
│   ├── forms.css            # Form components
│   ├── cards.css            # Card components
│   └── navigation.css       # Navigation components
├── layouts/                  # Layout patterns
│   ├── grid.css             # Grid systems
│   └── containers.css       # Container layouts
└── utilities/                # Utility classes
    ├── animations.css       # Animations and transitions
    └── helpers.css          # Helper utilities
```

## Design System

### Design Tokens

All design tokens are defined in `base/variables.css` using CSS custom properties:

- **Colors**: Primary, secondary, semantic colors, and gradients
- **Typography**: Font families, sizes, weights, and line heights
- **Spacing**: Consistent spacing scale based on 4px grid
- **Shadows**: Various shadow levels for depth
- **Border Radius**: Consistent border radius scale
- **Breakpoints**: Responsive design breakpoints

### Themes

The system supports light and dark themes:

- **Light Theme**: Default theme with light backgrounds
- **Dark Theme**: Dark mode with appropriate contrast adjustments
- **Theme Switching**: Controlled via `data-theme` attribute

### RTL Support

Full RTL (Right-to-Left) support for Persian content:

- RTL-aware CSS custom properties
- Directional utilities
- Proper text alignment and spacing

## Usage

### Including Styles

The main entry point is `style.css` which imports the modern architecture:

```html
<link rel="stylesheet" href="{% static 'css/style.css' %}" />
```

### Theme Switching

To enable theme switching, add the `data-theme` attribute to the `html` element:

```html
<html data-theme="light">
  <!-- or "dark" -->
</html>
```

### Using Design Tokens

Use CSS custom properties in your styles:

```css
.my-component {
  color: var(--color-primary);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}
```

### Glassmorphism Effects

Apply glassmorphism effects using the `.glass` class or custom properties:

```css
.glass-card {
  background: var(--glass-background);
  backdrop-filter: var(--backdrop-blur);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow);
}
```

## Implementation Status

- ✅ **Task 1**: Modern CSS architecture and design tokens
- ⏳ **Task 2**: Foundation styles and typography system
- ⏳ **Task 3**: Base template modernization
- ⏳ **Task 4**: Navigation component redesign
- ⏳ **Task 5**: Button component system
- ⏳ **Task 6**: Form component enhancements
- ⏳ **Task 7**: Card component modernization
- ⏳ **Task 8**: Home page redesign
- ⏳ **Task 9**: Micro-interactions and animations
- ⏳ **Task 10**: Footer enhancements
- ⏳ **Task 11**: Accessibility improvements
- ⏳ **Task 12**: CSS performance optimization
- ⏳ **Task 13**: Responsive design enhancements
- ⏳ **Task 14**: Theme switching functionality
- ⏳ **Task 15**: Cross-browser compatibility
- ⏳ **Task 16**: Testing and validation

## Migration Strategy

The architecture maintains backward compatibility through:

1. **Legacy Styles**: Existing styles moved to `legacy.css`
2. **Gradual Migration**: Components will be modernized incrementally
3. **No Breaking Changes**: Existing functionality preserved during transition

## Browser Support

- Modern browsers with CSS custom properties support
- Graceful degradation for older browsers
- Progressive enhancement approach

## Performance Considerations

- Modular architecture for better caching
- CSS custom properties for dynamic theming
- Minimal redundancy through design tokens
- Optimized for critical CSS extraction

## Contributing

When adding new styles:

1. Use design tokens from `variables.css`
2. Follow the modular architecture
3. Add styles to appropriate component files
4. Maintain RTL support
5. Test in both light and dark themes
6. Ensure accessibility compliance
