<template>
  <div class="h-full bg-blue-900">
    <div class="container mx-auto space-y-4 px-4 py-4">
      <!-- Stats Cards with uniform gap spacing -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Devices Card -->
        <div class="bg-blue-600 rounded-md overflow-hidden shadow-lg">
          <div class="p-4 flex justify-between items-start">
            <div>
              <h2 class="text-lg uppercase font-semibold text-gray-300">DEVICES</h2>
              <div class="mt-2 flex items-baseline">
                <p class="text-4xl font-bold text-white">0</p>
                <p class="ml-2 text-sm text-gray-300">Total Managed Devices</p>
              </div>
            </div>
            <div class="flex items-center justify-center h-10 w-10 rounded-md bg-blue-700">
              <svg class="w-6 h-6 text-blue-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
                <line x1="8" y1="21" x2="16" y2="21" />
                <line x1="12" y1="17" x2="12" y2="21" />
              </svg>
            </div>
          </div>
          <div class="bg-blue-700 px-4 py-3">
            <router-link to="/devices" class="flex items-center text-sm font-medium text-blue-300 hover:text-white">
              View Details
              <svg class="ml-1 w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </router-link>
          </div>
        </div>

        <!-- Jobs Card -->
        <div class="bg-green-600 rounded-md overflow-hidden shadow-lg">
          <div class="p-4 flex justify-between items-start">
            <div>
              <h2 class="text-lg uppercase font-semibold text-gray-300">JOBS</h2>
              <div class="mt-2 flex items-baseline">
                <p class="text-4xl font-bold text-white">0</p>
                <p class="ml-2 text-sm text-gray-300">Active Jobs</p>
              </div>
            </div>
            <div class="flex items-center justify-center h-10 w-10 rounded-md bg-green-700">
              <svg class="w-6 h-6 text-green-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3.332.8-4.5 2.05C10.875 3.87 9.32 3 7.5 3A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
              </svg>
            </div>
          </div>
          <div class="bg-green-700 px-4 py-3">
            <router-link to="/jobs" class="flex items-center text-sm font-medium text-green-300 hover:text-white">
              View Details
              <svg class="ml-1 w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </router-link>
          </div>
        </div>

        <!-- Credentials Card -->
        <div class="bg-purple-600 rounded-md overflow-hidden shadow-lg">
          <div class="p-4 flex justify-between items-start">
            <div>
              <h2 class="text-lg uppercase font-semibold text-gray-300">CREDENTIALS</h2>
              <div class="mt-2 flex items-baseline">
                <p class="text-4xl font-bold text-white">0</p>
                <p class="ml-2 text-sm text-gray-300">Stored Credentials</p>
              </div>
            </div>
            <div class="flex items-center justify-center h-10 w-10 rounded-md bg-purple-700">
              <svg class="w-6 h-6 text-purple-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path d="M15 7a2 2 0 0 1 2 2m4 0a6 6 0 0 1-7.743 5.743L11 17H9v2H7v2H4a1 1 0 0 1-1-1v-2.586a1 1 0 0 1 .293-.707l5.964-5.964A6 6 0 0 1 21 9z" />
              </svg>
            </div>
          </div>
          <div class="bg-purple-700 px-4 py-3">
            <router-link to="/credentials" class="flex items-center text-sm font-medium text-purple-300 hover:text-white">
              View Details
              <svg class="ml-1 w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </router-link>
          </div>
        </div>
      </div>

      <!-- Recent Activity Section -->
      <div class="bg-sidebar border border-divider rounded-md overflow-hidden">
        <div class="px-4 py-3 border-b border-divider flex justify-between items-center">
          <div>
            <h2 class="text-lg font-semibold text-white">Recent Activity</h2>
            <p class="text-xs text-gray-400">Latest system events and logs</p>
          </div>
          <router-link to="/logs" class="flex items-center text-sm font-medium text-blue-400 hover:text-white">
            View All Logs
            <svg class="ml-1 w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </router-link>
        </div>
        <div class="p-4">
          <div class="flex justify-center items-center py-6">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <span class="ml-3 text-gray-400">Loading recent activity...</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';

// In Vue 3.5, we can use the improved reactivity system
const isLoading = ref(true);

// Simple function to simulate data loading
// In a real app, this would be an API call
onMounted(() => {
  // Simulate API request
  setTimeout(() => {
    isLoading.value = false;
  }, 2000);
});
</script>
