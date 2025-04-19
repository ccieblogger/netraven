<template>
  <div>
    <div v-if="isLoading && logs.length === 0" class="text-center py-4">Loading Connection Logs...</div>
    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
      Error: {{ error }}
    </div>
    <div v-if="logs.length > 0" class="bg-white shadow-md rounded my-6" :class="{ 'opacity-50': isLoading }">
      <table class="min-w-max w-full table-auto">
        <thead>
          <tr class="bg-gray-200 text-gray-600 uppercase text-sm leading-normal">
            <th class="py-3 px-6 text-left">Timestamp</th>
            <th class="py-3 px-6 text-left">Job ID</th>
            <th class="py-3 px-6 text-left">Device ID</th>
            <th class="py-3 px-6 text-left">Log Content</th>
          </tr>
        </thead>
        <tbody class="text-gray-600 text-sm font-light">
          <tr v-for="log in logs" :key="log.id + 'conn'" class="border-b border-gray-200 hover:bg-gray-100">
            <td class="py-3 px-6 text-left text-xs whitespace-nowrap">{{ formatDateTime(log.timestamp) }}</td>
            <td class="py-3 px-6 text-left">{{ log.job_id }}</td>
            <td class="py-3 px-6 text-left">{{ log.device_id || '-' }}</td>
            <td class="py-3 px-6 text-left">
              <pre class="text-xs whitespace-pre-wrap font-mono">{{ log.log }}</pre>
            </td>
          </tr>
        </tbody>
      </table>
      <slot name="actions"></slot>
    </div>
    <div v-if="!isLoading && logs.length === 0 && !error" class="text-center text-gray-500 py-6">
      No connection logs found matching the criteria.
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useLogStore } from '../store/log'
const props = defineProps({
  jobId: { type: [Number, String], required: false },
  deviceId: { type: [Number, String], required: false }
})
const logStore = useLogStore()
const logs = computed(() => logStore.logs)
const isLoading = computed(() => logStore.isLoading)
const error = computed(() => logStore.error)
function formatDateTime(dateTimeString) {
  if (!dateTimeString) return '-'
  try {
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' }
    return new Date(dateTimeString).toLocaleString(undefined, options)
  } catch (e) {
    return dateTimeString
  }
}
function fetchLogs() {
  const filters = {}
  if (props.jobId) filters.job_id = props.jobId
  if (props.deviceId) filters.device_id = props.deviceId
  logStore.fetchLogs(1, filters)
}
onMounted(fetchLogs)
watch(() => [props.jobId, props.deviceId], fetchLogs)
</script> 