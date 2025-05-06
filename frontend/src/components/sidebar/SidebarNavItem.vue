<template>
  <div :class="paddingClass">
    <div v-if="isGroup" class="flex items-center py-2 rounded cursor-pointer select-none hover:bg-card"
         :class="{ 'bg-card text-text-primary': isActive, 'text-text-secondary': !isActive }"
         @click="$emit('toggle')">
      <component :is="item.icon" class="w-4 h-4" />
      <span class="truncate flex-1 text-sm">{{ item.name }}</span>
      <span class="ml-auto">
        <svg v-if="isOpen" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M19 9l-7 7-7-7"/></svg>
        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7"/></svg>
      </span>
    </div>
    <router-link v-else :to="item.path" class="flex items-center py-2 rounded hover:bg-card"
      :class="{ 'bg-card text-text-primary': isActive, 'text-text-secondary': !isActive }">
      <component :is="item.icon" class="w-4 h-4" />
      <span class="truncate text-sm">{{ item.name }}</span>
    </router-link>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({
  item: Object,
  activeRoute: String,
  isGroup: Boolean,
  isOpen: Boolean,
  level: {
    type: Number,
    default: 0
  }
})
const isActive = props.activeRoute && props.item.path && props.activeRoute.startsWith(props.item.path)

// Static mapping for Tailwind padding classes
const paddingMap = {
  0: 'pl-0',
  1: 'pl-4',
  2: 'pl-8',
  3: 'pl-12'
}
const paddingClass = computed(() => paddingMap[props.level] || 'pl-18')
</script> 