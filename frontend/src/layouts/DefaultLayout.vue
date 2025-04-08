<template>
  <div class=\"min-h-screen bg-gray-100 flex\">
    <!-- Sidebar -->
    <aside class=\"w-64 bg-gray-800 text-white flex flex-col\">
      <div class=\"px-4 py-6 font-bold text-xl border-b border-gray-700\">NetRaven</div>
      <nav class=\"flex-1 px-2 py-4 space-y-1\">
        <router-link to=\"/dashboard\" class=\"block px-4 py-2 rounded hover:bg-gray-700\">Dashboard</router-link>
        <router-link to=\"/devices\" class=\"block px-4 py-2 rounded hover:bg-gray-700\">Devices</router-link>
        <router-link to=\"/tags\" class=\"block px-4 py-2 rounded hover:bg-gray-700\">Tags</router-link>
        <router-link to=\"/credentials\" class=\"block px-4 py-2 rounded hover:bg-gray-700\">Credentials</router-link>
        <router-link to=\"/jobs\" class=\"block px-4 py-2 rounded hover:bg-gray-700\">Jobs</router-link>
        <router-link to=\"/logs\" class=\"block px-4 py-2 rounded hover:bg-gray-700\">Logs</router-link>
        <router-link to=\"/users\" class=\"block px-4 py-2 rounded hover:bg-gray-700\">Users</router-link>
        <!-- Add other links as needed -->
      </nav>
      <div class=\"px-4 py-4 border-t border-gray-700\">
        <!-- User info / Logout button can go here -->
        <div v-if=\"authStore.isAuthenticated\" class=\"text-sm mb-2\">Logged in as: {{ authStore.username }}</div>
        <button 
          v-if=\"authStore.isAuthenticated\" 
          @click=\"authStore.logout\" 
          class=\"w-full text-left px-4 py-2 rounded hover:bg-gray-700\">
          Logout
          </button>
        <router-link 
          v-else 
          to=\"/login\" 
          class=\"w-full text-left block px-4 py-2 rounded hover:bg-gray-700\">
          Login
          </router-link>
      </div>
    </aside>

    <!-- Main Content -->
    <main class=\"flex-1 p-6\">
      <router-view />
    </main>

     <!-- Global Notification Area -->
     <!-- TODO: Implement Notification Component -->

  </div>
</template>

<script setup>
import { useAuthStore } from '../store/auth'; // Import auth store
const authStore = useAuthStore(); // Initialize

// Add sidebar logic if needed (e.g., user role checks for links)
</script> 