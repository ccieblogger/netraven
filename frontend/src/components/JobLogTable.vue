<template>
  <div>
    <div v-if="isLoading && logs.length === 0" class="text-center py-4">Loading Job Logs...</div>
    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
      Error: {{ error }}
    </div>
    <div v-if="logs.length > 0" class="bg-white shadow-md rounded my-6" :class="{ 'opacity-50': isLoading }">
      <table class="min-w-max w-full table-auto">
        <thead>
          <tr class="bg-gray-200 text-gray-600 uppercase text-sm leading-normal">
            <th class="py-3 px-6 text-left">Timestamp</th>
            <th class="py-3 px-6 text-left">Job Name</th>
            <th class="py-3 px-6 text-left">Device Name</th>
            <th class="py-3 px-6 text-left">Job Type</th>
            <th class="py-3 px-6 text-left">Level</th>
            <th class="py-3 px-6 text-left">Message</th>
          </tr>
        </thead>
        <tbody class="text-xs text-gray-600 font-light">
          <tr v-for="log in logs" :key="log.id + 'job'" class="border-b border-gray-200 hover:bg-gray-100">
            <td class="py-3 px-6 text-left text-xs whitespace-nowrap">{{ formatDateTime(log.timestamp) }}</td>
            <td class="py-3 px-6 text-left">
              <router-link v-if="log.job_id && log.job_name" :to="`/jobs/${log.job_id}`" class="text-blue-600 hover:underline">{{ log.job_name }}</router-link>
              <span v-else>{{ log.job_name || '-' }}</span>
            </td>
            <td class="py-3 px-6 text-left">
              <router-link v-if="log.device_id && log.device_name" :to="`/devices/${log.device_id}`" class="text-blue-600 hover:underline">{{ log.device_name }}</router-link>
              <span v-else>{{ log.device_name || '-' }}</span>
            </td>
            <td class="py-3 px-6 text-left">{{ log.job_type || '-' }}</td>
            <td class="py-3 px-6 text-left">
              <span :class="logLevelClass(log.level)" class="py-1 px-3 rounded-full text-xs">{{ log.level }}</span>
            </td>
            <td class="py-3 px-6 text-left">{{ log.message }}</td>
          </tr>
        </tbody>
      </table>
      <slot name="actions"></slot>
    </div>
    <div v-if="!isLoading && logs.length === 0 && !error" class="text-center text-gray-500 py-6">
      No job logs found matching the criteria.
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useJobLogStore } from '../store/job_log'
const props = defineProps({
  jobId: { type: [Number, String], required: false },
  deviceId: { type: [Number, String], required: false }
})
const jobLogStore = useJobLogStore()
const logs = computed(() => jobLogStore.logs)
const isLoading = computed(() => jobLogStore.isLoading)
const error = computed(() => jobLogStore.error)
function formatDateTime(dateTimeString) {
  if (!dateTimeString) return '-'
  try {
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' }
    return new Date(dateTimeString).toLocaleString(undefined, options)
  } catch (e) {
    return dateTimeString
  }
}
function logLevelClass(level) {
  if (!level) return 'bg-gray-200 text-gray-600'
  level = level.toLowerCase()
  if (level === 'critical' || level === 'error') return 'bg-red-200 text-red-600'
  if (level === 'warning') return 'bg-yellow-200 text-yellow-600'
  if (level === 'info') return 'bg-blue-200 text-blue-600'
  if (level === 'debug') return 'bg-gray-200 text-gray-600'
  return 'bg-gray-200 text-gray-600'
}
function fetchLogs() {
  const filters = {}
  if (props.jobId) filters.job_id = props.jobId
  if (props.deviceId) filters.device_id = props.deviceId
  jobLogStore.fetchLogs(1, filters)
}
onMounted(fetchLogs)
watch(() => [props.jobId, props.deviceId], fetchLogs)
</script> 