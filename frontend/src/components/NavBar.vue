<template>
  <nav class="bg-blue-800 border-b border-gray-700">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <div class="flex">
          <div class="flex-shrink-0 flex items-center">
            <img class="h-8 w-8" src="/logo.svg" alt="NetRaven Logo" />
            <span class="ml-2 text-xl font-bold text-white">NetRaven</span>
          </div>
          <div class="hidden sm:ml-6 sm:flex sm:items-center">
            <div class="flex space-x-4">
              <template v-for="item in navigationItems" :key="item.name">
                <div v-if="item.children" class="relative group">
                  <span class="text-gray-300 px-3 py-2 rounded-md text-sm font-medium cursor-default group-hover:text-white">{{ item.name }}</span>
                  <div class="ml-4 flex flex-col">
                    <router-link
                      v-for="child in item.children"
                      :key="child.name"
                      :to="child.href"
                      :class="[
                        $route.path === child.href
                          ? 'bg-blue-900 text-white'
                          : 'text-gray-300 hover:bg-blue-900 hover:text-white',
                        'px-3 py-2 rounded-md text-sm font-medium mt-1'
                      ]"
                    >
                      {{ child.name }}
                    </router-link>
                  </div>
                </div>
                <router-link
                  v-else
                  :to="item.href"
                  :class="[
                    $route.path === item.href
                      ? 'bg-blue-900 text-white'
                      : 'text-gray-300 hover:bg-blue-900 hover:text-white',
                    'px-3 py-2 rounded-md text-sm font-medium'
                  ]"
                >
                  {{ item.name }}
                </router-link>
              </template>
            </div>
          </div>
        </div>
        <div class="hidden sm:ml-6 sm:flex sm:items-center">
          <!-- Profile dropdown -->
          <div class="ml-3 relative">
            <div>
              <button
                type="button"
                class="bg-blue-800 flex text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-blue-800 focus:ring-white"
                id="user-menu-button"
                @click="toggleProfileMenu"
              >
                <span class="sr-only">Open user menu</span>
                <img
                  class="h-8 w-8 rounded-full"
                  src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80"
                  alt=""
                />
              </button>
            </div>

            <div
              v-if="isProfileMenuOpen"
              class="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white ring-1 ring-black ring-opacity-5 focus:outline-none"
              role="menu"
              aria-orientation="vertical"
              aria-labelledby="user-menu-button"
              tabindex="-1"
            >
              <a
                href="#"
                class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                role="menuitem"
                tabindex="-1"
                id="user-menu-item-0"
                >Your Profile</a
              >
              <a
                href="#"
                class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                role="menuitem"
                tabindex="-1"
                id="user-menu-item-1"
                >Settings</a
              >
              <a
                href="#"
                class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                role="menuitem"
                tabindex="-1"
                id="user-menu-item-2"
                @click="logout"
                >Sign out</a
              >
            </div>
          </div>
        </div>
        <div class="-mr-2 flex items-center sm:hidden">
          <!-- Mobile menu button -->
          <button
            type="button"
            class="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-white hover:bg-blue-900 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
            aria-controls="mobile-menu"
            :aria-expanded="isMobileMenuOpen"
            @click="toggleMobileMenu"
          >
            <span class="sr-only">Open main menu</span>
            <svg
              v-if="!isMobileMenuOpen"
              class="block h-6 w-6"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
            <svg
              v-else
              class="block h-6 w-6"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile menu -->
    <div
      v-if="isMobileMenuOpen"
      class="sm:hidden bg-blue-800"
      id="mobile-menu"
    >
      <div class="px-2 pt-2 pb-3 space-y-1">
        <router-link
          v-for="item in navigationItems"
          :key="item.name"
          :to="item.href"
          :class="[
            $route.path === item.href
              ? 'bg-blue-900 text-white'
              : 'text-gray-300 hover:bg-blue-900 hover:text-white',
            'block px-3 py-2 rounded-md text-base font-medium'
          ]"
        >
          {{ item.name }}
        </router-link>
      </div>
      <div class="pt-4 pb-3 border-t border-gray-700">
        <div class="flex items-center px-5">
          <div class="flex-shrink-0">
            <img
              class="h-10 w-10 rounded-full"
              src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80"
              alt=""
            />
          </div>
          <div class="ml-3">
            <div class="text-base font-medium text-white">Tom Cook</div>
            <div class="text-sm font-medium text-gray-400">tom@example.com</div>
          </div>
        </div>
        <div class="mt-3 px-2 space-y-1">
          <a
            href="#"
            class="block px-3 py-2 rounded-md text-base font-medium text-gray-400 hover:text-white hover:bg-blue-900"
            >Your Profile</a
          >
          <a
            href="#"
            class="block px-3 py-2 rounded-md text-base font-medium text-gray-400 hover:text-white hover:bg-blue-900"
            >Settings</a
          >
          <a
            href="#"
            class="block px-3 py-2 rounded-md text-base font-medium text-gray-400 hover:text-white hover:bg-blue-900"
            @click="logout"
            >Sign out</a
          >
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const isProfileMenuOpen = ref(false);
const isMobileMenuOpen = ref(false);

const navigationItems = [
  { name: 'Dashboard', href: '/' },
  {
    name: 'Jobs',
    children: [
      { name: 'Job Status Dashboard', href: '/jobs-dashboard' },
      { name: 'List', href: '/jobs' },
    ]
  },
  { name: 'Devices', href: '/devices' },
  { name: 'Tags', href: '/tags' },
  { name: 'Credentials', href: '/credentials' },
  { name: 'Backups', href: '/backups' },
  { name: 'Users', href: '/users' },
  { name: 'Logs', href: '/logs' },
  { name: 'System Status', href: '/system-status' },
];

function toggleProfileMenu() {
  isProfileMenuOpen.value = !isProfileMenuOpen.value;
}

function toggleMobileMenu() {
  isMobileMenuOpen.value = !isMobileMenuOpen.value;
}

function logout() {
  // Implement logout logic here
  // For example: clear token from localStorage
  localStorage.removeItem('token');
  router.push('/login');
}
</script> 