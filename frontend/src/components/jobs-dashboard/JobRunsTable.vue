<template>
  <div class="nr-card overflow-x-auto">
    <table class="min-w-full table-auto">
      <thead>
        <tr style="border-bottom:2px solid #fff;" class="bg-card text-text-primary font-semibold text-sm">
          <th class="py-2 px-4 text-left">Start Time</th>
          <th class="py-2 px-4 text-left">Job Name</th>
          <th class="py-2 px-4 text-left">Device Name</th>
          <th class="py-2 px-4 text-left">Job Type</th>
          <th class="py-2 px-4 text-left">Status</th>
          <th class="py-2 px-4 text-left">Completed At</th>
          <th class="py-2 px-4 text-left">Details</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="job in jobs" :key="job.id" class="border-b border-divider text-text-primary">
          <td class="py-2 px-4 text-xs">{{ formatDate(job.created_at) }}</td>
          <td class="py-2 px-4 text-xs">{{ job.job_name }}</td>
          <td class="py-2 px-4 text-xs">{{ job.device_name }}</td>
          <td class="py-2 px-4 text-xs">{{ job.job_type }}</td>
          <td class="py-2 px-4 text-xs">
            <span :class="statusClass(job.status)">{{ job.status }}</span>
          </td>
          <td class="py-2 px-4 text-xs">{{ formatDate(job.result_time) }}</td>
          <td class="py-2 px-4 text-xs">
            <button class="text-primary underline" @click="$emit('show-details', job.details)">View</button>
          </td>
        </tr>
        <tr v-if="jobs.length === 0">
          <td colspan="7" class="text-center text-text-secondary py-4 text-xs">No job runs found.</td>
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
  return 'text-text-primary'
}
function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script> 