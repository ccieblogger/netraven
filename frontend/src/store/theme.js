import { defineStore } from 'pinia';

export const useThemeStore = defineStore('theme', {
  state: () => ({
    currentTheme: 'dark',
    availableThemes: ['dark', 'light', 'blue'],
  }),
  
  getters: {
    isDarkTheme: (state) => state.currentTheme === 'dark',
    isLightTheme: (state) => state.currentTheme === 'light',
    isBlueTheme: (state) => state.currentTheme === 'blue',
  },
  
  actions: {
    setTheme(theme) {
      if (this.availableThemes.includes(theme)) {
        // Remove current theme class
        document.documentElement.classList.remove(`theme-${this.currentTheme}`);
        
        // Add new theme class
        document.documentElement.classList.add(`theme-${theme}`);
        
        // Tailwind dark mode support
        if (theme === 'dark') {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
        
        // Update state
        this.currentTheme = theme;
        
        // Save to localStorage for persistence
        localStorage.setItem('netraven-theme', theme);
      }
    },
    
    initTheme() {
      // Get saved theme or use default
      const savedTheme = localStorage.getItem('netraven-theme') || 'dark';
      
      // Apply theme
      this.setTheme(savedTheme);
    },
    
    toggleDarkMode() {
      // Simple toggle between light and dark
      const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
      this.setTheme(newTheme);
    }
  }
}); 