<template>
  <div class="overflow-x-auto px-6 bg-card rounded-lg shadow">
    <table class="min-w-full">
      <thead>
        <tr>
          <th class="px-4 py-2">Name</th>
          <th class="px-4 py-2">Status</th>
          <th class="px-4 py-2">Started</th>
          <th class="px-4 py-2">Devices</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="job in jobs" :key="job.id">
          <td class="px-4 py-2">{{ job.name }}</td>
          <td class="px-4 py-2">
            <span :class="statusClass(job.status)">{{ job.status }}</span>
          </td>
          <td class="px-4 py-2">{{ job.started }}</td>
          <td class="px-4 py-2">{{ job.devices }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
<script setup>
// Phase 1: mock data only
const props = defineProps({
  jobs: {
    type: Array,
    required: true,
    default: () => []
  }
})
function statusClass(status) {
  if (status === 'Running') return 'text-info font-semibold'
  if (status === 'Succeeded') return 'text-success font-semibold'
  if (status === 'Failed') return 'text-danger font-semibold'
  return ''
}
</script> 