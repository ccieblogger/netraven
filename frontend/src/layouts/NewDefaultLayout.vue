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
          <img src="../assets/logo.png" alt="Logo" class="h-8 w-auto" />
          <span v-if="isSidebarOpen" class="text-lg font-semibold text-white">NetRaven</span>
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
      <nav class="flex-1 px-2 py-4 space-y-1">
        <router-link 
          v-for="item in navigation" 
          :key="item.name"
          :to="item.path" 
          class="group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors duration-150 ease-in-out"
          :class="[
            $route.path.startsWith(item.path) 
              ? 'text-white bg-[#19253D] border-l-4 border-blue-500' 
              : 'text-gray-400 hover:text-white hover:bg-[#19253D]'
          ]"
        >
          <div v-html="item.icon.template" class="mr-3" 
               :class="{ 
                 'ml-1': !$route.path.startsWith(item.path),
                 'text-green-500': $route.path.startsWith(item.path)
               }"></div>
          <span v-if="isSidebarOpen" class="truncate">{{ item.name }}</span>
        </router-link>
      </nav>

      <!-- User account -->
      <div class="p-4 border-t border-gray-700">
        <div class="flex items-center space-x-3" :class="{ 'justify-center': !isSidebarOpen }">
          <img
            class="h-9 w-9 rounded-full"
            src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80"
            alt="User avatar"
          />
          <div v-if="isSidebarOpen">
            <p class="text-sm font-medium text-white">Admin User</p>
            <button 
              @click="authStore.logout" 
              class="text-xs text-gray-400 hover:text-white"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main content -->
    <div class="flex flex-col flex-1 overflow-hidden">
      <!-- Main content header -->
      <header class="sticky top-0 z-10 flex items-center justify-between h-16 bg-[#101B2D] border-b border-gray-700 px-4">
        <div class="flex items-center">
          <h1 class="text-xl font-semibold text-white">Dashboard</h1>
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
        <router-view />
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