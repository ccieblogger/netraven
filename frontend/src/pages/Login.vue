<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
      <h2 class="text-2xl font-bold mb-6 text-center text-gray-800">NetRaven Login</h2>
      
      <!-- Login Form -->
      <form @submit.prevent="handleLogin">
        <div class="mb-4">
          <label for="username" class="block text-sm font-medium text-gray-700 mb-1">Username</label>
          <input 
            type="text" 
            id="username" 
            v-model="username" 
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="Enter your username"
          >
        </div>
        <div class="mb-6">
          <label for="password" class="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input 
            type="password" 
            id="password" 
            v-model="password" 
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="Enter your password"
          >
        </div>

        <!-- Error Message -->
        <div v-if="authStore.loginError" class="mb-4 text-red-600 text-sm text-center">
          {{ authStore.loginError }}
        </div>

        <!-- Submit Button -->
        <button 
          type="submit" 
          :disabled="authStore.isLoading" 
          class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50"
        >
          <span v-if="authStore.isLoading">Logging in...</span>
          <span v-else>Login</span>
        </button>
      </form>
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
