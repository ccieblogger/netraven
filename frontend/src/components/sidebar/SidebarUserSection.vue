<template>
  <div class="p-4 mt-auto border-t border-divider">
    <div class="flex items-center gap-3">
      <div class="flex-shrink-0">
        <div class="h-9 w-9 rounded-full bg-primary flex items-center justify-center text-white font-medium text-lg">
          A
        </div>
      </div>
      <div>
        <p class="text-sm font-medium text-text-primary">admin</p>
      </div>
    </div>
    <div class="mt-3 pb-3">
      <!-- ThemeSwitcher placeholder -->
      <div class="h-8 w-20 bg-gray-700 rounded"></div>
    </div>
    <div class="mt-2">
      <button class="w-full flex items-center gap-2 px-3 py-2 text-sm font-medium text-text-secondary hover:text-text-primary rounded-md hover:bg-card group">
        <svg class="h-5 w-5 text-text-secondary group-hover:text-text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
          <polyline points="16 17 21 12 16 7"></polyline>
          <line x1="21" y1="12" x2="9" y2="12"></line>
        </svg>
        Logout
      </button>
    </div>
  </div>
</template>

<script setup>
// Add logic for user info, theme switcher, and logout as needed
</script> 