<template>
  <div class="flex h-screen overflow-hidden">
    <!-- Sidebar -->
    <aside class="h-screen w-sidebar flex-shrink-0 flex flex-col bg-sidebar border-r border-divider">
      <!-- Sidebar header with logo -->
      <div class="flex items-center px-4 py-4">
        <router-link to="/" class="flex items-center space-x-2">
          <span class="text-xl font-semibold">
            <span class="text-primary">Net</span><span class="text-text-primary">Raven</span>
          </span>
        </router-link>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-2 py-4 space-y-1">
        <router-link 
          v-for="item in navigation" 
          :key="item.name"
          :to="item.path" 
          class="group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-150 ease-in-out"
          :class="[
            $route.path.startsWith(item.path) 
              ? 'text-text-primary bg-card border-l-4 border-primary pl-2' 
              : 'text-text-secondary hover:text-text-primary hover:bg-card border-l-4 border-transparent'
          ]"
        >
          <div v-html="item.icon.template" class="w-5 h-5 flex-shrink-0 mr-3" 
               :class="{ 
                 'text-text-secondary': !$route.path.startsWith(item.path),
                 'text-primary': $route.path.startsWith(item.path)
               }"></div>
          <span class="truncate">{{ item.name }}</span>
        </router-link>
      </nav>

      <!-- User account -->
      <div class="p-4 mt-auto border-t border-divider">
        <div class="flex items-center gap-3">
          <div class="flex-shrink-0">
            <div class="h-9 w-9 rounded-full bg-primary flex items-center justify-center text-white font-medium text-lg">
              A
            </div>
          </div>
          <div>
            <p class="text-sm font-medium text-text-primary">{{ authStore.user?.username || 'admin' }}</p>
          </div>
        </div>
        
        <!-- Theme Switcher -->
        <div class="mt-3 pb-3">
          <ThemeSwitcher />
        </div>
        
        <div class="mt-2">
          <button 
            @click="authStore.logout" 
            class="w-full flex items-center gap-2 px-3 py-2 text-sm font-medium text-text-secondary hover:text-text-primary rounded-md hover:bg-card group"
          >
            <svg class="h-5 w-5 text-text-secondary group-hover:text-text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
            Logout
          </button>
        </div>
      </div>
    </aside>

    <!-- Main content -->
    <div class="flex flex-col flex-1 overflow-hidden">
      <!-- Main content header -->
      <header class="sticky top-0 z-10 flex items-center justify-between h-16 bg-sidebar border-b border-divider px-4">
        <div class="flex flex-col">
          <h1 class="text-xl font-semibold">
            <span class="text-primary">Welcome to</span> <span class="text-text-primary">NetRaven</span>
          </h1>
          <p class="text-sm text-text-secondary">Network Configuration Management System</p>
        </div>
        <div class="flex items-center space-x-4">
          <button class="p-1 text-text-secondary rounded-full hover:text-text-primary focus:outline-none">
            <BellIcon class="w-6 h-6" />
          </button>
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1 overflow-y-auto bg-content p-6">
        <slot></slot>
      </main>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '../store/auth';
import { BellIcon } from '@heroicons/vue/24/outline';
import ThemeSwitcher from '../components/ui/ThemeSwitcher.vue';

const authStore = useAuthStore();

const navigation = [
  { 
    name: 'Dashboard', 
    path: '/dashboard', 
    icon: {
      template: `<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="3" y="3" width="7" height="7" />
        <rect x="14" y="3" width="7" height="7" />
        <rect x="14" y="14" width="7" height="7" />
        <rect x="3" y="14" width="7" height="7" />
      </svg>`
    }
  },
  { 
    name: 'Devices', 
    path: '/devices', 
    icon: {
      template: `<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
        <line x1="8" y1="21" x2="16" y2="21" />
        <line x1="12" y1="17" x2="12" y2="21" />
      </svg>`
    } 
  },
  { 
    name: 'Tags', 
    path: '/tags', 
    icon: {
      template: `<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M7 7h.01M7 3h5a1.99 1.99 0 0 1 1.414.586l7 7a2 2 0 0 1 0 2.828l-7 7a2 2 0 0 1-2.828 0l-7-7A1.99 1.99 0 0 1 3 12V7a4 4 0 0 1 4-4z" />
      </svg>`
    } 
  },
  { 
    name: 'Credentials', 
    path: '/credentials', 
    icon: {
      template: `<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M15 7a2 2 0 0 1 2 2m4 0a6 6 0 0 1-7.743 5.743L11 17H9v2H7v2H4a1 1 0 0 1-1-1v-2.586a1 1 0 0 1 .293-.707l5.964-5.964A6 6 0 0 1 21 9z" />
      </svg>`
    } 
  },
  { 
    name: 'Jobs', 
    path: '/jobs', 
    icon: {
      template: `<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2" />
      </svg>`
    } 
  },
  { 
    name: 'Config Diff', 
    path: '/config-diff', 
    icon: {
      template: `<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 2v20M2 6h4m-2 4h2m14-4h4m-2 4h2M2 14h2m-2 4h4M18 14h2m-2 4h4" />
      </svg>`
    } 
  },
  { 
    name: 'Logs', 
    path: '/logs', 
    icon: {
      template: `<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 10v6M12 10l4-4M12 16l4 4M12 10l-4-4M12 16l-4 4" />
      </svg>`
    } 
  },
  { 
    name: 'Users', 
    path: '/users', 
    icon: {
      template: `<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
        <circle cx="9" cy="7" r="4"></circle>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
        <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
      </svg>`
    } 
  }
];
</script>

<style>
/* Removing global styles in favor of inline Tailwind classes */
</style> 