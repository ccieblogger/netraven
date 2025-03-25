<template>
  <div class="min-h-screen flex flex-col bg-gray-100">
    <!-- Error display -->
    <div v-if="layoutError" class="bg-red-100 border-l-4 border-red-500 p-4">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="ml-3">
          <p class="text-sm text-red-700">
            {{ layoutError }}
            <button @click="retryLayout" class="font-medium underline text-red-700 hover:text-red-600 ml-2">
              Retry
            </button>
          </p>
        </div>
      </div>
    </div>
    
    <!-- Top Navigation -->
    <nav class="bg-blue-600 text-white">
      <div class="container mx-auto px-4 py-3 flex justify-between items-center">
        <div class="flex items-center space-x-4">
          <router-link to="/" class="text-2xl font-bold">NetRaven</router-link>
          <span class="text-sm hidden md:inline">Network Device Configuration Management</span>
        </div>
        
        <div v-if="isAuthenticated" class="flex items-center space-x-4">
          <div class="hidden md:flex space-x-4">
            <router-link to="/devices" class="hover:text-blue-200 transition">Devices</router-link>
            <router-link to="/backups" class="hover:text-blue-200 transition">Backups</router-link>
            <router-link to="/credentials" class="hover:text-blue-200 transition">Credentials</router-link>
            <router-link to="/credentials/dashboard" class="hover:text-blue-200 transition">Credential Dashboard</router-link>
            <router-link to="/tags" class="hover:text-blue-200 transition">Tags</router-link>
            <router-link to="/tag-rules" class="hover:text-blue-200 transition">Tag Rules</router-link>
            <router-link to="/job-logs" class="hover:text-blue-200 transition">Job Logs</router-link>
            <router-link to="/scheduled-jobs" class="hover:text-blue-200 transition">Scheduled Jobs</router-link>
            
            <!-- Admin section -->
            <template v-if="isAdmin">
              <router-link to="/keys" class="hover:text-blue-200 transition">Key Management</router-link>
              <router-link to="/admin-settings" class="hover:text-blue-200 transition">Admin Settings</router-link>
              <router-link to="/audit-logs" class="hover:text-blue-200 transition">Audit Logs</router-link>
            </template>
          </div>
          
          <div class="relative">
            <button @click="showUserMenu = !showUserMenu" class="flex items-center space-x-2 hover:text-blue-200">
              <span>{{ username || 'User' }}</span>
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </button>
            
            <div v-if="showUserMenu" class="absolute right-0 mt-2 py-2 w-48 bg-white rounded-md shadow-lg z-10">
              <a href="#" @click.prevent="logout" class="block px-4 py-2 text-gray-800 hover:bg-gray-100">
                Logout
              </a>
            </div>
          </div>
        </div>
        
        <div v-else>
          <router-link to="/login" class="px-4 py-2 bg-blue-700 rounded hover:bg-blue-800 transition">
            Login
          </router-link>
        </div>
      </div>
    </nav>
    
    <!-- Mobile Navigation (shown only on small screens) -->
    <div v-if="isAuthenticated" class="md:hidden bg-blue-700 text-white">
      <div class="container mx-auto px-4 py-2 flex justify-between">
        <router-link to="/devices" class="hover:text-blue-200 transition">Devices</router-link>
        <router-link to="/backups" class="hover:text-blue-200 transition">Backups</router-link>
        <router-link to="/credentials" class="hover:text-blue-200 transition">Creds</router-link>
        <router-link to="/credentials/dashboard" class="hover:text-blue-200 transition">Stats</router-link>
        <router-link to="/tags" class="hover:text-blue-200 transition">Tags</router-link>
        <router-link to="/tag-rules" class="hover:text-blue-200 transition">Rules</router-link>
        <router-link to="/job-logs" class="hover:text-blue-200 transition">Logs</router-link>
        <router-link to="/scheduled-jobs" class="hover:text-blue-200 transition">Jobs</router-link>
      </div>
      
      <!-- Admin Mobile links -->
      <div v-if="isAdmin" class="container mx-auto px-4 py-2 flex justify-between bg-purple-700">
        <router-link to="/keys" class="hover:text-purple-200 transition">Keys</router-link>
        <router-link to="/admin-settings" class="hover:text-purple-200 transition">Settings</router-link>
        <router-link to="/audit-logs" class="hover:text-purple-200 transition">Audit</router-link>
      </div>
    </div>
    
    <!-- Main Content -->
    <div class="flex-grow container mx-auto px-4 py-6">
      <header class="bg-white shadow">
        <div class="flex items-center justify-between max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <div class="flex items-center">
            <button 
              v-if="canGoBack"
              @click="goBack" 
              class="mr-3 text-gray-600 hover:text-gray-900 focus:outline-none"
              title="Go back"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <slot name="header"></slot>
          </div>
          <div class="flex items-center">
            <!-- User dropdown -->
          </div>
        </div>
      </header>
      <slot></slot>
    </div>
    
    <!-- Footer -->
    <footer class="bg-gray-800 text-white py-6">
      <div class="container mx-auto px-4">
        <div class="flex flex-col md:flex-row justify-between items-center">
          <div>
            <p class="text-sm">&copy; {{ new Date().getFullYear() }} NetRaven. All rights reserved.</p>
          </div>
          <div class="mt-4 md:mt-0">
            <p class="text-sm">Version 0.1.0</p>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
import { ref, computed, onMounted, onErrorCaptured, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../store/auth'

export default {
  name: 'MainLayout',
  props: {
    title: {
      type: String,
      default: ''
    }
  },
  setup(props) {
    const authStore = useAuthStore()
    const router = useRouter()
    const route = useRoute()
    
    const showUserMenu = ref(false)
    const layoutError = ref(null)
    const previousRoute = ref(null)
    
    const isAuthenticated = computed(() => authStore.isAuthenticated)
    const isAdmin = computed(() => authStore.hasRole('admin'))
    
    const username = computed(() => {
      try {
        if (!authStore.user) {
          // If we have a token but no user data, show a placeholder
          return hasToken.value ? 'User' : '';
        }
        return authStore.user.username || authStore.user.full_name || 'User';
      } catch (e) {
        console.error('Error computing username:', e);
        return 'User';
      }
    })
    
    const hasToken = computed(() => !!localStorage.getItem('access_token'))
    
    const currentRoute = computed(() => {
      try {
        // Extra safeguards around route access
        if (!route) return 'unknown';
        if (typeof route.path !== 'string') return 'unknown';
        return route.path;
      } catch (e) {
        console.error('MainLayout: Error getting current route:', e)
        return 'unknown'
      }
    })
    
    // Safer method to check if a route exists
    const routeExists = () => {
      try {
        return !!route && typeof route === 'object';
      } catch (e) {
        console.error('MainLayout: Error checking route existence:', e);
        return false;
      }
    }
    
    // Error handling
    onErrorCaptured((err, instance, info) => {
      console.error('MainLayout error captured:', err, info)
      
      // Special handling for navigation/route errors
      if (err.message && (
        err.message.includes('undefined (reading') || 
        err.message.includes('location') ||
        err.message.includes('route')
      )) {
        console.warn('MainLayout: Navigation error captured, handled locally:', err.message);
        return true; // Handle locally without propagating
      }
      
      // For other errors, display in the layout
      layoutError.value = `${err.message || 'Unknown error'}`
      return false // prevent error from propagating further
    })
    
    // Watch route changes with extra safety
    if (routeExists()) {
      watch(() => {
        try {
          return route.path;
        } catch (e) {
          console.error('MainLayout: Error in route watcher:', e);
          return 'unknown';
        }
      }, (newPath, oldPath) => {
        try {
          previousRoute.value = oldPath || 'unknown';
        } catch (e) {
          console.error('MainLayout: Error updating previous route:', e);
        }
      });
    }
    
    onMounted(async () => {
      console.log('MainLayout mounted');
      
      // If we have a token but no user data, fetch the user
      if (hasToken.value && !authStore.user) {
        try {
          console.log('MainLayout: Token found but no user data, fetching user');
          await authStore.fetchCurrentUser();
        } catch (err) {
          console.error('MainLayout: Failed to fetch user data on mount', err);
          
          // Only show error for non-404 responses
          if (err.response?.status !== 404) {
            layoutError.value = 'Failed to load user data';
          } else {
            console.log('MainLayout: User endpoint not found (404), continuing without user data');
            
            // Create a minimal user object when the endpoint is not available
            if (hasToken.value) {
              console.log('Setting minimal user data from token');
              const token = localStorage.getItem('access_token');
              try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                const username = payload.sub || 'User';
                authStore.user = { username };
              } catch (e) {
                console.error('Error extracting username from token:', e);
                authStore.user = { username: 'User' };
              }
            }
          }
          
          // Don't redirect on initial load to avoid disrupting the current flow
          // User can use the retry button if needed
        }
      }
    })
    
    const logout = () => {
      try {
        authStore.logout()
        router.push('/login')
      } catch (err) {
        console.error('Logout error:', err)
        // Force logout even if there's an error
        localStorage.removeItem('access_token')
        window.location.href = '/login'
      }
    }
    
    const retryLayout = async () => {
      layoutError.value = null;
      
      try {
        // Check if we have a token but no user data
        if (hasToken.value) {
          console.log('MainLayout: Retrying user data fetch');
          await authStore.fetchCurrentUser();
        } else {
          // If no token, redirect to login
          console.log('MainLayout: No token found, redirecting to login');
          router.push('/login');
        }
      } catch (err) {
        console.error('MainLayout: Retry failed', err);
        layoutError.value = 'Still having issues. Try logging out and back in.';
        
        // If we get a 401 error, redirect to login
        if (err.response?.status === 401) {
          console.log('MainLayout: Token invalid (401), redirecting to login');
          router.push('/login');
        }
      }
    }
    
    // Back navigation support
    const canGoBack = computed(() => {
      // Always show back button on detail pages
      return route.path.includes('/devices/') || 
             route.path.includes('/job-logs/') ||
             route.path.includes('/backups/');
    })
    
    const goBack = () => {
      router.back()
    }
    
    return {
      isAuthenticated,
      isAdmin,
      username,
      showUserMenu,
      logout,
      layoutError,
      retryLayout,
      hasToken,
      currentRoute,
      previousRoute,
      canGoBack,
      goBack
    }
  }
}
</script> 