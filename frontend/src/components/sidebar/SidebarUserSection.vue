<template>
  <div class="p-4 mt-auto border-t border-divider">
    <div class="flex items-center gap-3">
      <div class="flex-shrink-0">
        <template v-if="user.value?.avatar">
          <img :src="user.value.avatar" class="h-9 w-9 rounded-full object-cover" alt="User avatar" />
        </template>
        <template v-else>
          <div class="w-9 h-9 min-w-9 min-h-9 aspect-square rounded-full bg-primary inline-flex items-center justify-center overflow-hidden text-white font-semibold text-base">
            {{ userInitials }}
          </div>
        </template>
      </div>
      <div>
        <p class="text-sm font-medium text-text-primary">{{ displayUsername }}</p>
      </div>
    </div>
    <div class="mt-3 pb-3">
      <label class="block text-xs text-text-secondary mb-1">Theme</label>
      <Dropdown
        v-model="themeStore.currentTheme"
        :options="themeOptions"
        optionLabel="label"
        optionValue="value"
        class="w-full text-xs"
        inputClass="bg-card text-white text-xs h-8 px-2"
        panelClass="bg-card text-white text-xs"
        dropdownIcon="pi pi-chevron-down text-white"
        :dropdownClass="'bg-card text-white'"
        @change="onThemeChange"
        placeholder="Select Theme"
      />
    </div>
    <div class="mt-2">
      <button class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-text-secondary hover:text-text-primary rounded-md hover:bg-card group justify-start"
        @click="logout">
        <svg class="h-5 w-5 text-text-secondary group-hover:text-text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
          <polyline points="16 17 21 12 16 7"></polyline>
          <line x1="21" y1="12" x2="9" y2="12"></line>
        </svg>
        Logout
      </button>
    </div>
  </div>
</template>

<script setup>
import { useThemeStore } from '../../store/theme'
import Dropdown from 'primevue/dropdown'
import { useRouter } from 'vue-router'
import { computed } from 'vue'
import { useAuthStore } from '../../store/auth'
const themeStore = useThemeStore()
const router = useRouter()
const themeOptions = themeStore.availableThemes.map(theme => ({
  label: theme.charAt(0).toUpperCase() + theme.slice(1),
  value: theme
}))

const authStore = useAuthStore()
const user = computed(() => authStore.user)
const userInitials = computed(() => {
  if (!user.value?.username) return '?'
  return user.value.username[0].toUpperCase()
})

const displayUsername = computed(() => {
  return user.value && user.value.username ? user.value.username : 'User'
})

function onThemeChange(e) {
  themeStore.setTheme(e.value)
}
function logout() {
  localStorage.removeItem('netraven-token')
  // Optionally clear other user/session data here
  authStore.logout()
}
</script> 