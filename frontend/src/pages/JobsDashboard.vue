<template>
  <PageContainer title="Jobs Dashboard">
    <!-- Top Row: Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <JobTypesCard :job-types="dashboardStore.jobTypes" />
      <RedisStatusCard :status="dashboardStore.systemStatus" />
      <RQQueuesCard :status="dashboardStore.systemStatus" />
      <WorkerStatusCard :status="dashboardStore.systemStatus" />
    </div>
    <!-- Tabs and Filter Bar -->
    <div class="nr-card p-0">
      <JobsTableTabs v-model:tab="activeTab" />
      <JobsTableFilter :activeTab="activeTab" :selectedFilters="selectedFilters" @removeFilter="removeFilter" />
      <JobsTable
        :activeTab="activeTab"
        :filters="selectedFilters"
        :scheduled-jobs="dashboardStore.scheduledJobs"
        :recent-jobs="dashboardStore.recentJobs"
      />
    </div>
    <div v-if="dashboardStore.loading" class="text-center py-4 text-text-secondary">Loading dashboard...</div>
    <div v-if="dashboardStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
      Error: {{ dashboardStore.error }}
    </div>
  </PageContainer>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useJobsDashboardStore } from '../store/jobsDashboard'
import PageContainer from '../components/ui/PageContainer.vue'
import JobTypesCard from '../components/jobs-dashboard/JobTypesCard.vue'
import RedisStatusCard from '../components/jobs-dashboard/RedisStatusCard.vue'
import RQQueuesCard from '../components/jobs-dashboard/RQQueuesCard.vue'
import WorkerStatusCard from '../components/jobs-dashboard/WorkerStatusCard.vue'
import JobsTableTabs from '../components/jobs-dashboard/JobsTableTabs.vue'
import JobsTableFilter from '../components/jobs-dashboard/JobsTableFilter.vue'
import JobsTable from '../components/jobs-dashboard/JobsTable.vue'

const dashboardStore = useJobsDashboardStore()
const activeTab = ref('scheduled')
const selectedFilters = ref([])

onMounted(() => {
  dashboardStore.fetchAll()
})

function removeFilter(filter) {
  selectedFilters.value = selectedFilters.value.filter(f => f !== filter)
}
</script> 