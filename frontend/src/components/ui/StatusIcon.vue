<template>
  <span
    class="relative inline-flex items-center justify-center cursor-pointer focus:outline-none"
    tabindex="0"
    @mouseenter="show = true"
    @mouseleave="show = false"
    @focusin="show = true"
    @focusout="show = false"
    :aria-label="ariaLabel"
    role="status"
  >
    <i :class="iconClass" :style="iconStyle" aria-hidden="true"></i>
    <transition name="fade">
      <div
        v-if="show && tooltipText"
        class="absolute z-50 left-1/2 -translate-x-1/2 mt-2 min-w-max bg-gray-900 text-white text-xs rounded-lg shadow-lg px-3 py-2 pointer-events-none"
        role="tooltip"
      >
        <span>{{ tooltipText }}</span>
      </div>
    </transition>
  </span>
</template>

<script setup>
import { ref, computed } from 'vue'
const props = defineProps({
  status: {
    type: String,
    default: 'unknown',
  },
  tooltip: {
    type: String,
    default: '',
  },
})
const show = ref(false)
const iconMap = {
  healthy: { icon: 'pi pi-check-circle', color: '#22c55e' }, // green-500
  unhealthy: { icon: 'pi pi-times-circle', color: '#ef4444' }, // red-500
  warning: { icon: 'pi pi-exclamation-triangle', color: '#f59e42' }, // yellow-500
  unknown: { icon: 'pi pi-question-circle', color: '#6b7280' }, // gray-500
}
const iconClass = computed(() => {
  const entry = iconMap[props.status] || iconMap.unknown
  return `${entry.icon} text-base` // text-base for sizing
})
const iconStyle = computed(() => {
  const entry = iconMap[props.status] || iconMap.unknown
  return { color: entry.color }
})
const tooltipText = computed(() => props.tooltip || {
  healthy: 'Reachable',
  unhealthy: 'Unreachable',
  warning: 'Warning',
  unknown: 'Unknown',
}[props.status] || 'Unknown')
const ariaLabel = computed(() => tooltipText.value)
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.15s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style> 