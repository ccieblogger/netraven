<template>
  <div class="h-full bg-[#0D1321]">
    <!-- Use a container with uniform padding on all sides -->
    <div class="container mx-auto space-y-4 px-4 py-4">
      <!-- Stats Cards with uniform gap spacing -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Devices Card -->
        <div class="bg-blue-600 rounded overflow-hidden shadow-lg">
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
        <div class="bg-green-600 rounded overflow-hidden shadow-lg">
          <div class="p-4 flex justify-between items-start">
            <div>
              <h2 class="text-lg uppercase font-semibold text-gray-300">JOBS</h2>
              <div class="mt-2 flex items-baseline">
                <p class="text-4xl font-bold text-white">0</p>
                <p class="ml-2 text-sm text-gray-300">Active Jobs</p>
              </div>
            </div>
            <div class="flex items-center justify-center h-10 w-10 rounded-md bg-green-700">
              <svg class="w-6 h-6 text-green-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
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
        <div class="bg-purple-600 rounded overflow-hidden shadow-lg">
          <div class="p-4 flex justify-between items-start">
            <div>
              <h2 class="text-lg uppercase font-semibold text-gray-300">CREDENTIALS</h2>
              <div class="mt-2 flex items-baseline">
                <p class="text-4xl font-bold text-white">0</p>
                <p class="ml-2 text-sm text-gray-300">Stored Credentials</p>
              </div>
            </div>
            <div class="flex items-center justify-center h-10 w-10 rounded-md bg-purple-700">
              <svg class="w-6 h-6 text-purple-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
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
      <div class="bg-[#101B2D] border border-gray-700 rounded-md overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-700 flex justify-between items-center">
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
// Dashboard data can be fetched here
</script>
