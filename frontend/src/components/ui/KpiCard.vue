<template>
  <div class="nr-card flex flex-col justify-between h-full border-l-4 p-0" :class="borderColor">
    <div class="flex items-center justify-between pt-2 pl-3 pr-3">
      <span class="text-xs uppercase font-semibold text-text-secondary">{{ label }}</span>
      <span
        class="flex items-center justify-center w-7 h-7 rounded-full flex-shrink-0 flex-grow-0 basis-auto self-center max-w-[1.75rem] max-h-[1.75rem]"
        :class="iconBg"
        :title="statusLabel"
        aria-label="statusLabel"
      >
        <component :is="iconComponent" class="w-5 h-5" />
      </span>
    </div>
    <div class="text-base font-bold text-text-primary pb-2 pl-4 pr-3 mt-1">{{ value }}</div>
  </div>
</template>

<script setup>
import { h, computed } from 'vue'
const props = defineProps({
  label: String,
  value: [String, Number],
  icon: String,
  color: String // e.g., 'red', 'yellow', 'green', 'blue'
})
const icons = {
  healthy: {
    render() { return h('svg', { class: 'w-6 h-6', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [h('circle', { cx: '12', cy: '12', r: '10', stroke: 'currentColor', 'stroke-width': '2', fill: 'none' }), h('path', { d: 'M8 12l2 2 4-4', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })]) }
  },
  unhealthy: {
    render() { return h('svg', { class: 'w-6 h-6', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [h('circle', { cx: '12', cy: '12', r: '10', stroke: 'currentColor', 'stroke-width': '2', fill: 'none' }), h('path', { d: 'M15 9l-6 6M9 9l6 6', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })]) }
  },
  unknown: {
    render() { return h('svg', { class: 'w-6 h-6', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [h('circle', { cx: '12', cy: '12', r: '10', stroke: 'currentColor', 'stroke-width': '2', fill: 'none' }), h('text', { x: '12', y: '16', 'text-anchor': 'middle', 'font-size': '16', fill: 'currentColor' }, '?')]) }
  }
}
const statusKey = computed(() => {
  if (props.value && typeof props.value === 'string') {
    const v = props.value.toLowerCase()
    if (v === 'healthy') return 'healthy'
    if (v === 'unhealthy' || v === 'failed' || v === 'error') return 'unhealthy'
  }
  return 'unknown'
})
const iconComponent = computed(() => icons[statusKey.value])
const borderColor = computed(() => {
  if (props.color === 'red') return 'border-l-red-500'
  if (props.color === 'yellow') return 'border-l-yellow-500'
  if (props.color === 'green') return 'border-l-green-600'
  if (props.color === 'blue') return 'border-l-blue-500'
  return 'border-l-primary'
})
const iconBg = computed(() => {
  if (props.color === 'red') return 'bg-red-600'
  if (props.color === 'yellow') return 'bg-yellow-500'
  if (props.color === 'green') return 'bg-green-600'
  if (props.color === 'blue') return 'bg-blue-600'
  return 'bg-primary'
})
const statusLabel = computed(() => {
  if (statusKey.value === 'healthy') return 'Healthy'
  if (statusKey.value === 'unhealthy') return 'Unhealthy'
  return 'Unknown'
})
</script> 