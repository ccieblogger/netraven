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
      <JobFiltersBar :filters="filters" :jobNames="jobNames" :jobTypes="jobTypes" @updateFilters="onUpdateFilters" class="pt-4"/>
      <div class="bg-card rounded-lg w-full">
        <TabGroup>
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
                    <span class="text-xs">Page {{ jobRunsPage }} / {{ Math.ceil(jobRunsTotal/jobRunsPageSize) }}</span>
                    <button class="btn btn-sm" :disabled="jobRunsPage*jobRunsPageSize>=jobRunsTotal" @click="nextJobRunsPage">Next</button>
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
                    <span class="text-xs">Page {{ logsPage }} / {{ Math.ceil(logsTotal/logsPageSize) }}</span>
                    <button class="btn btn-sm" :disabled="logsPage*logsPageSize>=logsTotal" @click="nextLogsPage">Next</button>
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
import { ref, computed } from 'vue'
import KpiCard from '../components/ui/KpiCard.vue'
import Card from '../components/ui/Card.vue'
import JobRunsTable from '../components/jobs-dashboard/JobRunsTable.vue'
import UnifiedLogsTable from '../components/jobs-dashboard/UnifiedLogsTable.vue'
import JobFiltersBar from '../components/jobs-dashboard/JobFiltersBar.vue'
import { TabGroup, TabList, Tab, TabPanels, TabPanel } from '@headlessui/vue'
import BaseModal from '../components/BaseModal.vue'
// Phase 1: mock data only
const jobSummary = ref({ total: 12, running: 2, succeeded: 8, failed: 2 })
const filters = ref({ status: '', type: '', search: '' })
const jobRuns = ref([
  {
    id: 1,
    job_name: 'Backup Core',
    device_name: 'Router1',
    job_type: 'Backup',
    status: 'Running',
    result_time: '2025-05-01T10:00:00Z',
    details: { result: 'Partial', errors: ['Device unreachable: Switch2'] },
    created_at: '2025-05-01T09:59:00Z',
  },
  {
    id: 2,
    job_name: 'Audit Edge',
    device_name: 'Switch2',
    job_type: 'Audit',
    status: 'Succeeded',
    result_time: '2025-05-01T09:00:00Z',
    details: { result: 'Success', notes: 'All checks passed.' },
    created_at: '2025-05-01T08:59:00Z',
  },
  {
    id: 3,
    job_name: 'Config Pull',
    device_name: 'Firewall1',
    job_type: 'Config',
    status: 'Failed',
    result_time: '2025-04-30T22:00:00Z',
    details: { result: 'Failed', errors: ['Timeout'] },
    created_at: '2025-04-30T21:59:00Z',
  },
])
const unifiedLogs = ref([
  {
    id: 101,
    timestamp: '2025-05-01T10:01:00Z',
    log_type: 'job',
    level: 'info',
    job_id: 1,
    device_id: 1,
    source: 'worker.executor',
    message: 'Job started',
    meta: { user: 'admin', extra: 'Started by scheduler' },
  },
  {
    id: 102,
    timestamp: '2025-05-01T10:02:00Z',
    log_type: 'job',
    level: 'error',
    job_id: 1,
    device_id: 2,
    source: 'worker.executor',
    message: 'Device unreachable',
    meta: { error: 'Timeout', ip: '10.0.0.2' },
  },
  {
    id: 103,
    timestamp: '2025-05-01T09:01:00Z',
    log_type: 'job',
    level: 'info',
    job_id: 2,
    device_id: 2,
    source: 'worker.executor',
    message: 'Job completed',
    meta: { duration: '1m', result: 'success' },
  },
])
const showDetailsModal = ref(false)
const selectedDetails = ref(null)
const showMetaModal = ref(false)
const selectedMeta = ref(null)
const jobNames = computed(() => Array.from(new Set(jobRuns.value.map(j => j.job_name))))
const jobTypes = computed(() => Array.from(new Set(jobRuns.value.map(j => j.job_type))))
function onUpdateFilters(newFilters) { filters.value = newFilters }
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
const jobRunsPage = ref(1)
const jobRunsPageSize = ref(5)
const jobRunsPageSizeOptions = [5, 10, 20, 50]
const jobRunsTotal = computed(() => jobRuns.value.length)
const paginatedJobRuns = computed(() => jobRuns.value.slice((jobRunsPage.value-1)*jobRunsPageSize.value, jobRunsPage.value*jobRunsPageSize.value))
function nextJobRunsPage() { if (jobRunsPage.value * jobRunsPageSize.value < jobRunsTotal.value) jobRunsPage.value++ }
function prevJobRunsPage() { if (jobRunsPage.value > 1) jobRunsPage.value-- }
function setJobRunsPageSize(size) { jobRunsPageSize.value = size; jobRunsPage.value = 1 }

const logsPage = ref(1)
const logsPageSize = ref(5)
const logsPageSizeOptions = [5, 10, 20, 50]
const logsTotal = computed(() => unifiedLogs.value.length)
const paginatedLogs = computed(() => unifiedLogs.value.slice((logsPage.value-1)*logsPageSize.value, logsPage.value*logsPageSize.value))
function nextLogsPage() { if (logsPage.value * logsPageSize.value < logsTotal.value) logsPage.value++ }
function prevLogsPage() { if (logsPage.value > 1) logsPage.value-- }
function setLogsPageSize(size) { logsPageSize.value = size; logsPage.value = 1 }
// TODO: Phase 2 - Replace mock data with API integration
</script>

<style scoped>
.bg-card {
  background: var(--nr-bg-card);
}
.border-divider {
  border-color: var(--nr-border);
}
</style> 