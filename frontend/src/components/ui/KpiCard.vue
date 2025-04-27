<template>
  <div class="nr-card flex flex-col justify-between h-full border-l-4 p-0" :class="borderColor">
    <div class="flex items-start justify-between pt-3 pl-4 pr-4">
      <span class="text-sm uppercase font-semibold text-text-secondary">{{ label }}</span>
      <span class="flex items-center justify-center h-9 w-9 rounded-md" :class="iconBg">
        <component :is="iconComponent" class="w-6 h-6 text-white" />
      </span>
    </div>
    <div class="text-2xl font-bold text-text-primary pb-3 pl-6 pr-4 mt-2">{{ value }}</div>
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
  status: {
    render() { return h('svg', { class: 'w-6 h-6', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [h('circle', { cx: '12', cy: '12', r: '10', stroke: 'currentColor', 'stroke-width': '2', fill: 'currentColor' })]) }
  },
  clock: {
    render() { return h('svg', { class: 'w-6 h-6', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [h('circle', { cx: '12', cy: '12', r: '10', stroke: 'currentColor', 'stroke-width': '2' }), h('path', { d: 'M12 6v6l4 2', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })]) }
  },
  memory: {
    render() { return h('svg', { class: 'w-6 h-6', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [h('rect', { x: '4', y: '8', width: '16', height: '8', rx: '2', fill: 'currentColor' })]) }
  },
  list: {
    render() { return h('svg', { class: 'w-6 h-6', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [h('path', { d: 'M4 6h16M4 12h16M4 18h7', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })]) }
  },
  queue: {
    render() { return h('svg', { class: 'w-6 h-6', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [h('rect', { x: '4', y: '4', width: '16', height: '16', rx: '2', fill: 'currentColor' })]) }
  },
  'user-group': {
    render() { return h('svg', { class: 'w-6 h-6', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [h('circle', { cx: '9', cy: '7', r: '4', stroke: 'currentColor', 'stroke-width': '2' }), h('circle', { cx: '17', cy: '7', r: '4', stroke: 'currentColor', 'stroke-width': '2' }), h('rect', { x: '2', y: '15', width: '20', height: '6', rx: '3', fill: 'currentColor' })]) }
  },
  progress: {
    render() { return h('svg', { class: 'w-6 h-6', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [h('circle', { cx: '12', cy: '12', r: '10', stroke: 'currentColor', 'stroke-width': '2' }), h('path', { d: 'M12 6v6l4 2', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })]) }
  }
}
const iconComponent = computed(() => icons[props.icon] || icons.status)
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
</script> 