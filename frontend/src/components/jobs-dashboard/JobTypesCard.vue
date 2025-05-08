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
          <component :is="iconForType(type)" class="w-4 h-4" />
        </span>
        {{ type.label }}
      </button>
    </template>
  </div>
</template>

<script setup>
import { h } from 'vue'
// Import Heroicons
import { DocumentIcon, CloudArrowDownIcon, SignalIcon, BellAlertIcon, QuestionMarkCircleIcon } from '@heroicons/vue/24/outline'

// Map icon string from API to Heroicon component
const heroiconMap = {
  BackupIcon: CloudArrowDownIcon,
  NetworkCheckIcon: SignalIcon,
  NotifyIcon: BellAlertIcon,
  // Add more mappings as needed
  // Fallbacks for common names
  DocumentIcon: DocumentIcon,
}

const iconForType = (typeObj) => {
  // Use the icon string from the API, fallback to QuestionMarkCircleIcon
  const iconStr = typeObj.icon
  return heroiconMap[iconStr] || QuestionMarkCircleIcon
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