<template>
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-semibold mb-4">System Logs</h1>

    <!-- Filters -->
    <div class="bg-white p-4 rounded shadow mb-6 flex space-x-4 items-end">
      <div>
        <label for="jobIdFilter" class="block text-sm font-medium text-gray-700">Job ID</label>
        <input type="number" id="jobIdFilter" v-model.number="currentFilters.job_id" placeholder="Filter by Job ID" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
      </div>
      <div>
        <label for="deviceIdFilter" class="block text-sm font-medium text-gray-700">Device ID</label>
        <input type="number" id="deviceIdFilter" v-model.number="currentFilters.device_id" placeholder="Filter by Device ID" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
      </div>
      <div>
        <label for="logTypeFilter" class="block text-sm font-medium text-gray-700">Log Type</label>
        <select id="logTypeFilter" v-model="currentFilters.log_type" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
          <option :value="null">All</option>
          <option value="job">Job Logs</option>
          <option value="connection">Connection Logs</option>
        </select>
      </div>
      <button @click="applyFilters" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
        Apply Filters
      </button>
      <button @click="resetFilters" class="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded">
        Reset
      </button>
    </div>

    <!-- Loading/Error Indicators -->
    <div v-if="logStore.isLoading && logs.length === 0" class="text-center py-4">Loading Logs...</div>
     <div v-if="logStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
       Error: {{ logStore.error }}
    </div>

    <!-- Logs Table -->
    <div v-if="logs.length > 0" class="bg-white shadow-md rounded my-6" :class="{ 'opacity-50': logStore.isLoading }">
      <table class="min-w-max w-full table-auto">
        <thead>
          <tr class="bg-gray-200 text-gray-600 uppercase text-sm leading-normal">
            <th class="py-3 px-6 text-left">Timestamp</th>
            <th class="py-3 px-6 text-left">Type</th>
            <th class="py-3 px-6 text-left">Job ID</th>
            <th class="py-3 px-6 text-left">Device ID</th>
            <th class="py-3 px-6 text-left">Level</th>
            <th class="py-3 px-6 text-left">Message / Log Content</th>
          </tr>
        </thead>
        <tbody class="text-gray-600 text-sm font-light">
          <tr v-for="log in logs" :key="log.id + (log.message ? 'job' : 'conn')" class="border-b border-gray-200 hover:bg-gray-100">
             <td class="py-3 px-6 text-left text-xs whitespace-nowrap">{{ formatDateTime(log.timestamp) }}</td>
             <td class="py-3 px-6 text-left">
                <span :class="log.message ? 'bg-purple-100 text-purple-600' : 'bg-green-100 text-green-600' " class="py-1 px-3 rounded-full text-xs">
                  {{ log.message ? 'Job' : 'Connection' }}
                </span>
             </td>
             <td class="py-3 px-6 text-left">{{ log.job_id }}</td>
             <td class="py-3 px-6 text-left">{{ log.device_id || '-' }}</td>
             <td class="py-3 px-6 text-left">
                 <span v-if="log.level" :class="logLevelClass(log.level)" class="py-1 px-3 rounded-full text-xs">
                   {{ log.level }}
                 </span>
                 <span v-else>-</span>
             </td>
             <td class="py-3 px-6 text-left">
                 <pre v-if="!log.message" class="text-xs whitespace-pre-wrap font-mono">{{ log.log }}</pre>
                 <span v-else>{{ log.message }}</span>
             </td>
          </tr>
        </tbody>
      </table>
       <!-- Pagination Controls -->
       <PaginationControls
            v-if="totalPages > 1"
            :current-page="logStore.pagination.currentPage"
            :total-pages="totalPages"
            @change-page="handlePageChange"
        />
    </div>

    <!-- No Logs Message -->
    <div v-if="!logStore.isLoading && logs.length === 0 && !logStore.error" class="text-center text-gray-500 py-6">
      No logs found matching the criteria.
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, computed, reactive, watch } from 'vue'
import { useLogStore } from '../store/log'
import { useRoute, useRouter } from 'vue-router' // To potentially pre-fill filters from query params
import PaginationControls from '../components/PaginationControls.vue'

const logStore = useLogStore()
const logs = computed(() => logStore.logs)
const totalPages = computed(() => logStore.totalPages) // Use computed from store
const route = useRoute()
const router = useRouter()

// Local reactive state for filter inputs, initialized from route query
const currentFilters = reactive({
  job_id: route.query.job_id ? parseInt(route.query.job_id) : null,
  device_id: route.query.device_id ? parseInt(route.query.device_id) : null,
  log_type: route.query.log_type || null,
})

// Function to update route query params when filters or page change
function updateRouteQuery() {
    const query = { ...route.query }; // Start with existing query params

    // Update filters in query
    Object.keys(currentFilters).forEach(key => {
        if (currentFilters[key] != null && currentFilters[key] !== '') {
            query[key] = currentFilters[key];
        } else {
            delete query[key]; // Remove empty/null filters from URL
        }
    });

    // Update page in query
    if (logStore.pagination.currentPage > 1) {
        query.page = logStore.pagination.currentPage;
    } else {
        delete query.page; // Don't show page=1 in URL
    }

    // Use replace to avoid adding multiple history entries for pagination/filtering
    router.replace({ query });
}

// Fetch logs when component mounts
onMounted(() => {
    const initialPage = route.query.page ? parseInt(route.query.page) : 1;
    // Pass initial filters and page from route query
    logStore.fetchLogs(initialPage, currentFilters)
})

function applyFilters() {
  // fetchLogs in store now resets page to 1 when newFilters are passed
  logStore.fetchLogs(1, currentFilters);
  updateRouteQuery(); // Update URL after applying filters
}

function resetFilters() {
  currentFilters.job_id = null
  currentFilters.device_id = null
  currentFilters.log_type = null
  // fetchLogs resets page to 1
  logStore.fetchLogs(1, currentFilters);
  updateRouteQuery(); // Update URL after resetting filters
}

function handlePageChange(newPage) {
    logStore.fetchLogs(newPage); // Fetch new page, filters remain the same
    updateRouteQuery(); // Update URL after changing page
}

// --- Helper Functions ---
function formatDateTime(dateTimeString) {
  if (!dateTimeString) return '-';
  try {
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' };
    return new Date(dateTimeString).toLocaleString(undefined, options);
  } catch (e) {
    return dateTimeString;
  }
}

function logLevelClass(level) {
  if (!level) return 'bg-gray-200 text-gray-600';
  level = level.toLowerCase();
  if (level === 'critical' || level === 'error') return 'bg-red-200 text-red-600';
  if (level === 'warning') return 'bg-yellow-200 text-yellow-600';
  if (level === 'info') return 'bg-blue-200 text-blue-600';
  if (level === 'debug') return 'bg-gray-200 text-gray-600';
  return 'bg-gray-200 text-gray-600';
}

// Optional: Watch route query changes if you want external links to update the view
// watch(() => route.query, (newQuery) => {
//     currentFilters.job_id = newQuery.job_id ? parseInt(newQuery.job_id) : null;
//     currentFilters.device_id = newQuery.device_id ? parseInt(newQuery.device_id) : null;
//     currentFilters.log_type = newQuery.log_type || null;
//     const page = newQuery.page ? parseInt(newQuery.page) : 1;
//     logStore.fetchLogs(page, currentFilters);
// }, { deep: true });

</script>

<style scoped>
/* Add any page-specific styles */
</style>
