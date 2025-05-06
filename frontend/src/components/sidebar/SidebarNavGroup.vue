<template>
  <div>
    <SidebarNavItem
      :item="item"
      :active-route="activeRoute"
      :is-group="!!item.children"
      :is-open="isOpen"
      @toggle="toggleOpen"
    />
    <div v-if="item.children && isOpen" class="ml-4 flex flex-col">
      <SidebarNavItem
        v-for="child in item.children"
        :key="child.name"
        :item="child"
        :active-route="activeRoute"
        class="mt-1"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SidebarNavItem from './SidebarNavItem.vue'
const props = defineProps(['item', 'activeRoute'])
const isOpen = ref(false)
function toggleOpen() { isOpen.value = !isOpen.value }
</script> 