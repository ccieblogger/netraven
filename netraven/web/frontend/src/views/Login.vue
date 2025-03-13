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

      <div v-if="showDebugInfo" class="mt-8 p-4 bg-gray-100 rounded-md text-xs">
        <h3 class="font-bold mb-2">Login Debug Info</h3>
        <pre class="overflow-auto max-h-40">
Current Time: {{ new Date().toISOString() }}
Origin: {{ window.location.origin }}
Hostname: {{ window.location.hostname }}
API URL: {{ apiInfo }}
Access Token: {{ hasToken ? 'Present (' + tokenFirstChars + '...)' : 'Not present' }}
Last Login Error: {{ error }}
User Agent: {{ navigator.userAgent }}
        </pre>
        <div class="mt-2">
          <button @click="testAuth" class="px-2 py-1 bg-blue-500 text-white rounded text-xs">
            Test Auth Store
          </button>
          <button @click="testLocalStorage" class="ml-2 px-2 py-1 bg-green-500 text-white rounded text-xs">
            Test localStorage
          </button>
          <button @click="testRedirect" class="ml-2 px-2 py-1 bg-purple-500 text-white rounded text-xs">
            Test Redirect
          </button>
        </div>
        <div v-if="testResult" class="mt-2 p-2 bg-yellow-100 rounded">
          {{ testResult }}
        </div>
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
    const testResult = ref(null)
    
    // Computed properties
    const loading = computed(() => authStore.loading)
    const error = computed(() => authStore.error)
    const apiInfo = computed(() => {
      try {
        return JSON.stringify({
          envUrl: import.meta.env?.VITE_API_BASE_URL || 'Not set',
          localhostUrl: 'http://localhost:8000',
          dynamicUrl: window.location.origin.replace(':8080', ':8000')
        })
      } catch (err) {
        return 'Error: ' + err.message
      }
    })
    const hasToken = computed(() => !!localStorage.getItem('access_token'))
    const tokenFirstChars = computed(() => {
      const token = localStorage.getItem('access_token')
      return token ? token.substring(0, 10) : ''
    })
    
    // Methods
    function updateDebugInfo() {
      try {
        // Get info from the window and environment
        const envInfo = import.meta.env ? 'Available' : 'Not available'
        const apiUrl = import.meta.env?.VITE_API_BASE_URL || 'Not set'
        
        // Construct potential login URLs for debugging
        const loginUrlOptions = [
          apiUrl ? apiUrl + '/api/auth/token' : 'Not available',
          'http://localhost:8000/api/auth/token', 
          window.location.hostname + ':8000/api/auth/token',
          'http://' + window.location.hostname + ':8000/api/auth/token'
        ];
        
        debugInfo.value = {
          time: new Date().toISOString(),
          origin: window.location.origin,
          hostname: window.location.hostname,
          envInfo: envInfo,
          apiUrl: apiUrl,
          fallbackUrls: {
            localhost: 'http://localhost:8000',
            hostname: 'http://' + window.location.hostname + ':8000',
            dynamic: window.location.origin.replace(':8080', ':8000')
          },
          loginUrlOptions: loginUrlOptions,
          tokenStatus: localStorage.getItem('access_token') ? 'Present' : 'None',
          browserInfo: navigator.userAgent
        }
        
        // Try to ping the API URL to check connection
        debugInfo.value.connectionTest = {
          status: 'Testing connection...',
          timestamp: new Date().toISOString()
        }
        
        // Test connection to the first fallback URL
        testConnection('http://localhost:8000')
          .then(result => {
            debugInfo.value.connectionTest = {
              ...debugInfo.value.connectionTest,
              localhost: result
            }
          })
          .catch(error => {
            debugInfo.value.connectionTest = {
              ...debugInfo.value.connectionTest,
              localhost: { error: error.message }
            }
          });
      } catch (e) {
        debugInfo.value = {
          error: 'Error generating debug info: ' + e.message
        }
      }
    }
    
    // Helper function to test connection to an API URL
    async function testConnection(url) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);
        
        const response = await fetch(url + '/api/health', {
          method: 'GET',
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        return {
          status: response.status,
          ok: response.ok,
          timestamp: new Date().toISOString()
        };
      } catch (error) {
        return {
          error: error.message,
          timestamp: new Date().toISOString()
        };
      }
    }
    
    function testAuth() {
      try {
        testResult.value = `Auth Store Status: 
- Store initialized: ${!!authStore}
- Is authenticated: ${authStore.isAuthenticated}
- Has token: ${!!authStore.token}
- Has user: ${!!authStore.user}
- Loading: ${authStore.loading}
- Error: ${authStore.error || 'None'}`
      } catch (err) {
        testResult.value = `Auth Store Error: ${err.message}`
      }
    }
    
    function testLocalStorage() {
      try {
        // Try to write to localStorage
        const testKey = 'login_test_' + Date.now()
        localStorage.setItem(testKey, 'test value')
        const readValue = localStorage.getItem(testKey)
        localStorage.removeItem(testKey)
        
        testResult.value = `localStorage Test: ${readValue === 'test value' ? 'Success' : 'Failed - values don\'t match'}`
      } catch (err) {
        testResult.value = `localStorage Error: ${err.message}`
      }
    }
    
    function testRedirect() {
      testResult.value = 'Testing redirect to /route-test...'
      setTimeout(() => {
        window.location.href = '/route-test'
      }, 1000)
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
        updateDebugInfo() // Ensure debug info is updated even if not showing
        
        // Enhanced direct fetch for debugging
        try {
          const formData = new URLSearchParams()
          formData.append('username', username.value)
          formData.append('password', password.value)
          
          // Define URLs to try
          const testUrls = [
            'http://localhost:8000/api/auth/token',
            'http://' + window.location.hostname + ':8000/api/auth/token',
            window.location.origin.replace(':8080', ':8000') + '/api/auth/token'
          ]
          
          debugInfo.value.loginAttempts = []
          
          // Only test one URL if debug not showing to avoid delays
          const urlsToTest = showDebugInfo.value ? testUrls : [testUrls[0]]
          
          for (const url of urlsToTest) {
            try {
              console.log('Login: Trying direct fetch to', url)
              
              const startTime = new Date().getTime()
              const directResponse = await fetch(url, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: formData,
                mode: 'cors'
              })
              const endTime = new Date().getTime()
              
              let responseData = {}
              try {
                responseData = await directResponse.json()
              } catch (e) {
                responseData = { parseError: e.message }
              }
              
              const attemptResult = {
                url: url,
                latency: endTime - startTime + 'ms',
                status: directResponse.status,
                success: directResponse.ok,
                data: responseData
              }
              
              debugInfo.value.loginAttempts.push(attemptResult)
              console.log('Login: Direct fetch response', attemptResult)
              
              if (directResponse.ok) {
                // Found a working URL, no need to try others
                break
              }
            } catch (urlError) {
              const attemptResult = {
                url: url,
                error: urlError.message,
                errorType: urlError.name
              }
              debugInfo.value.loginAttempts.push(attemptResult)
              console.error('Login: Direct fetch failed for ' + url, urlError)
            }
          }
        } catch (directError) {
          console.error('Login: All direct fetch attempts failed', directError)
          debugInfo.value.directFetchError = directError.message
        }
        
        // Always show debug info on error
        showDebugInfo.value = true
        
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
        showDebugInfo.value = true // Always show debug info on error
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
      toggleDebugInfo,
      testAuth,
      testLocalStorage,
      testRedirect,
      testResult,
      apiInfo,
      hasToken,
      tokenFirstChars
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