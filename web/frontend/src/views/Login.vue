<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 px-4">
    <div class="max-w-md w-full bg-white rounded-lg shadow-lg overflow-hidden">
      <div class="bg-blue-600 text-white py-4 px-6">
        <h2 class="text-2xl font-bold">NetRaven Login</h2>
        <p class="text-sm">Sign in to manage your network devices</p>
      </div>
      
      <form @submit.prevent="handleLogin" class="py-6 px-8">
        <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {{ error }}
        </div>
        
        <div class="mb-4">
          <label for="username" class="block text-gray-700 text-sm font-bold mb-2">Username</label>
          <input
            id="username"
            v-model="username"
            type="text"
            class="appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            required
          />
        </div>
        
        <div class="mb-6">
          <label for="password" class="block text-gray-700 text-sm font-bold mb-2">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            class="appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            required
          />
        </div>
        
        <div class="flex items-center justify-between">
          <button
            type="submit"
            class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full"
            :disabled="loading"
          >
            <span v-if="loading">Signing in...</span>
            <span v-else>Sign In</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../store/auth'

export default {
  name: 'Login',
  
  setup() {
    const authStore = useAuthStore()
    const router = useRouter()
    const route = useRoute()
    
    const username = ref('')
    const password = ref('')
    const loading = computed(() => authStore.loading)
    const error = computed(() => authStore.error)
    
    const handleLogin = async () => {
      const success = await authStore.login(username.value, password.value)
      
      if (success) {
        // Redirect to the requested page or dashboard
        const redirectPath = route.query.redirect || '/'
        router.push(redirectPath)
      }
    }
    
    return {
      username,
      password,
      loading,
      error,
      handleLogin
    }
  }
}
</script> 