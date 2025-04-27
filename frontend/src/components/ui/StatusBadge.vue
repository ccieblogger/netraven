<template>
  <span class="relative inline-flex items-center justify-center" @mouseenter="show = true" @mouseleave="show = false" @focusin="show = true" @focusout="show = false" tabindex="0">
    <slot />
    <transition name="fade">
      <div v-if="show" class="absolute z-50 left-1/2 -translate-x-1/2 mt-2 min-w-max bg-gray-900 text-white text-xs rounded-lg shadow-lg px-3 py-2 pointer-events-none" role="tooltip">
        <slot name="popover" />
      </div>
    </transition>
  </span>
</template>

<script setup>
import { ref } from 'vue'
const show = ref(false)
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.15s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style> 