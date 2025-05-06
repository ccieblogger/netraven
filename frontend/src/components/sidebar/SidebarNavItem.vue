<template>
  <div>
    <div v-if="isGroup" class="flex items-center gap-x-0 px-0 py-2 rounded cursor-pointer select-none hover:bg-card"
         :class="[paddingClass, { 'bg-card text-text-primary': isActive, 'text-text-secondary': !isActive }]"
         @click="$emit('toggle')">
      <component :is="item.icon" class="w-4 h-5" />
      <span class="truncate flex-1">{{ item.name }}</span>
      <span class="ml-auto">
        <svg v-if="isOpen" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M19 9l-7 7-7-7"/></svg>
        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7"/></svg>
      </span>
    </div>
    <router-link v-else :to="item.path" class="flex items-center gap-x-0 px-0 py-2 rounded hover:bg-card"
      :class="[paddingClass, { 'bg-card text-text-primary': isActive, 'text-text-secondary': !isActive }]">
      <component :is="item.icon" class="w-4 h-5" />
      <span class="truncate">{{ item.name }}</span>
    </router-link>
  </div>
</template>

<script setup>
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

// Compute padding class based on level
const paddingClass = `pl-${props.level * 4}`
</script> 