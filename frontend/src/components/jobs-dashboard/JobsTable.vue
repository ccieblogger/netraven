<template>
  <div class="nr-card overflow-x-auto">
    <table class="min-w-full table-auto">
      <thead>
        <tr class="bg-card text-text-secondary text-sm">
          <th class="py-2 px-4 text-left">Job Name</th>
          <th class="py-2 px-4 text-left">Job Type</th>
          <th class="py-2 px-4 text-left">{{ activeTab === 'scheduled' ? 'Schedule' : 'Run Time' }}</th>
          <th class="py-2 px-4 text-left">{{ activeTab === 'scheduled' ? 'Next Run' : 'Duration' }}</th>
          <th class="py-2 px-4 text-left">{{ activeTab === 'scheduled' ? 'Last Run' : 'Status' }}</th>
          <th class="py-2 px-4 text-left">Targets</th>
        </tr>
      </thead>
      <tbody>
        <template v-if="activeTab === 'scheduled'">
          <tr v-for="job in scheduledJobsToShow" :key="job.id" class="border-b text-text-primary">
            <td class="py-2 px-4">{{ job.name }}</td>
            <td class="py-2 px-4">{{ job.job_type }}</td>
            <td class="py-2 px-4">{{ job.schedule_type === 'interval' ? `Every ${job.interval_seconds}s` : job.schedule_type === 'cron' ? job.cron_string : job.schedule_type === 'onetime' ? formatDateTime(job.scheduled_for) : '-' }}</td>
            <td class="py-2 px-4">{{ formatDateTime(job.next_run) }}</td>
            <td class="py-2 px-4">{{ job.last_run || '-' }}</td>
            <td class="py-2 px-4">
              <span v-for="tag in job.tags || []" :key="tag.id" class="bg-blue-100 text-blue-700 px-2 py-1 rounded-full text-xs mr-1">{{ tag.name }}</span>
              <button class="bg-blue-500 hover:bg-blue-700 text-white text-xs px-3 py-1 rounded ml-2">View</button>
            </td>
          </tr>
          <tr v-if="scheduledJobsToShow.length === 0">
            <td colspan="6" class="text-center text-text-secondary py-4">No jobs found.</td>
          </tr>
        </template>
        <template v-else>
          <tr v-for="job in recentJobsToShow" :key="job.id" class="border-b text-text-primary">
            <td class="py-2 px-4">{{ job.name }}</td>
            <td class="py-2 px-4">{{ job.job_type }}</td>
            <td class="py-2 px-4">{{ formatDateTime(job.run_time) }}</td>
            <td class="py-2 px-4">{{ formatDuration(job.duration) }}</td>
            <td class="py-2 px-4">{{ job.status }}</td>
            <td class="py-2 px-4">
              <span v-for="dev in job.devices || []" :key="dev.id" class="bg-blue-100 text-blue-700 px-2 py-1 rounded-full text-xs mr-1">{{ dev.name }}</span>
              <button class="bg-blue-500 hover:bg-blue-700 text-white text-xs px-3 py-1 rounded ml-2">View</button>
            </td>
          </tr>
          <tr v-if="recentJobsToShow.length === 0">
            <td colspan="6" class="text-center text-text-secondary py-4">No jobs found.</td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>
<script setup>
import { computed } from 'vue'
const props = defineProps({
  activeTab: String,
  filters: Array,
  scheduledJobs: { type: Array, default: () => [] },
  recentJobs: { type: Array, default: () => [] }
})
const scheduledJobsToShow = computed(() => props.scheduledJobs || [])
const recentJobsToShow = computed(() => props.recentJobs || [])
function formatDateTime(dt) {
  if (!dt) return '-';
  try {
    return new Date(dt).toLocaleString();
  } catch {
    return dt;
  }
}
function formatDuration(seconds) {
  if (!seconds) return '-';
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return m > 0 ? `${m} min${m > 1 ? 's' : ''} ${s}s` : `${s}s`
}
</script> 