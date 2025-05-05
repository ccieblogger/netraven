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
      <JobFiltersBar :filters="filters" @updateFilters="onUpdateFilters" class="pt-4"/>
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
                <JobRunsTable :jobs="jobRuns" @show-details="openDetailsModal" />
              </TabPanel>
              <TabPanel>
                <UnifiedLogsTable :logs="unifiedLogs" />
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
  </PageContainer>
</template>

<script setup>
import { ref } from 'vue'
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
  { id: 101, timestamp: '2025-05-01 10:01', level: 'info', message: 'Job started', job_id: 1 },
  { id: 102, timestamp: '2025-05-01 10:02', level: 'error', message: 'Device unreachable', job_id: 1 },
  { id: 103, timestamp: '2025-05-01 09:01', level: 'info', message: 'Job completed', job_id: 2 },
])
const showDetailsModal = ref(false)
const selectedDetails = ref(null)
function onUpdateFilters(newFilters) { filters.value = newFilters }
function openDetailsModal(details) {
  selectedDetails.value = details
  showDetailsModal.value = true
}
function closeDetailsModal() {
  showDetailsModal.value = false
  selectedDetails.value = null
}
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