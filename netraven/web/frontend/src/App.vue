<template>
  <div id="app">
    <!-- Simple error display -->
    <div v-if="appError" class="app-error">
      <div class="error-container">
        <h2>Application Error</h2>
        <p>{{ appError }}</p>
        <div class="error-actions">
          <button @click="reloadApp" class="error-button">Reload Application</button>
        </div>
      </div>
    </div>
    
    <!-- Simple loading indicator -->
    <div v-if="isInitializing" class="app-loading">
      <div class="loading-container">
        <div class="spinner"></div>
        <p>Loading application...</p>
      </div>
    </div>
    
    <!-- Main application -->
    <router-view v-if="!appError && !isInitializing" />
  </div>
</template>

<script>
import { ref, onErrorCaptured, onMounted, watch } from 'vue'
import { useAuthStore } from './store/auth'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

export default {
  name: 'App',
  
  setup() {
    const appError = ref(null)
    const isInitializing = ref(true)
    const authStore = useAuthStore()
    const router = useRouter()
    const toast = useToast()
    
    // Simple error handler
    onErrorCaptured((err, instance, info) => {
      console.error('App-level error captured:', err, info);
      
      // Don't set app error for authentication errors - they're handled by components
      if (err.message?.includes('authentication') || 
          err.message?.includes('token') || 
          err.response?.status === 401) {
        console.log('Authentication error caught at App level - not displaying global error');
        return false; // Don't propagate auth errors
      }
      
      // Set global error for other types of errors
      appError.value = `${err.message || 'An unexpected error occurred'}`;
      return false; // Don't propagate app-level errors
    })
    
    // Initialize auth state on app mount
    onMounted(() => {
      // If we have a token in localStorage, validate and setup refresh
      if (localStorage.getItem('access_token')) {
        // Set token in store
        authStore.token = localStorage.getItem('access_token')
        
        // Validate token and setup refresh mechanism
        const isValid = authStore.validateToken()
        
        if (isValid) {
          console.log('Token validated, setting up refresh mechanism')
          authStore.setupTokenRefresh()
          
          // Try to fetch user data with the token
          authStore.fetchCurrentUser().catch(error => {
            console.error('Failed to fetch user data on app start:', error)
          })
        } else {
          console.warn('Invalid token found in localStorage, clearing')
          authStore.clearAuth()
          toast.warning('Your session has expired. Please log in again.')
        }
      }
    })
    
    // Watch for token changes to save to localStorage
    watch(() => authStore.token, (newToken) => {
      if (newToken) {
        localStorage.setItem('access_token', newToken)
      } else {
        localStorage.removeItem('access_token')
      }
    })
    
    // Watch for auth errors to display toast
    watch(() => authStore.error, (newError) => {
      if (newError) {
        toast.error(newError)
        // Clear error after showing toast
        setTimeout(() => {
          authStore.clearError()
        }, 100)
      }
    })
    
    // Reload the application
    const reloadApp = () => {
      window.location.reload()
    }
    
    return {
      appError,
      isInitializing,
      reloadApp
    }
  }
}
</script>

<style>
@import 'tailwindcss/base';
@import 'tailwindcss/components';
@import 'tailwindcss/utilities';

body {
  background-color: #f3f4f6;
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
    Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.app-error {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.app-loading {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9998;
}

.loading-container {
  text-align: center;
}

.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border-left-color: #3b82f6;
  margin: 0 auto 1rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-container {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  padding: 2rem;
  max-width: 500px;
  width: 90%;
  text-align: center;
}

.error-container h2 {
  color: #ef4444;
  margin-top: 0;
}

.error-actions {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.error-button {
  background-color: #3b82f6;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 1rem;
}

.error-button:hover {
  background-color: #2563eb;
}
</style> 