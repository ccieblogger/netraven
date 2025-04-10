<template>
  <div class="p-6">
    <!-- Header Section -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-white">Welcome to NetRaven</h1>
      <p class="text-gray-400 mt-1">Network Configuration Management System</p>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
      <!-- Devices Card -->
      <div class="bg-blue-800 rounded-lg shadow-lg overflow-hidden">
        <div class="p-5 flex justify-between items-start">
          <div>
            <h2 class="text-lg uppercase font-semibold text-gray-300">DEVICES</h2>
            <div class="mt-2 flex items-baseline">
              <p class="text-5xl font-bold text-white">0</p>
              <p class="ml-2 text-sm text-gray-400">Total Managed Devices</p>
            </div>
          </div>
          <div class="p-3 bg-blue-900 rounded-full">
            <svg class="w-8 h-8 text-blue-200" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
              <line x1="8" y1="21" x2="16" y2="21"></line>
              <line x1="12" y1="17" x2="12" y2="21"></line>
            </svg>
          </div>
        </div>
        <div class="bg-blue-900 px-5 py-3">
          <router-link to="/devices" class="text-blue-200 hover:text-white text-sm font-medium flex items-center">
            View Details
            <svg class="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
            </svg>
          </router-link>
        </div>
      </div>

      <!-- Jobs Card -->
      <div class="bg-green-800 rounded-lg shadow-lg overflow-hidden">
        <div class="p-5 flex justify-between items-start">
          <div>
            <h2 class="text-lg uppercase font-semibold text-gray-300">JOBS</h2>
            <div class="mt-2 flex items-baseline">
              <p class="text-5xl font-bold text-white">0</p>
              <p class="ml-2 text-sm text-gray-400">Active Jobs</p>
            </div>
          </div>
          <div class="p-3 bg-green-700 rounded-full">
            <svg class="w-8 h-8 text-green-200" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
            </svg>
          </div>
        </div>
        <div class="bg-green-700 px-5 py-3">
          <router-link to="/jobs" class="text-green-200 hover:text-white text-sm font-medium flex items-center">
            View Details
            <svg class="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
            </svg>
          </router-link>
        </div>
      </div>

      <!-- Credentials Card -->
      <div class="bg-purple-800 rounded-lg shadow-lg overflow-hidden">
        <div class="p-5 flex justify-between items-start">
          <div>
            <h2 class="text-lg uppercase font-semibold text-gray-300">CREDENTIALS</h2>
            <div class="mt-2 flex items-baseline">
              <p class="text-5xl font-bold text-white">0</p>
              <p class="ml-2 text-sm text-gray-400">Stored Credentials</p>
            </div>
          </div>
          <div class="p-3 bg-purple-900 rounded-full">
            <svg class="w-8 h-8 text-purple-200" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
          </div>
        </div>
        <div class="bg-purple-900 px-5 py-3">
          <router-link to="/credentials" class="text-purple-200 hover:text-white text-sm font-medium flex items-center">
            View Details
            <svg class="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
            </svg>
          </router-link>
        </div>
      </div>
    </div>

    <!-- Recent Activity Section -->
    <div class="bg-blue-800 rounded-lg shadow-lg overflow-hidden">
      <div class="px-5 py-4 border-b border-gray-700 flex justify-between items-center">
        <h2 class="text-xl font-bold text-white">Recent Activity</h2>
        <router-link to="/logs" class="text-gray-400 hover:text-white text-sm font-medium flex items-center">
          View All Logs
          <svg class="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
          </svg>
        </router-link>
      </div>
      <div class="p-5">
        <div class="flex justify-center items-center py-8">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span class="ml-3 text-gray-400">Loading recent activity...</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// Dashboard data can be fetched here
</script>
