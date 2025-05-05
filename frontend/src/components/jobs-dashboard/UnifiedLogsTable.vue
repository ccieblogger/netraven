<template>
  <div class="nr-card overflow-x-auto">
    <table class="min-w-full table-auto">
      <thead>
        <tr style="border-bottom:2px solid #fff;" class="bg-card text-text-primary font-semibold text-sm">
          <th class="py-2 px-4 text-left">Timestamp</th>
          <th class="py-2 px-4 text-left">Log Type</th>
          <th class="py-2 px-4 text-left">Level</th>
          <th class="py-2 px-4 text-left">Source</th>
          <th class="py-2 px-4 text-left">Job ID</th>
          <th class="py-2 px-4 text-left">Device ID</th>
          <th class="py-2 px-4 text-left">Message</th>
          <th class="py-2 px-4 text-left">Meta</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in logs" :key="log.id" class="border-b border-divider text-text-primary">
          <td class="py-2 px-4 text-xs">{{ formatDate(log.timestamp) }}</td>
          <td class="py-2 px-4 text-xs">{{ log.log_type }}</td>
          <td class="py-2 px-4 text-xs">
            <span :class="levelClass(log.level)">{{ log.level }}</span>
          </td>
          <td class="py-2 px-4 text-xs">{{ log.source }}</td>
          <td class="py-2 px-4 text-xs">{{ log.job_id }}</td>
          <td class="py-2 px-4 text-xs">{{ log.device_id }}</td>
          <td class="py-2 px-4 text-xs">{{ log.message }}</td>
          <td class="py-2 px-4 text-xs">
            <button v-if="log.meta" class="text-primary underline" @click="$emit('show-meta', log.meta)">View</button>
            <span v-else class="text-text-secondary">-</span>
          </td>
        </tr>
        <tr v-if="logs.length === 0">
          <td colspan="8" class="text-center text-text-secondary py-4 text-xs">No logs found.</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
<script setup>
// Phase 1: mock data only
const props = defineProps({
  logs: {
    type: Array,
    required: true,
    default: () => []
  }
})
function levelClass(level) {
  if (level === 'info') return 'text-info font-semibold'
  if (level === 'error') return 'text-danger font-semibold'
  if (level === 'warning') return 'text-warning font-semibold'
  return 'text-text-primary'
}
function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script> 