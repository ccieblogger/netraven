<template>
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-semibold mb-4">Job Logs</h1>
    <!-- Filters -->
    <ResourceFilter
      title="Job Log Filters"
      :filter-fields="filterFields"
      :initial-filters="currentFilters"
      @apply-filters="applyFilters"
      @reset-filters="resetFilters"
    />
    <!-- Loading/Error Indicators -->
    <div v-if="jobLogStore.isLoading && logs.length === 0" class="text-center py-4">Loading Job Logs...</div>
    <div v-if="jobLogStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
      <span v-if="jobLogStore.error === 'Not authenticated' || jobLogStore.error === '401 Unauthorized'">
        Your session has expired or you are not logged in. <router-link to="/login" class="underline text-blue-700">Please log in again.</router-link>
      </span>
      <span v-else-if="jobLogStore.error === 'Not Found' || jobLogStore.error === '404 Not Found'">
        Job Logs endpoint not found. Please contact support.
      </span>
      <span v-else>
        Error: {{ jobLogStore.error }}
      </span>
    </div>
    <!-- Logs Table -->
    <div v-if="logs.length > 0" class="bg-white shadow-md rounded my-6" :class="{ 'opacity-50': jobLogStore.isLoading }">
      <table class="min-w-max w-full table-auto">
        <thead>
          <tr class="bg-gray-200 text-gray-600 uppercase text-sm leading-normal">
            <th class="py-3 px-6 text-left">Timestamp</th>
            <th class="py-3 px-6 text-left">Job ID</th>
            <th class="py-3 px-6 text-left">Device ID</th>
            <th class="py-3 px-6 text-left">Level</th>
            <th class="py-3 px-6 text-left">Message</th>
          </tr>
        </thead>
        <tbody class="text-gray-600 text-sm font-light">
          <tr v-for="log in logs" :key="log.id + 'job'" class="border-b border-gray-200 hover:bg-gray-100">
            <td class="py-3 px-6 text-left text-xs whitespace-nowrap">{{ formatDateTime(log.timestamp) }}</td>
            <td class="py-3 px-6 text-left">{{ log.job_id }}</td>
            <td class="py-3 px-6 text-left">{{ log.device_id || '-' }}</td>
            <td class="py-3 px-6 text-left">
              <span :class="logLevelClass(log.level)" class="py-1 px-3 rounded-full text-xs">{{ log.level }}</span>
            </td>
            <td class="py-3 px-6 text-left">{{ log.message }}</td>
          </tr>
        </tbody>
      </table>
      <!-- Pagination Controls -->
      <PaginationControls
        v-if="totalPages > 1"
        :current-page="jobLogStore.pagination.currentPage"
        :total-pages="totalPages"
        @change-page="handlePageChange"
      />
    </div>
    <!-- No Logs Message -->
    <div v-if="!jobLogStore.isLoading && logs.length === 0 && !jobLogStore.error" class="text-center text-gray-500 py-6">
      No job logs found matching the criteria.
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, reactive } from 'vue'
import { useJobLogStore } from '../store/job_log'
import { useRoute, useRouter } from 'vue-router'
import PaginationControls from '../components/PaginationControls.vue'
import ResourceFilter from '../components/ResourceFilter.vue'

const jobLogStore = useJobLogStore()
const logs = computed(() => jobLogStore.logs)
const totalPages = computed(() => jobLogStore.totalPages)
const route = useRoute()
const router = useRouter()

// Filter fields configuration
const filterFields = [
  {
    id: 'job_id',
    label: 'Job ID',
    type: 'number',
    placeholder: 'Filter by Job ID'
  },
  {
    id: 'device_id',
    label: 'Device ID',
    type: 'number',
    placeholder: 'Filter by Device ID'
  },
  {
    id: 'level',
    label: 'Level',
    type: 'select',
    placeholder: 'Select level',
    options: [
      { value: null, label: 'All' },
      { value: 'INFO', label: 'INFO' },
      { value: 'ERROR', label: 'ERROR' },
      { value: 'WARNING', label: 'WARNING' },
      { value: 'CRITICAL', label: 'CRITICAL' },
      { value: 'DEBUG', label: 'DEBUG' }
    ]
  }
]

const currentFilters = reactive({
  job_id: route.query.job_id ? parseInt(route.query.job_id) : null,
  device_id: route.query.device_id ? parseInt(route.query.device_id) : null,
  level: route.query.level || null
})

function updateRouteQuery() {
  const query = { ...route.query }
  Object.keys(currentFilters).forEach(key => {
    if (currentFilters[key] != null && currentFilters[key] !== '') {
      query[key] = currentFilters[key]
    } else {
      delete query[key]
    }
  })
  if (jobLogStore.pagination.currentPage > 1) {
    query.page = jobLogStore.pagination.currentPage
  } else {
    delete query.page
  }
  router.replace({ query })
}

onMounted(() => {
  const initialPage = route.query.page ? parseInt(route.query.page) : 1
  jobLogStore.fetchLogs(initialPage, currentFilters)
})

function applyFilters(filters) {
  Object.assign(currentFilters, filters)
  jobLogStore.fetchLogs(1, currentFilters)
  updateRouteQuery()
}

function resetFilters() {
  Object.keys(currentFilters).forEach(key => {
    currentFilters[key] = null
  })
  jobLogStore.fetchLogs(1, currentFilters)
  updateRouteQuery()
}

function handlePageChange(newPage) {
  jobLogStore.fetchLogs(newPage)
  updateRouteQuery()
}

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
</script>

<style scoped>
/* Add any page-specific styles */
</style> 