<script setup>
import DefaultLayout from './layouts/DefaultLayout.vue'
import { useRoute } from 'vue-router'
import { computed } from 'vue'
// Import other layouts if needed

// Only use DefaultLayout for authenticated pages
const route = useRoute()
const isLoginPage = computed(() => route.path === '/login')
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
/* Global styles */
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  background-color: #1e3a8a; /* bg-blue-900 */
  color: white;
}
</style>
