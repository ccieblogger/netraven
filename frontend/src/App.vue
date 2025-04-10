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
  background-color: #0D1321; /* Rich Black - main content background */
  color: white;
  font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}

/* Card styling using direct CSS instead of @apply */
.netraven-card {
  border-radius: 0.375rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Icon containers */
.icon-container {
  padding: 0.75rem;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 3rem;
}

/* Stat counter styling */
.stat-counter {
  font-size: 3rem;
  font-weight: 700;
  color: white;
  line-height: 1;
}

/* View details links */
.view-details {
  font-size: 0.875rem;
  font-weight: 500;
  display: flex;
  align-items: center;
}
.view-details:hover {
  text-decoration: underline;
}
</style>
