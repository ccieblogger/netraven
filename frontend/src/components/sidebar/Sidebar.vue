<template>
  <nav class="h-full w-56 flex flex-col bg-sidebar border-r border-divider">
    <div class="flex items-center px-4 py-4">
      <router-link to="/" class="flex items-center space-x-2">
        <span class="text-xl font-semibold">
          <span class="text-primary">Net</span><span class="text-text-primary">Raven</span>
        </span>
      </router-link>
    </div>
    <div class="flex-1 overflow-y-auto">
      <SidebarNavGroup
        v-for="item in navConfig"
        :key="item.name"
        :item="item"
        :active-route="currentRoute"
      />
    </div>
    <SidebarUserSection />
  </nav>
</template>

<script setup>
import navConfig from './navConfig'
import SidebarNavGroup from './SidebarNavGroup.vue'
import SidebarUserSection from './SidebarUserSection.vue'
import { useRoute } from 'vue-router'
const currentRoute = useRoute().path
</script> 