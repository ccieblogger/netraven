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
    <span
      :class="[
        'w-3 h-3 rounded-full border-2 border-white shadow',
        statusColor,
        'inline-block mr-2 transition-colors duration-150'
      ]"
      aria-hidden="true"
    ></span>
    <span class="text-xs text-text-secondary select-none">{{ label }}</span>
    <transition name="fade">
      <div
        v-if="show"
        class="absolute z-50 left-1/2 -translate-x-1/2 mt-2 min-w-max bg-gray-900 text-white text-xs rounded-lg shadow-lg px-3 py-2 pointer-events-none"
        role="tooltip"
      >
        <slot name="tooltip">
          <span>{{ tooltipText }}</span>
        </slot>
      </div>
    </transition>
  </span>
</template>

<script setup>
import { ref, computed } from 'vue'
const props = defineProps({
  status: {
    type: String,
    default: 'unknown', // healthy, unhealthy, unknown
  },
  label: {
    type: String,
    required: true,
  },
  tooltip: {
    type: String,
    default: '',
  },
})
const show = ref(false)
const statusColor = computed(() => {
  switch (props.status) {
    case 'healthy':
      return 'bg-green-500'
    case 'unhealthy':
      return 'bg-red-500'
    case 'warning':
      return 'bg-yellow-400'
    default:
      return 'bg-gray-400'
  }
})
const tooltipText = computed(() => {
  if (props.tooltip) return props.tooltip
  if (props.status === 'healthy') return 'Healthy'
  if (props.status === 'unhealthy') return 'Unhealthy'
  if (props.status === 'warning') return 'Warning'
  return 'Unknown'
})
const ariaLabel = computed(() => `${props.label}: ${tooltipText.value}`)
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.15s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style> 