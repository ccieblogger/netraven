<template>
  <NrCard accent className="border-l-4 border-l-blue-500">
    <div class="p-4 flex flex-col h-full">
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-lg uppercase font-semibold text-text-secondary">Job Types</h2>
        <span class="flex items-center justify-center h-8 w-8 rounded-md bg-blue-600">
          <!-- Clipboard List Icon -->
          <svg class="w-5 h-5 text-blue-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5h6M9 3h6a2 2 0 012 2v14a2 2 0 01-2 2H9a2 2 0 01-2-2V5a2 2 0 012-2zm0 0V3a2 2 0 012-2h2a2 2 0 012 2v2" />
          </svg>
        </span>
      </div>
      <ul class="flex-1 space-y-2">
        <li v-for="type in jobTypes" :key="type.job_type">
          <button
            class="w-full flex items-center px-2 py-2 rounded transition-colors text-left focus:outline-none focus:ring-2 focus:ring-blue-400"
            :class="selectedType === type.job_type ? 'bg-blue-600 text-white' : 'bg-card text-text-primary hover:bg-blue-900'"
            @click="$emit('select', type.job_type)"
            :aria-pressed="selectedType === type.job_type"
            :tabindex="0"
          >
            <span class="flex items-center">
              <span class="flex items-center justify-center h-7 w-7 rounded-md mr-3"
                :class="iconBg(type.job_type)">
                <component :is="iconForType(type.job_type)" class="w-5 h-5" />
              </span>
              <span class="font-medium">{{ type.label }}</span>
            </span>
          </button>
        </li>
      </ul>
    </div>
  </NrCard>
</template>

<script setup>
import NrCard from '../ui/Card.vue'
import { h } from 'vue'
// Example icons (replace with your icon set as needed)
const BackupIcon = {
  render() { return h('svg', { class: 'w-5 h-5 text-green-300', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 4v16m8-8H4' })]) }
}
const SyncIcon = {
  render() { return h('svg', { class: 'w-5 h-5 text-yellow-300', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 4v6h6M20 20v-6h-6M5 19A9 9 0 0021 7.5M19 5A9 9 0 003 16.5' })]) }
}
const ReportIcon = {
  render() { return h('svg', { class: 'w-5 h-5 text-purple-300', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [h('rect', { x: '3', y: '4', width: '18', height: '16', rx: '2', ry: '2' }), h('line', { x1: '16', y1: '2', x2: '16', y2: '6' }), h('line', { x1: '8', y1: '2', x2: '8', y2: '6' })]) }
}
const NotifyIcon = {
  render() { return h('svg', { class: 'w-5 h-5 text-pink-300', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V4a2 2 0 10-4 0v1.341C7.67 7.165 6 9.388 6 12v2.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9' })]) }
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