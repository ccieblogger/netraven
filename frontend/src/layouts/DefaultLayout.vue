<template>
  <div class="flex h-screen bg-blue-900 text-white">
    <!-- Sidebar -->
    <aside class="w-64 flex flex-col bg-blue-800 border-r border-opacity-20 border-white">
      <!-- Logo -->
      <div class="px-6 py-4 border-b border-opacity-20 border-white">
        <h1 class="text-xl font-bold">
          <span class="text-green-500">Net</span><span class="text-white">Raven</span>
        </h1>
      </div>
      
      <!-- Navigation Links -->
      <nav class="flex-1 overflow-y-auto py-4">
        <div class="px-4 space-y-1">
          <router-link to="/dashboard" class="flex items-center px-4 py-2 hover:bg-blue-700 group">
            <svg class="w-5 h-5 mr-3 text-gray-400 group-hover:text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
            Dashboard
          </router-link>
          
          <router-link to="/devices" class="flex items-center px-4 py-2 hover:bg-blue-700 group">
            <svg class="w-5 h-5 mr-3 text-gray-400 group-hover:text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
            Devices
          </router-link>
          
          <router-link to="/tags" class="flex items-center px-4 py-2 hover:bg-blue-700 group">
            <svg class="w-5 h-5 mr-3 text-gray-400 group-hover:text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg>
            Tags
          </router-link>
          
          <router-link to="/credentials" class="flex items-center px-4 py-2 hover:bg-blue-700 group">
            <svg class="w-5 h-5 mr-3 text-gray-400 group-hover:text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
            Credentials
          </router-link>
          
          <router-link to="/jobs" class="flex items-center px-4 py-2 hover:bg-blue-700 group">
            <svg class="w-5 h-5 mr-3 text-gray-400 group-hover:text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
            Jobs
          </router-link>
          
          <router-link to="/logs" class="flex items-center px-4 py-2 hover:bg-blue-700 group">
            <svg class="w-5 h-5 mr-3 text-gray-400 group-hover:text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            Logs
          </router-link>
          
          <router-link to="/config-diff" class="flex items-center px-4 py-2 hover:bg-blue-700 group">
            <svg class="w-5 h-5 mr-3 text-gray-400 group-hover:text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="2" x2="22" y2="6"></line><path d="M7.5 20.5L19 9l-4-4L3.5 16.5 2 22l5.5-1.5z"></path></svg>
            Config Diff
          </router-link>
          
          <router-link to="/users" class="flex items-center px-4 py-2 hover:bg-blue-700 group">
            <svg class="w-5 h-5 mr-3 text-gray-400 group-hover:text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
            Users
          </router-link>
        </div>
      </nav>
      
      <!-- User Account Section -->
      <div class="px-4 py-4 border-t border-opacity-20 border-white mt-auto">
        <div v-if="authStore.isAuthenticated" class="flex items-center">
          <div class="flex-shrink-0">
            <div class="h-8 w-8 rounded-full bg-green-500 flex items-center justify-center">
              <span class="font-bold text-blue-900">{{ authStore.username?.charAt(0).toUpperCase() || 'A' }}</span>
            </div>
          </div>
          <div class="ml-3">
            <p class="text-sm font-medium">{{ authStore.username }}</p>
            <button @click="authStore.logout" class="text-xs text-gray-400 hover:text-white mt-1">
              Logout
            </button>
          </div>
        </div>
        <router-link v-else to="/login" class="flex items-center px-4 py-2 hover:bg-blue-700">
          Login
        </router-link>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 overflow-y-auto bg-blue-900">
      <slot></slot>
    </main>

    <!-- Global Notification Area -->
    <NotificationToast />
  </div>
</template>

<script setup>
import { useAuthStore } from '../store/auth';
import NotificationToast from '../components/NotificationToast.vue';

const authStore = useAuthStore();
</script>

<style scoped>
.router-link-active {
  background-color: rgba(30, 58, 138, 0.5); /* bg-blue-900 with opacity */
}

.router-link-active svg {
  color: #10b981; /* text-green-500 */
}
</style> 