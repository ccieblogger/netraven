<template>
  <div>
    <SidebarNavItem
      :item="item"
      :active-route="activeRoute"
      :is-group="!!item.children"
      :is-open="isOpen"
      :level="level"
      @toggle="toggleOpen"
    />
    <div v-if="item.children && isOpen" class="flex flex-col">
      <SidebarNavGroup
        v-for="child in item.children"
        :key="child.name"
        :item="child"
        :active-route="activeRoute"
        :level="level + 1"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SidebarNavItem from './SidebarNavItem.vue'
import SidebarNavGroup from './SidebarNavGroup.vue'
const props = defineProps({
  item: Object,
  activeRoute: String,
  level: {
    type: Number,
    default: 0
  }
})
const isOpen = ref(false)
function toggleOpen() { isOpen.value = !isOpen.value }
</script> 