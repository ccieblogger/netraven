<template>
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-semibold mb-4">Logs</h1>

    <!-- Global Search Bar -->
    <div class="mb-4 flex flex-row gap-2 items-center">
      <InputText v-model="globalSearch" placeholder="Global search (message, source, etc.)" class="w-96" @input="onGlobalSearch" />
      <Button label="Clear" @click="clearGlobalSearch" v-if="globalSearch" size="small" />
    </div>

    <!-- DataTable -->
    <DataTable
      :value="logs"
      filterDisplay="row"
      :loading="logStore.isLoading"
      :paginator="true"
      :rows="pageSize"
      :totalRecords="logStore.totalCount"
      :first="(currentPage - 1) * pageSize"
      :rowsPerPageOptions="[10, 20, 50, 100]"
      :sortField="sortField"
      :sortOrder="sortOrder"
      @page="onPageChange"
      @sort="onSort"
      @filter="onFilter"
      :filters="filters"
      responsiveLayout="scroll"
      class="shadow-md rounded bg-white"
      dataKey="id"
      :emptyMessage="logStore.isLoading ? 'Loading logs...' : 'No logs found.'"
      :rowClass="rowClass"
    >
      <Column field="timestamp" header="Timestamp" :sortable="true" :filter="true" :filterMatchMode="'between'" :dataType="'date'" :body="formatDateTime" style="min-width: 180px" />
      <Column field="log_type" header="Type" :sortable="true" :filter="true" :filterMatchMode="'equals'" style="min-width: 120px">
        <template #filter="{ filterModel }">
          <Dropdown v-model="filterModel.value" :options="logTypeOptions" placeholder="All Types" showClear />
        </template>
      </Column>
      <Column field="level" header="Level" :sortable="true" :filter="true" :filterMatchMode="'equals'" style="min-width: 100px" :body="logLevelBody">
        <template #filter="{ filterModel }">
          <Dropdown v-model="filterModel.value" :options="logLevelOptions" placeholder="All Levels" showClear />
        </template>
      </Column>
      <Column field="job_id" header="Job ID" :sortable="true" :filter="true" :filterMatchMode="'equals'" style="min-width: 80px" />
      <Column field="device_id" header="Device ID" :sortable="true" :filter="true" :filterMatchMode="'equals'" style="min-width: 80px" />
      <Column field="source" header="Source" :sortable="true" :filter="true" :filterMatchMode="'contains'" style="min-width: 120px" />
      <Column field="message" header="Message" :sortable="true" :filter="true" :filterMatchMode="'contains'" style="min-width: 200px" />
      <Column field="meta" header="Meta" :body="metaBody" style="min-width: 180px" />
    </DataTable>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useLogStore } from '../store/log'
import { useRoute, useRouter } from 'vue-router'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Button from 'primevue/button'

const logStore = useLogStore()
const route = useRoute()
const router = useRouter()

const logs = computed(() => logStore.logs)
const currentPage = ref(1)
const pageSize = ref(20)
const sortField = ref('timestamp')
const sortOrder = ref(-1) // -1: desc, 1: asc
const filters = ref({})
const globalSearch = ref('')

// For dropdown filters
const logTypeOptions = ref([])
const logLevelOptions = ref([])

// --- Deep-linking helpers ---
function parseQueryParams() {
  // Parse query params and set initial state
  const q = route.query
  if (q.page) currentPage.value = parseInt(q.page)
  if (q.size) pageSize.value = parseInt(q.size)
  if (q.sort) {
    const [field, dir] = q.sort.split('_')
    sortField.value = field
    sortOrder.value = dir === 'asc' ? 1 : -1
  }
  // Filters
  filters.value = {}
  if (q.log_type) filters.value.log_type = { value: q.log_type }
  if (q.level) filters.value.level = { value: q.level }
  if (q.job_id) filters.value.job_id = { value: q.job_id }
  if (q.device_id) filters.value.device_id = { value: q.device_id }
  if (q.source) filters.value.source = { value: q.source }
  if (q.message) filters.value.message = { value: q.message }
  if (q.start_time && q.end_time) filters.value.timestamp = { value: [q.start_time, q.end_time] }
  if (q.search) globalSearch.value = q.search
}
function updateQueryParams() {
  // Update the URL with the current filter/sort/page state
  const q = {}
  if (currentPage.value > 1) q.page = currentPage.value
  if (pageSize.value !== 20) q.size = pageSize.value
  if (sortField.value) q.sort = `${sortField.value}_${sortOrder.value === 1 ? 'asc' : 'desc'}`
  // Filters
  if (filters.value.log_type && filters.value.log_type.value) q.log_type = filters.value.log_type.value
  if (filters.value.level && filters.value.level.value) q.level = filters.value.level.value
  if (filters.value.job_id && filters.value.job_id.value) q.job_id = filters.value.job_id.value
  if (filters.value.device_id && filters.value.device_id.value) q.device_id = filters.value.device_id.value
  if (filters.value.source && filters.value.source.value) q.source = filters.value.source.value
  if (filters.value.message && filters.value.message.value) q.message = filters.value.message.value
  if (filters.value.timestamp && filters.value.timestamp.value && filters.value.timestamp.value.length === 2) {
    q.start_time = filters.value.timestamp.value[0]
    q.end_time = filters.value.timestamp.value[1]
  }
  if (globalSearch.value) q.search = globalSearch.value
  router.replace({ query: q })
}

// Fetch log types/levels for dropdowns
async function fetchFilterOptions() {
  const [types, levels] = await Promise.all([
    logStore.fetchLogTypes(),
    logStore.fetchLogLevels()
  ])
  logTypeOptions.value = types.map(t => ({ label: t.description || t.log_type, value: t.log_type }))
  logLevelOptions.value = levels.map(l => ({ label: l.description || l.level, value: l.level }))
}

onMounted(async () => {
  await fetchFilterOptions()
  parseQueryParams()
  fetchLogs()
})

function fetchLogs() {
  logStore.fetchLogs(currentPage.value, buildFilters())
}

function buildFilters() {
  // Build filter object for API from DataTable filters/global search
  const f = {}
  if (filters.value.log_type) f.log_type = filters.value.log_type.value
  if (filters.value.level) f.level = filters.value.level.value
  if (filters.value.job_id) f.job_id = filters.value.job_id.value
  if (filters.value.device_id) f.device_id = filters.value.device_id.value
  if (filters.value.source) f.source = filters.value.source.value
  if (filters.value.message) f.search = filters.value.message.value
  if (filters.value.timestamp && filters.value.timestamp.value && filters.value.timestamp.value.length === 2) {
    f.start_time = filters.value.timestamp.value[0]
    f.end_time = filters.value.timestamp.value[1]
  }
  if (globalSearch.value) f.search = globalSearch.value
  return f
}

function onPageChange(e) {
  currentPage.value = e.page + 1
  pageSize.value = e.rows
  fetchLogs()
  updateQueryParams()
}
function onSort(e) {
  sortField.value = e.sortField
  sortOrder.value = e.sortOrder
  fetchLogs()
  updateQueryParams()
}
function onFilter(e) {
  filters.value = e.filters
  fetchLogs()
  updateQueryParams()
}
function onGlobalSearch() {
  fetchLogs()
  updateQueryParams()
}
function clearGlobalSearch() {
  globalSearch.value = ''
  fetchLogs()
  updateQueryParams()
}

// Custom body for meta column
function metaBody(row) {
  return row.meta ? `<pre class='text-xs whitespace-pre-wrap font-mono'>${JSON.stringify(row.meta, null, 2)}</pre>` : '-'
}
// Custom body for log level
function logLevelBody(row) {
  const level = row.level ? row.level.toLowerCase() : ''
  let color = 'bg-gray-200 text-gray-600'
  if (level === 'critical' || level === 'error') color = 'bg-red-200 text-red-600'
  else if (level === 'warning') color = 'bg-yellow-200 text-yellow-600'
  else if (level === 'info') color = 'bg-blue-200 text-blue-600'
  return `<span class='${color} px-2 py-1 rounded text-xs font-semibold'>${row.level}</span>`
}
// Custom row class for hover effect
function rowClass() {
  return 'hover:bg-gray-100'
}
// Format timestamp
function formatDateTime(row) {
  if (!row.timestamp) return '-'
  try {
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' }
    return new Date(row.timestamp).toLocaleString(undefined, options)
  } catch (e) {
    return row.timestamp
  }
}
</script>

<style scoped>
.p-datatable .p-datatable-thead > tr > th {
  background: #f3f4f6;
  color: #374151;
  font-weight: 600;
  font-size: 0.95rem;
  padding: 0.75rem 1rem;
}
.p-datatable .p-datatable-tbody > tr > td {
  padding: 0.65rem 1rem;
  font-size: 0.95rem;
}
.p-datatable .p-datatable-tbody > tr:hover > td {
  background: #f1f5f9;
}
</style>
