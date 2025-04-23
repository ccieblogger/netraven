<template>
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-semibold mb-4">Job Logs</h1>
    <!-- Filters -->
    <ResourceFilter
      title="Job Log Filters"
      :filter-fields="filterFields"
      :initial-filters="currentFilters"
      @filter="applyFilters"
      @reset="resetFilters"
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
    <JobLogTable :logs="logs" :is-loading="jobLogStore.isLoading" :error="jobLogStore.error" />
    <!-- Pagination Controls -->
    <PaginationControls
      v-if="totalPages > 1"
      :current-page="jobLogStore.pagination.currentPage"
      :total-pages="totalPages"
      @change-page="handlePageChange"
    />
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
import { jobTypeRegistry } from '../jobTypeRegistry'
import JobLogTable from '../components/JobLogTable.vue'

const jobLogStore = useJobLogStore()
const logs = computed(() => jobLogStore.logs)
const totalPages = computed(() => jobLogStore.totalPages)
const route = useRoute()
const router = useRouter()

// Prepare job type options from registry
const jobTypeOptions = Object.entries(jobTypeRegistry).map(([key, value]) => ({
  value: key,
  label: value.label
}))

// Filter fields configuration
const filterFields = [
  {
    name: 'search',
    label: 'Search',
    type: 'text',
    placeholder: 'Search logs...'
  },
  {
    name: 'job_name',
    label: 'Job Name',
    type: 'select',
    placeholder: 'Select job name',
    options: computed(() => jobLogStore.jobNames.map(n => ({ value: n, label: n }))),
    loading: computed(() => jobLogStore.jobNamesLoading),
    async: true
  },
  {
    name: 'device_names',
    label: 'Device',
    type: 'select',
    placeholder: 'Select device',
    options: computed(() => jobLogStore.deviceNames.map(n => ({ value: n, label: n }))),
    loading: computed(() => jobLogStore.deviceNamesLoading),
    async: true
  },
  {
    name: 'job_type',
    label: 'Job Type',
    type: 'select',
    placeholder: 'Select job type',
    options: jobTypeOptions
  },
  {
    name: 'level',
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
  search: '',
  job_name: null,
  device_names: [],
  job_type: null,
  level: null
})

function updateRouteQuery() {
  const query = { ...route.query }
  Object.keys(currentFilters).forEach(key => {
    if (currentFilters[key] != null && currentFilters[key] !== '' && (!Array.isArray(currentFilters[key]) || currentFilters[key].length > 0)) {
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

onMounted(async () => {
  await Promise.all([
    jobLogStore.fetchJobNames(),
    jobLogStore.fetchDeviceNames()
  ])
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
    if (Array.isArray(currentFilters[key])) {
      currentFilters[key] = []
    } else {
      currentFilters[key] = null
    }
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