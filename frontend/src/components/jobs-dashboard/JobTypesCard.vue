<template>
  <div class="flex flex-wrap gap-2 items-center mb-4">
    <template v-for="type in jobTypes" :key="type.job_type">
      <button
        class="flex items-center gap-2 px-4 py-2 rounded-full font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400"
        :class="selectedType === type.job_type ? 'bg-blue-600 text-white' : 'bg-card text-text-primary hover:bg-blue-900'"
        @click="$emit('select', type.job_type)"
        :aria-pressed="selectedType === type.job_type"
        :tabindex="0"
      >
        <span class="flex items-center justify-center h-6 w-6 rounded-md"
          :class="iconBg(type.job_type)">
          <component :is="iconForType(type.job_type)" class="w-4 h-4" />
        </span>
        {{ type.label }}
      </button>
    </template>
  </div>
</template>

<script setup>
import { h } from 'vue'
// Example icons (replace with your icon set as needed)
const BackupIcon = {
  render() { return h('svg', { class: 'w-4 h-4 text-green-300', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 4v16m8-8H4' })]) }
}
const SyncIcon = {
  render() { return h('svg', { class: 'w-4 h-4 text-yellow-300', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 4v6h6M20 20v-6h-6M5 19A9 9 0 0021 7.5M19 5A9 9 0 003 16.5' })]) }
}
const ReportIcon = {
  render() { return h('svg', { class: 'w-4 h-4 text-purple-300', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [h('rect', { x: '3', y: '4', width: '18', height: '16', rx: '2', ry: '2' }), h('line', { x1: '16', y1: '2', x2: '16', y2: '6' }), h('line', { x1: '8', y1: '2', x2: '8', y2: '6' })]) }
}
const NotifyIcon = {
  render() { return h('svg', { class: 'w-4 h-4 text-pink-300', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V4a2 2 0 10-4 0v1.341C7.67 7.165 6 9.388 6 12v2.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9' })]) }
}
const iconForType = (type) => {
  if (type === 'backup') return BackupIcon
  if (type === 'sync') return SyncIcon
  if (type === 'report') return ReportIcon
  if (type === 'notify') return NotifyIcon
  return BackupIcon
}
const iconBg = (type) => {
  if (type === 'backup') return 'bg-green-700'
  if (type === 'sync') return 'bg-yellow-700'
  if (type === 'report') return 'bg-purple-700'
  if (type === 'notify') return 'bg-pink-700'
  return 'bg-blue-700'
}
const props = defineProps({
  jobTypes: {
    type: Array,
    default: () => []
  },
  selectedType: {
    type: String,
    default: ''
  }
})
</script> 