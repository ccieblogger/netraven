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
    <Card title="Job Runs & Logs" subtitle="Filter and search job runs and logs" :contentClass="'pt-0 px-0 pb-2'">
      <JobFiltersBar :filters="filters" @updateFilters="onUpdateFilters" />
      <TabView v-model:activeIndex="activeTab">
        <TabPanel header="Job Runs">
          <JobRunsTable :jobs="jobRuns" />
        </TabPanel>
        <TabPanel header="Unified Logs">
          <UnifiedLogsTable :logs="unifiedLogs" />
        </TabPanel>
      </TabView>
    </Card>
    <!-- Minimal TabView Test Block -->
    <TabView>
      <TabPanel header="Test Tab 1">
        <div style="color:white">Tab 1 Content</div>
      </TabPanel>
      <TabPanel header="Test Tab 2">
        <div style="color:white">Tab 2 Content</div>
      </TabPanel>
    </TabView>
  </PageContainer>
</template>

<script setup>
import { ref } from 'vue'
import KpiCard from '../components/ui/KpiCard.vue'
import Card from '../components/ui/Card.vue'
import JobRunsTable from '../components/jobs-dashboard/JobRunsTable.vue'
import UnifiedLogsTable from '../components/jobs-dashboard/UnifiedLogsTable.vue'
import JobFiltersBar from '../components/jobs-dashboard/JobFiltersBar.vue'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
// Phase 1: mock data only
const jobSummary = ref({ total: 12, running: 2, succeeded: 8, failed: 2 })
const filters = ref({ status: '', type: '', search: '' })
const jobRuns = ref([
  { id: 1, name: 'Backup Core', status: 'Running', started: '2025-05-01 10:00', devices: 5 },
  { id: 2, name: 'Audit Edge', status: 'Succeeded', started: '2025-05-01 09:00', devices: 3 },
  { id: 3, name: 'Config Pull', status: 'Failed', started: '2025-04-30 22:00', devices: 2 },
])
const unifiedLogs = ref([
  { id: 101, timestamp: '2025-05-01 10:01', level: 'info', message: 'Job started', job_id: 1 },
  { id: 102, timestamp: '2025-05-01 10:02', level: 'error', message: 'Device unreachable', job_id: 1 },
  { id: 103, timestamp: '2025-05-01 09:01', level: 'info', message: 'Job completed', job_id: 2 },
])
const activeTab = ref(0)
function onUpdateFilters(newFilters) { filters.value = newFilters }
// TODO: Phase 2 - Replace mock data with API integration
</script> 