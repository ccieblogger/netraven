<script setup>
import DefaultLayout from './layouts/DefaultLayout.vue'
import { useRoute } from 'vue-router'
import { computed, onMounted } from 'vue'
import { useThemeStore } from './store/theme'
// Import other layouts if needed

// Only use DefaultLayout for authenticated pages
const route = useRoute()
const isLoginPage = computed(() => route.path === '/login')

// Initialize theme
const themeStore = useThemeStore()
onMounted(() => {
  themeStore.initTheme()
})
</script>

<template>
  <!-- Use DefaultLayout for all pages except login -->
  <DefaultLayout v-if="!isLoginPage">
    <router-view />
  </DefaultLayout>
  
  <!-- Direct router-view for login page -->
  <router-view v-else />
</template>

<style>
/* Global styles moved to main.scss */
</style>
