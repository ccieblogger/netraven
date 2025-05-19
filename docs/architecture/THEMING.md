# NetRaven UI Theming System

This document explains the theming system implemented in NetRaven to enable consistent UI styling and easy theme switching.

## Overview

The NetRaven UI uses a combination of:
1. CSS variables for theme colors and properties
2. Tailwind CSS for utility classes
3. Vue components for reusable UI elements
4. Pinia store for theme state management

## Theme Variables

All theme colors and properties are defined as CSS variables in `src/styles/theme.scss`. These variables are then used throughout the application to ensure consistent styling. The main variable categories are:

- Brand colors (`--nr-primary`, `--nr-primary-light`, etc.)
- Background colors (`--nr-bg-sidebar`, `--nr-bg-content`, etc.)
- Text colors (`--nr-text-primary`, `--nr-text-secondary`)
- Border colors (`--nr-border`)
- Component-specific variables (`--nr-card-radius`, `--nr-sidebar-width`)

## Available Themes

NetRaven currently supports three themes:

1. **Dark** (default): Dark blue/navy color scheme
2. **Light**: White/gray color scheme for better daylight visibility
3. **Blue**: Deep blue color scheme as an alternative dark option

## How to Use the Theme System

### Using Theme Variables in Components

Instead of hardcoding colors, use the CSS variables or their Tailwind mappings:

```html
<!-- Use Tailwind classes that map to theme variables -->
<div class="bg-sidebar text-text-primary border-divider">
  Themed content
</div>

<!-- Or use CSS variables directly -->
<div :style="{ 
  backgroundColor: 'var(--nr-bg-sidebar)', 
  color: 'var(--nr-text-primary)'
}">
  Themed content
</div>
```

### Using the UI Components

The UI component library provides pre-styled components that respect the theme:

```html
<NrCard title="My Card">
  <p>This card will automatically use theme colors</p>
</NrCard>

<NrButton variant="primary">Themed Button</NrButton>
```

### Switching Themes

Use the ThemeSwitcher component or access the theme store directly:

```html
<!-- Include the theme switcher -->
<ThemeSwitcher />
```

```javascript
// Or switch themes programmatically
import { useThemeStore } from '@/store/theme'

const themeStore = useThemeStore()
themeStore.setTheme('light') // Options: 'dark', 'light', 'blue'
```

## Adding New Themes

To add a new theme:

1. Add a new theme class in `src/styles/theme.scss`:

```scss
.theme-new-theme {
  --nr-primary: #your-color;
  --nr-bg-sidebar: #your-color;
  // Override other variables as needed
}
```

2. Add the theme to the theme store in `src/store/theme.js`:

```javascript
state: () => ({
  currentTheme: 'dark',
  availableThemes: ['dark', 'light', 'blue', 'new-theme'],
}),
```

3. Add the theme to the ThemeSwitcher component options:

```javascript
const themes = [
  { value: 'dark', label: 'Dark', color: '#0D1321' },
  { value: 'light', label: 'Light', color: '#F1F5F9' },
  { value: 'blue', label: 'Blue', color: '#1E3A8A' },
  { value: 'new-theme', label: 'New Theme', color: '#your-color' },
];
```

## Extending the UI Component Library

When creating new components, follow these guidelines:

1. Use existing theme variables for colors and properties
2. Use Tailwind classes that map to theme variables when possible
3. Make components responsive and accessible
4. Document props and slots in component comments

## Best Practices

- Always use theme variables instead of hardcoding colors
- Ensure all interactive elements have appropriate hover/focus states
- Test components in all available themes
- Keep component props consistent with similar components 