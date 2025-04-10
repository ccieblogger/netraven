<template>
  <div class="flex h-screen bg-[#0D1321]">
    <!-- Sidebar -->
    <aside :class="[
      'h-screen flex-shrink-0 flex flex-col transition-all duration-300 bg-[#0D1321] border-r border-gray-700',
      isSidebarOpen ? 'w-64' : 'w-16'
    ]">
      <!-- Sidebar header with logo -->
      <div class="flex items-center justify-between px-4 py-4">
        <router-link to="/" class="flex items-center space-x-2">
          <span v-if="isSidebarOpen" class="text-lg font-semibold">
            <span class="text-green-500">Net</span><span class="text-white">Raven</span>
          </span>
          <span v-else class="text-lg font-semibold">
            <span class="text-green-500">N</span>
          </span>
        </router-link>
        <button @click="toggleSidebar" class="text-gray-400 hover:text-white focus:outline-none">
          <svg v-if="isSidebarOpen" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M15 19l-7-7 7-7" />
          </svg>
          <svg v-else class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-2 py-4 space-y-2">
        <router-link 
          v-for="item in navigation" 
          :key="item.name"
          :to="item.path" 
          class="group flex items-center gap-4 px-2 py-2 text-sm font-medium transition-colors duration-150 ease-in-out"
          :class="[
            $route.path.startsWith(item.path) 
              ? 'text-white bg-[#19253D] border-l-4 border-blue-500 pl-1' 
              : 'text-gray-400 hover:text-white hover:bg-[#19253D] border-l-4 border-transparent'
          ]"
        >
          <div v-html="item.icon.template" class="w-5 h-5 flex-shrink-0" 
               :class="{ 
                 'text-gray-400': !$route.path.startsWith(item.path),
                 'text-green-500': $route.path.startsWith(item.path)
               }"></div>
          <span v-if="isSidebarOpen" class="truncate">{{ item.name }}</span>
        </router-link>
      </nav>

      <!-- User account -->
      <div class="p-4 mt-auto border-t border-gray-700">
        <div class="flex items-center gap-4" :class="{ 'justify-center': !isSidebarOpen }">
          <div class="flex-shrink-0">
            <div class="h-12 w-12 rounded-full bg-green-500 flex items-center justify-center text-white font-medium text-xl">
              A
            </div>
          </div>
          <div v-if="isSidebarOpen">
            <p class="text-base font-medium text-white">admin</p>
          </div>
        </div>
        
        <div v-if="isSidebarOpen" class="mt-5">
          <button 
            @click="authStore.logout" 
            class="w-full flex items-center gap-4 px-3 py-2 text-sm font-medium text-gray-300 hover:text-white group"
          >
            <svg class="h-5 w-5 text-gray-400 group-hover:text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
            Logout
          </button>
        </div>
        <div v-else class="mt-3 flex justify-center">
          <button 
            @click="authStore.logout" 
            class="p-2 text-gray-400 rounded-md hover:bg-[#19253D] hover:text-white"
          >
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
          </button>
        </div>
      </div>
    </aside>

    <!-- Main content -->
    <div class="flex flex-col flex-1 overflow-hidden">
      <!-- Main content header -->
      <header class="sticky top-0 z-10 flex items-center justify-between h-16 bg-[#101B2D] border-b border-gray-700 px-4">
        <div class="flex flex-col">
          <h1 class="text-xl font-semibold">
            <span class="text-green-500">Welcome to</span> <span class="text-white">NetRaven</span>
          </h1>
          <p class="text-sm text-gray-400">Network Configuration Management System</p>
        </div>
        <div class="flex items-center space-x-4">
          <button class="p-1 text-gray-400 rounded-full hover:text-white focus:outline-none">
            <BellIcon class="w-6 h-6" />
          </button>
          <!-- Mobile menu button (only visible on small screens) -->
          <button class="p-1 text-gray-400 rounded-full lg:hidden hover:text-white focus:outline-none">
            <Bars3Icon class="w-6 h-6" />
          </button>
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1 overflow-y-auto bg-[#141E32] p-6">
        <slot></slot>
      </main>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '../store/auth';
import NotificationToast from '../components/NotificationToast.vue';
import { ref } from 'vue';
import { Disclosure, DisclosureButton, DisclosurePanel } from '@headlessui/vue';
import { ChevronDownIcon, BellIcon, Bars3Icon, XMarkIcon } from '@heroicons/vue/24/outline';

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
    name: 'Jobs', 
    path: '/jobs', 
    icon: {
      template: `<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>`
    } 
  },
  { 
    name: 'Credentials', 
    path: '/credentials', 
    icon: {
      template: `<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
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
  },
  { 
    name: 'Settings', 
    path: '/settings', 
    icon: {
      template: `<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>`
    } 
  }
];

const isSidebarOpen = ref(true);
const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value;
};
</script>

<style>
/* Removing global styles in favor of inline Tailwind classes */
</style> 