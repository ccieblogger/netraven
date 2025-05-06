<template>
  <PageContainer title="Job Status Dashboard">
    <!-- KPI Cards Row: Job Status KPIs -->
    <div class="w-full px-0 mb-4">
      <div class="flex flex-row gap-4 w-full">
        <KpiCard label="Total" :value="jobSummary.total" icon="status" color="blue" class="flex-1 min-w-0 h-16 w-40 max-w-xs" />
        <KpiCard label="Running" :value="jobSummary.running" icon="status" color="yellow" class="flex-1 min-w-0 h-16 w-40 max-w-xs" />
        <KpiCard label="Succeeded" :value="jobSummary.succeeded" icon="status" color="green" class="flex-1 min-w-0 h-16 w-40 max-w-xs" />
        <KpiCard label="Failed" :value="jobSummary.failed" icon="status" color="red" class="flex-1 min-w-0 h-16 w-40 max-w-xs" />
      </div>
    </div>
    <!-- Main Card for Filters and Tabbed Tables -->
    <Card title="Job Runs & Logs" subtitle="Filter and search job runs and logs" :contentClass="'pt-0 px-0 pb-2'" class="mb-6">
      <JobFiltersBar :filters="{search}" :placeholder="searchPlaceholder" @updateFilters="onUpdateFilters" class="pt-4"/>
      <div class="bg-card rounded-lg w-full">
        <TabGroup :selectedIndex="activeTab" @change="activeTab = $event">
          <div class="border border-divider rounded-lg bg-card w-full">
            <TabList class="flex space-x-2 px-4 pt-4 bg-card rounded-t-lg border-b border-divider">
              <Tab v-slot="{ selected }" as="template">
                <button
                  :class="[
                    'px-3 py-2 text-sm font-semibold focus:outline-none',
                    selected
                      ? 'bg-card text-text-primary border-b-2 border-white -mb-px z-10'
                      : 'text-text-secondary border-b-2 border-transparent',
                  ]"
                >
                  Job Runs
                </button>
              </Tab>
              <Tab v-slot="{ selected }" as="template">
                <button
                  :class="[
                    'px-3 py-2 text-sm font-semibold focus:outline-none',
                    selected
                      ? 'bg-card text-text-primary border-b-2 border-white -mb-px z-10'
                      : 'text-text-secondary border-b-2 border-transparent',
                  ]"
                >
                  Unified Logs
                </button>
              </Tab>
            </TabList>
            <TabPanels class="p-4">
              <TabPanel>
                <JobRunsTable :jobs="paginatedJobRuns" @show-details="openDetailsModal" />
                <div class="flex justify-between items-center gap-2 mt-2">
                  <div class="flex items-center gap-2">
                    <span class="text-xs">Rows:</span>
                    <select v-model="jobRunsPageSize" @change="setJobRunsPageSize(Number($event.target.value))" class="form-select form-select-xs w-16">
                      <option v-for="size in jobRunsPageSizeOptions" :key="size" :value="size">{{ size }}</option>
                    </select>
                  </div>
                  <div class="flex items-center gap-2">
                    <button class="btn btn-sm" :disabled="jobRunsPage===1" @click="prevJobRunsPage">Prev</button>
                    <span class="text-xs">Page {{ jobRunsPage }} / {{ jobResultsStore.pagination.totalPages }}</span>
                    <button class="btn btn-sm" :disabled="jobRunsPage>=jobResultsStore.pagination.totalPages" @click="nextJobRunsPage">Next</button>
                  </div>
                </div>
              </TabPanel>
              <TabPanel>
                <UnifiedLogsTable :logs="paginatedLogs" @show-meta="openMetaModal" />
                <div class="flex justify-between items-center gap-2 mt-2">
                  <div class="flex items-center gap-2">
                    <span class="text-xs">Rows:</span>
                    <select v-model="logsPageSize" @change="setLogsPageSize(Number($event.target.value))" class="form-select form-select-xs w-16">
                      <option v-for="size in logsPageSizeOptions" :key="size" :value="size">{{ size }}</option>
                    </select>
                  </div>
                  <div class="flex items-center gap-2">
                    <button class="btn btn-sm" :disabled="logsPage===1" @click="prevLogsPage">Prev</button>
                    <span class="text-xs">Page {{ logsPage }} / {{ logStore.pagination.totalPages }}</span>
                    <button class="btn btn-sm" :disabled="logsPage>=logStore.pagination.totalPages" @click="nextLogsPage">Next</button>
                  </div>
                </div>
              </TabPanel>
            </TabPanels>
          </div>
        </TabGroup>
      </div>
    </Card>
    <BaseModal :isOpen="showDetailsModal" title="Job Details" @close="closeDetailsModal">
      <template #content>
        <div v-if="selectedDetails">
          <pre class="bg-gray-100 p-4 rounded text-xs">{{ JSON.stringify(selectedDetails, null, 2) }}</pre>
        </div>
      </template>
    </BaseModal>
    <BaseModal :isOpen="showMetaModal" title="Log Meta Details" @close="closeMetaModal">
      <template #content>
        <div v-if="selectedMeta">
          <pre class="bg-gray-100 p-4 rounded text-xs">{{ JSON.stringify(selectedMeta, null, 2) }}</pre>
        </div>
      </template>
    </BaseModal>
  </PageContainer>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useJobResultsStore } from '../store/job_results'
import { useLogStore } from '../store/log'
import KpiCard from '../components/ui/KpiCard.vue'
import Card from '../components/ui/Card.vue'
import JobRunsTable from '../components/jobs-dashboard/JobRunsTable.vue'
import UnifiedLogsTable from '../components/jobs-dashboard/UnifiedLogsTable.vue'
import JobFiltersBar from '../components/jobs-dashboard/JobFiltersBar.vue'
import { TabGroup, TabList, Tab, TabPanels, TabPanel } from '@headlessui/vue'
import BaseModal from '../components/BaseModal.vue'

// --- State ---
const jobResultsStore = useJobResultsStore()
const logStore = useLogStore()
const jobRunsPage = ref(1)
const jobRunsPageSize = ref(5)
const jobRunsPageSizeOptions = [5, 10, 20, 50]
const isLoading = computed(() => jobResultsStore.isLoading)
const error = computed(() => jobResultsStore.error)

const logsPage = ref(1)
const logsPageSize = ref(5)
const logsPageSizeOptions = [5, 10, 20, 50]
const logsLoading = computed(() => logStore.isLoading)
const logsError = computed(() => logStore.error)

// --- Tab state ---
const activeTab = ref(0) // 0 = Job Runs, 1 = Logs
const search = ref('')

// --- Fetch job results from API ---
async function fetchJobRuns(newSearch = false) {
  if (newSearch) {
    await jobResultsStore.fetchResults(1, { search: search.value })
    jobRunsPage.value = 1
  } else {
    await jobResultsStore.fetchResults(jobRunsPage.value)
  }
}

// --- Fetch logs from API ---
async function fetchLogs(newSearch = false) {
  if (newSearch) {
    await logStore.fetchLogs(1, { search: search.value })
    logsPage.value = 1
  } else {
    await logStore.fetchLogs(logsPage.value)
  }
}

onMounted(() => {
  jobResultsStore.pagination.itemsPerPage = jobRunsPageSize.value
  logStore.pagination.itemsPerPage = logsPageSize.value
  fetchJobRuns()
  fetchLogs()
})

watch([jobRunsPage, jobRunsPageSize], () => {
  jobResultsStore.pagination.itemsPerPage = jobRunsPageSize.value
  fetchJobRuns()
})

watch([logsPage, logsPageSize], () => {
  logStore.pagination.itemsPerPage = logsPageSize.value
  fetchLogs()
})

function onUpdateFilters(newFilters) {
  search.value = newFilters.search
  if (activeTab.value === 0) {
    fetchJobRuns(true)
  } else {
    fetchLogs(true)
  }
}
function nextJobRunsPage() { if (jobRunsPage.value < jobResultsStore.pagination.totalPages) jobRunsPage.value++ }
function prevJobRunsPage() { if (jobRunsPage.value > 1) jobRunsPage.value-- }
function setJobRunsPageSize(size) { jobRunsPageSize.value = size; jobRunsPage.value = 1 }
function nextLogsPage() { if (logsPage.value < logStore.pagination.totalPages) logsPage.value++ }
function prevLogsPage() { if (logsPage.value > 1) logsPage.value-- }
function setLogsPageSize(size) { logsPageSize.value = size; logsPage.value = 1 }

// --- Job summary metrics ---
const jobSummary = computed(() => jobResultsStore.summary)

// --- Job runs table ---
const jobRuns = computed(() => jobResultsStore.results)
const jobRunsTotal = computed(() => jobResultsStore.pagination.totalItems)
const paginatedJobRuns = computed(() => jobRuns.value)

// --- Unified logs table ---
const logs = computed(() => logStore.logs)
const logsTotal = computed(() => logStore.pagination.totalItems)
const paginatedLogs = computed(() => logs.value)

// --- Modal logic (unchanged) ---
const showDetailsModal = ref(false)
const selectedDetails = ref(null)
const showMetaModal = ref(false)
const selectedMeta = ref(null)
function openDetailsModal(details) {
  selectedDetails.value = details
  showDetailsModal.value = true
}
function closeDetailsModal() {
  showDetailsModal.value = false
  selectedDetails.value = null
}
function openMetaModal(meta) {
  selectedMeta.value = meta
  showMetaModal.value = true
}
function closeMetaModal() {
  showMetaModal.value = false
  selectedMeta.value = null
}

// --- Dynamic placeholder for search box ---
const searchPlaceholder = computed(() =>
  activeTab.value === 0 ? 'Search job runs...' : 'Search logs...'
)
</script>

<style scoped>
.bg-card {
  background: var(--nr-bg-card);
}
.border-divider {
  border-color: var(--nr-border);
}
</style> 