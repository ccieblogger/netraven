<template>
  <div class="flex h-screen bg-gray-100">
    <!-- Sidebar Navigation -->
    <nav class="bg-gray-800 text-white w-64 flex-shrink-0 hidden md:block">
      <div class="p-4">
        <h1 class="text-xl font-semibold">NetRaven</h1>
      </div>
      <div class="py-4">
        <router-link 
          to="/" 
          class="block px-4 py-2 hover:bg-gray-700"
          :class="{ 'bg-gray-700': $route.path === '/' }"
        >
          Dashboard
        </router-link>
        <router-link 
          to="/devices" 
          class="block px-4 py-2 hover:bg-gray-700"
          :class="{ 'bg-gray-700': $route.path.startsWith('/devices') }"
        >
          Devices
        </router-link>
        <router-link 
          to="/backups" 
          class="block px-4 py-2 hover:bg-gray-700"
          :class="{ 'bg-gray-700': $route.path.startsWith('/backups') }"
        >
          Backups
        </router-link>
        <router-link 
          to="/scheduled-jobs" 
          class="block px-4 py-2 hover:bg-gray-700"
          :class="{ 'bg-gray-700': $route.path.startsWith('/scheduled-jobs') }"
        >
          Scheduled Jobs
        </router-link>
        <router-link 
          to="/job-logs" 
          class="block px-4 py-2 hover:bg-gray-700"
          :class="{ 'bg-gray-700': $route.path.startsWith('/job-logs') }"
        >
          Job Logs
        </router-link>
        <router-link 
          to="/tags" 
          class="block px-4 py-2 hover:bg-gray-700"
          :class="{ 'bg-gray-700': $route.path.startsWith('/tags') }"
        >
          Tags
        </router-link>
        <router-link 
          to="/tag-rules" 
          class="block px-4 py-2 hover:bg-gray-700"
          :class="{ 'bg-gray-700': $route.path.startsWith('/tag-rules') }"
        >
          Tag Rules
        </router-link>
        <router-link 
          to="/gateway" 
          class="block px-4 py-2 hover:bg-gray-700"
          :class="{ 'bg-gray-700': $route.path.startsWith('/gateway') }"
        >
          Gateway
        </router-link>
        
        <!-- Credentials Section -->
        <div class="mt-4 pt-4 border-t border-gray-700">
          <div class="px-4 py-2 text-gray-400 text-sm">Credentials</div>
          <router-link 
            to="/credentials" 
            class="block px-4 py-2 hover:bg-gray-700"
            :class="{ 'bg-gray-700': $route.path === '/credentials' }"
          >
            <div class="flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              Manage Credentials
            </div>
          </router-link>
          <router-link 
            to="/credentials/dashboard" 
            class="block px-4 py-2 hover:bg-gray-700"
            :class="{ 'bg-gray-700': $route.path === '/credentials/dashboard' }"
          >
            <div class="flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Basic Dashboard
            </div>
          </router-link>
          <router-link 
            to="/credentials/analytics" 
            class="block px-4 py-2 hover:bg-gray-700"
            :class="{ 'bg-gray-700': $route.path === '/credentials/analytics' }"
          >
            <div class="flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              Advanced Analytics
            </div>
          </router-link>
        </div>
        
        <!-- Admin Section -->
        <div v-if="isAdmin" class="mt-4 pt-4 border-t border-gray-700">
          <div class="px-4 py-2 text-gray-400 text-sm">Administration</div>
          <router-link 
            to="/keys" 
            class="block px-4 py-2 hover:bg-gray-700"
            :class="{ 'bg-gray-700': $route.path.startsWith('/keys') }"
          >
            <div class="flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
              </svg>
              Key Management
            </div>
          </router-link>
        </div>
      </div>
    </nav>
    
    <!-- Main Content -->
    <div class="flex-1 overflow-auto">
      <div class="container mx-auto p-6">
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue';
import { useAuthStore } from '../../store/auth';

export default {
  name: 'MainLayout',

  setup() {
    const authStore = useAuthStore();
    
    const isAdmin = computed(() => {
      return authStore.hasRole('admin');
    });

    return {
      isAdmin
    };
  }
}
</script> 