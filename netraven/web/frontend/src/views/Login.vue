<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-800 to-gray-900 py-12 px-4 sm:px-6 lg:px-8">
    <div class="w-full max-w-sm space-y-8">
      <!-- Logo Section -->
      <div class="text-center">
        <h1 class="text-white text-3xl font-bold tracking-tight">NetRaven</h1>
        <p class="mt-2 text-sm text-gray-400">Network Management Platform</p>
      </div>

      <!-- Login Card -->
      <div class="bg-white shadow-xl rounded-lg">
        <div class="text-center bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
          <h2 class="text-xl font-semibold text-white">Welcome Back</h2>
          <p class="mt-1 text-sm text-blue-100">Sign in to manage your network devices</p>
        </div>
        
        <form @submit.prevent="handleLogin" class="p-6 space-y-6">
          <!-- Error Alert -->
          <div v-if="error" 
               class="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 text-sm"
               role="alert">
            <p class="font-medium">Login Failed</p>
            <p>{{ error }}</p>
          </div>
          
          <!-- Username Field -->
          <div>
            <label for="username" class="block text-sm font-medium text-gray-700 mb-1">Username</label>
            <div class="relative rounded-md shadow-sm">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg class="h-4 w-4 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd" />
                </svg>
              </div>
              <input
                id="username"
                v-model="username"
                type="text"
                required
                autofocus
                class="block w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-md
                       focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500
                       placeholder:text-gray-400"
                placeholder="Enter your username"
                :disabled="loading"
              />
            </div>
          </div>
          
          <!-- Password Field -->
          <div>
            <label for="password" class="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <div class="relative rounded-md shadow-sm">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg class="h-4 w-4 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd" />
                </svg>
              </div>
              <input
                id="password"
                v-model="password"
                type="password"
                required
                class="block w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-md
                       focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500
                       placeholder:text-gray-400"
                placeholder="Enter your password"
                :disabled="loading"
              />
            </div>
          </div>
          
          <!-- Submit Button -->
          <div>
            <button
              type="submit"
              :disabled="loading"
              class="w-full flex justify-center items-center py-2 px-4 text-sm font-medium text-white
                     bg-gradient-to-r from-blue-600 to-blue-700 rounded-md
                     hover:from-blue-700 hover:to-blue-800
                     focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
                     disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors duration-200"
            >
              <template v-if="loading">
                <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Signing in...
              </template>
              <span v-else>Sign In</span>
            </button>
          </div>
          
          <!-- Debug Toggle -->
          <div class="text-center">
            <button type="button" @click="toggleDebugInfo" class="text-xs text-gray-500 hover:text-gray-700">
              {{ showDebugInfo ? 'Hide Debug Info' : 'Show Debug Info' }}
            </button>
          </div>
          
          <!-- Debug Info -->
          <div v-if="showDebugInfo" class="bg-gray-50 p-3 rounded text-xs text-gray-700 overflow-auto">
            <pre>{{ JSON.stringify(debugInfo, null, 2) }}</pre>
          </div>
        </form>
      </div>

      <!-- Footer -->
      <div class="text-center">
        <p class="text-xs text-gray-400">
          © {{ new Date().getFullYear() }} NetRaven. All rights reserved.
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../store/auth'

export default defineComponent({
  name: 'Login',
  
  setup() {
    const router = useRouter()
    const route = useRoute()
    const authStore = useAuthStore()
    
    // Reactive state
    const username = ref('admin')
    const password = ref('NetRaven')
    const showDebugInfo = ref(false)
    const debugInfo = ref({})
    
    // Computed properties
    const loading = computed(() => authStore.loading)
    const error = computed(() => authStore.error)
    
    // Methods
    function updateDebugInfo() {
      try {
        const envInfo = import.meta.env ? 'Available' : 'Not available'
        const apiUrl = import.meta.env?.VITE_API_BASE_URL || 'Not set'
        
        debugInfo.value = {
          time: new Date().toISOString(),
          origin: window.location.origin,
          hostname: window.location.hostname,
          envInfo: envInfo,
          apiUrl: apiUrl,
          tokenStatus: localStorage.getItem('access_token') ? 'Present' : 'None',
          browserInfo: navigator.userAgent
        }
      } catch (e) {
        debugInfo.value = {
          error: 'Error generating debug info: ' + e.message
        }
      }
    }
    
    function toggleDebugInfo() {
      showDebugInfo.value = !showDebugInfo.value
      if (showDebugInfo.value) {
        updateDebugInfo()
      }
    }
    
    async function handleLogin() {
      try {
        console.log('Login: Attempting login with username', username.value)
        
        // Try direct fetch for debugging
        if (showDebugInfo.value) {
          try {
            const formData = new URLSearchParams()
            formData.append('username', username.value)
            formData.append('password', password.value)
            
            const directUrl = 'http://localhost:8000/api/auth/token'
            console.log('Login: Trying direct fetch to', directUrl)
            
            const directResponse = await fetch(directUrl, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
              },
              body: formData,
              mode: 'cors'
            })
            
            const directData = await directResponse.json()
            console.log('Login: Direct fetch response', directResponse.status, directData)
            debugInfo.value.directFetch = {
              status: directResponse.status,
              success: directResponse.ok,
              data: directData
            }
          } catch (directError) {
            console.error('Login: Direct fetch failed', directError)
            debugInfo.value.directFetch = {
              error: directError.message
            }
          }
        }
        
        // Use the auth store for actual login
        const success = await authStore.login(username.value, password.value)
        
        if (success) {
          const redirectPath = route.query.redirect || '/dashboard'
          console.log('Login: Redirecting to', redirectPath)
          router.push(redirectPath)
        } else {
          console.error('Login: Failed', authStore.error)
          updateDebugInfo()
        }
      } catch (err) {
        console.error('Login: Exception occurred', err)
        updateDebugInfo()
      }
    }
    
    // Lifecycle hooks
    onMounted(() => {
      console.log('Login: Component mounted')
      authStore.error = null
      updateDebugInfo()
    })
    
    return {
      username,
      password,
      loading,
      error,
      showDebugInfo,
      debugInfo,
      handleLogin,
      toggleDebugInfo
    }
  }
})
</script>

<style scoped>
.error-message {
  color: #e53935;
  margin: 15px 0;
  text-align: center;
  background-color: rgba(229, 57, 53, 0.1);
  padding: 10px;
  border-radius: 4px;
  font-weight: 500;
}

.debug-info {
  margin-top: 10px;
  text-align: left;
  font-size: 12px;
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow: auto;
  max-height: 150px;
}

.debug-toggle {
  margin-top: 15px;
  text-align: center;
  color: #666;
  cursor: pointer;
}

.debug-toggle:hover {
  text-decoration: underline;
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s ease-in-out infinite;
  margin-right: 8px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style> 