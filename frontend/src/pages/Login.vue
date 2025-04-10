<template>
  <div class="min-h-screen flex items-center justify-center bg-blue-900 p-4">
    <div class="max-w-md w-full">
      <!-- Logo -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-green-500">NetRaven</h1>
        <p class="text-gray-400 mt-1">Network Configuration Management</p>
      </div>
      
      <!-- Login Form -->
      <div class="bg-blue-800 rounded-lg shadow-xl p-8 border border-gray-700">
        <h2 class="text-2xl font-bold mb-6 text-center text-white">Login</h2>
        
        <form @submit.prevent="handleLogin">
          <div class="mb-5">
            <label for="username" class="block text-sm font-medium text-gray-300 mb-1">Username</label>
            <input 
              type="text" 
              id="username" 
              v-model="username" 
              required
              class="w-full px-3 py-2 bg-blue-900 border border-gray-600 rounded-md shadow-sm text-white focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="Enter your username"
            >
          </div>
          <div class="mb-6">
            <label for="password" class="block text-sm font-medium text-gray-300 mb-1">Password</label>
            <input 
              type="password" 
              id="password" 
              v-model="password" 
              required
              class="w-full px-3 py-2 bg-blue-900 border border-gray-600 rounded-md shadow-sm text-white focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="Enter your password"
            >
          </div>

          <!-- Error Message -->
          <div v-if="authStore.loginError" class="mb-4 text-red-400 text-sm text-center bg-red-900/30 p-3 rounded border border-red-800">
            {{ authStore.loginError }}
          </div>

          <!-- Submit Button -->
          <button 
            type="submit" 
            :disabled="authStore.isLoading" 
            class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-opacity-50 disabled:opacity-50 transition-colors duration-200"
          >
            <span v-if="authStore.isLoading" class="flex items-center justify-center">
              <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Logging in...
            </span>
            <span v-else>Sign in</span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../store/auth'

const authStore = useAuthStore()
const username = ref('')
const password = ref('')

async function handleLogin() {
  if (!username.value || !password.value) {
    // Basic validation (can be enhanced)
    authStore.loginError = 'Username and password are required.'; 
    return;
  }
  await authStore.login({ username: username.value, password: password.value })
}
</script>

<style scoped>
/* Add custom styles if needed */
</style>
