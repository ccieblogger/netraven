<template>
  <div class="flex items-center">
    <button 
      v-for="theme in themes" 
      :key="theme.value" 
      @click="setTheme(theme.value)"
      class="w-8 h-8 rounded-full mr-2 flex items-center justify-center transition-all"
      :class="{ 
        'ring-2 ring-primary ring-offset-2 ring-offset-card': theme.value === currentTheme,
        'hover:scale-110': theme.value !== currentTheme
      }"
      :style="{ backgroundColor: theme.color }"
      :title="`Switch to ${theme.label} theme`"
    >
      <!-- Show checkmark icon if this is the active theme -->
      <svg 
        v-if="theme.value === currentTheme" 
        class="w-4 h-4 text-white" 
        fill="none" 
        viewBox="0 0 24 24" 
        stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useThemeStore } from '../../store/theme';

const themeStore = useThemeStore();
const currentTheme = computed(() => themeStore.currentTheme);

// Define the available themes with their colors
const themes = [
  { value: 'dark', label: 'Dark', color: '#0D1321' },
  { value: 'light', label: 'Light', color: '#F1F5F9' },
  { value: 'blue', label: 'Blue', color: '#1E3A8A' }
];

// Function to change the theme
const setTheme = (theme) => {
  themeStore.setTheme(theme);
};
</script> 