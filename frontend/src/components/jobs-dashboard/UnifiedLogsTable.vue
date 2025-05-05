<template>
  <div class="overflow-x-auto px-6 bg-card rounded-lg shadow">
    <table class="min-w-full">
      <thead>
        <tr>
          <th class="px-4 py-2">Timestamp</th>
          <th class="px-4 py-2">Level</th>
          <th class="px-4 py-2">Message</th>
          <th class="px-4 py-2">Job ID</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in logs" :key="log.id">
          <td class="px-4 py-2">{{ log.timestamp }}</td>
          <td class="px-4 py-2">
            <span :class="levelClass(log.level)">{{ log.level }}</span>
          </td>
          <td class="px-4 py-2">{{ log.message }}</td>
          <td class="px-4 py-2">{{ log.job_id }}</td>
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
  return ''
}
</script> 