<template>
  <div class="min-h-screen flex flex-col bg-gray-100">
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
            <router-link to="/tags" class="hover:text-blue-200 transition">Tags</router-link>
            <router-link to="/tag-rules" class="hover:text-blue-200 transition">Tag Rules</router-link>
          </div>
          
          <div class="relative">
            <button @click="showUserMenu = !showUserMenu" class="flex items-center space-x-2 hover:text-blue-200">
              <span>{{ username }}</span>
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
        <router-link to="/tags" class="hover:text-blue-200 transition">Tags</router-link>
        <router-link to="/tag-rules" class="hover:text-blue-200 transition">Rules</router-link>
      </div>
    </div>
    
    <!-- Main Content -->
    <div class="flex-grow container mx-auto px-4 py-6">
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'

export default {
  name: 'MainLayout',
  
  setup() {
    const authStore = useAuthStore()
    const router = useRouter()
    const showUserMenu = ref(false)
    
    const isAuthenticated = computed(() => authStore.isAuthenticated)
    const username = computed(() => {
      if (!authStore.user) return ''
      return authStore.user.username || authStore.user.full_name || 'User'
    })
    
    onMounted(async () => {
      if (isAuthenticated.value && !authStore.user) {
        await authStore.fetchCurrentUser()
      }
    })
    
    const logout = () => {
      authStore.logout()
      router.push('/login')
    }
    
    return {
      isAuthenticated,
      username,
      showUserMenu,
      logout
    }
  }
}
</script> 