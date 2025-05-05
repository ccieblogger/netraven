<template>
  <div class="nr-card overflow-x-auto">
    <table class="min-w-full table-auto">
      <thead>
        <tr style="border-bottom:2px solid #fff;" class="bg-card text-text-primary font-semibold text-sm">
          <th class="py-2 px-4 text-left">Timestamp</th>
          <th class="py-2 px-4 text-left">Level</th>
          <th class="py-2 px-4 text-left">Message</th>
          <th class="py-2 px-4 text-left">Job ID</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in logs" :key="log.id" class="border-b border-divider text-text-primary">
          <td class="py-2 px-4 text-xs">{{ log.timestamp }}</td>
          <td class="py-2 px-4 text-xs">
            <span :class="levelClass(log.level)">{{ log.level }}</span>
          </td>
          <td class="py-2 px-4 text-xs">{{ log.message }}</td>
          <td class="py-2 px-4 text-xs">{{ log.job_id }}</td>
        </tr>
        <tr v-if="logs.length === 0">
          <td colspan="4" class="text-center text-text-secondary py-4 text-xs">No logs found.</td>
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
</script> 