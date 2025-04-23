<template>
  <PageContainer title="Jobs Dashboard">
    <!-- Metrics Cards: Grouped in columns with headers -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <!-- Redis Column -->
      <div>
        <div class="text-lg font-semibold text-text-primary mb-3 pl-1 flex flex-col gap-1">
          <span>Redis</span>
          <div class="w-full h-1 bg-white rounded"></div>
        </div>
        <div class="flex flex-col gap-4">
          <MetricCard label="Redis Status" :value="redisStatus" icon="status" color="red" />
          <MetricCard label="Redis Uptime" :value="redisUptime" icon="clock" color="red" />
          <MetricCard label="Redis Memory" :value="redisMemory" icon="memory" color="red" />
        </div>
      </div>
      <!-- RQ Column -->
      <div>
        <div class="text-lg font-semibold text-text-primary mb-3 pl-1 flex flex-col gap-1">
          <span>RQ</span>
          <div class="w-full h-1 bg-white rounded"></div>
        </div>
        <div class="flex flex-col gap-4">
          <MetricCard label="RQ Total Jobs" :value="rqTotalJobs" icon="list" color="yellow" />
          <MetricCard label="RQ Low Queue" :value="rqLowQueue" icon="queue" color="yellow" />
          <MetricCard label="RQ High Queue" :value="rqHighQueue" icon="queue" color="yellow" />
        </div>
      </div>
      <!-- Worker Column -->
      <div>
        <div class="text-lg font-semibold text-text-primary mb-3 pl-1 flex flex-col gap-1">
          <span>Worker</span>
          <div class="w-full h-1 bg-white rounded"></div>
        </div>
        <div class="flex flex-col gap-4">
          <MetricCard label="Worker Status" :value="workerContainerStatus" icon="status" :color="workerContainerStatusColor" />
          <MetricCard label="Worker Status" :value="workerStatus" icon="user-group" color="green" />
          <MetricCard label="Jobs in Progress" :value="jobsInProc" icon="progress" color="green" />
        </div>
      </div>
    </div>
    <!-- Job Types Section -->
    <div class="nr-card flex flex-row items-center gap-4 mb-6 p-4">
      <button
        class="flex items-center gap-2 px-4 py-2 rounded-full bg-green-600 text-white font-medium hover:bg-green-700 transition-colors focus:outline-none focus:ring-2 focus:ring-green-400"
        @click="onCreateJob"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        New Job
      </button>
      <div class="flex flex-col gap-2 flex-1">
        <span class="text-sm font-semibold text-text-secondary mb-1">Job Schedule Filter</span>
        <JobTypesCard
          :job-types="dashboardStore.jobTypes"
          :selected-type="selectedType"
          @select="onJobTypeSelect"
        />
      </div>
    </div>
    <!-- Jobs Table -->
    <div class="nr-card p-0">
      <JobsTableTabs v-model:tab="activeTab" />
      <JobsTableFilter :activeTab="activeTab" :selectedFilters="selectedFilters" @removeFilter="removeFilter" />
      <JobsTable
        :activeTab="activeTab"
        :filters="selectedFilters"
        :scheduled-jobs="filteredScheduledJobs"
        :recent-jobs="dashboardStore.recentJobs"
      />
    </div>
    <div v-if="dashboardStore.loading" class="text-center py-4 text-text-secondary">Loading dashboard...</div>
    <div v-if="dashboardStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
      Error: {{ dashboardStore.error }}
    </div>
    <JobFormModal :is-open="isFormModalOpen" @close="closeFormModal" @save="onJobSaved" />
  </PageContainer>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useJobsDashboardStore } from '../store/jobsDashboard'
import PageContainer from '../components/ui/PageContainer.vue'
import MetricCard from '../components/jobs-dashboard/MetricCard.vue'
import JobTypesCard from '../components/jobs-dashboard/JobTypesCard.vue'
import JobsTableTabs from '../components/jobs-dashboard/JobsTableTabs.vue'
import JobsTableFilter from '../components/jobs-dashboard/JobsTableFilter.vue'
import JobsTable from '../components/jobs-dashboard/JobsTable.vue'
import api from '../services/api'
import JobFormModal from '../components/JobFormModal.vue'

const dashboardStore = useJobsDashboardStore()
const activeTab = ref('scheduled')
const selectedFilters = ref([])
const selectedType = ref('')
const workerContainerStatus = ref('-')
const workerContainerStatusColor = computed(() => workerContainerStatus.value === 'healthy' ? 'green' : 'red')
const isFormModalOpen = ref(false)
const systemHealth = ref({})

onMounted(() => {
  fetchSystemHealth()
  fetchWorkerContainerStatus()
  dashboardStore.fetchAll()
})

function removeFilter(filter) {
  selectedFilters.value = selectedFilters.value.filter(f => f !== filter)
}
function onJobTypeSelect(type) {
  selectedType.value = type
  // Optionally update filters or jobs table here
}
function onCreateJob() {
  isFormModalOpen.value = true
}
function closeFormModal() {
  isFormModalOpen.value = false
}

async function fetchSystemHealth() {
  try {
    const res = await api.get('/system/status')
    systemHealth.value = res.data
  } catch (e) {
    systemHealth.value = {}
  }
}

async function fetchWorkerContainerStatus() {
  try {
    const res = await api.get('/system/status')
    workerContainerStatus.value = res.data.worker || '-'
  } catch (e) {
    workerContainerStatus.value = 'unreachable'
  }
}

// Metric values (computed from store)
const redisStatus = computed(() => {
  const status = systemHealth.value.redis
  if (status && status.toLowerCase() === 'healthy') return 'Healthy'
  if (status && status.toLowerCase() === 'unhealthy') return 'Unhealthy'
  return 'Unknown'
})
const redisUptime = computed(() => {
  const s = systemHealth.value.redis_uptime
  if (!s) return '-'
  const d = Math.floor(s/86400), h = Math.floor((s%86400)/3600)
  return `${d}d, ${h}h`
})
const redisMemory = computed(() => systemHealth.value.redis_memory ? `${(systemHealth.value.redis_memory/1024/1024).toFixed(0)} MB` : '-')
const rqTotalJobs = computed(() => systemHealth.value.rq_queues?.reduce((sum, q) => sum + (q.job_count || 0), 0) || 0)
const rqLowQueue = computed(() => systemHealth.value.rq_queues?.find(q => q.name === 'low')?.job_count || 0)
const rqHighQueue = computed(() => systemHealth.value.rq_queues?.find(q => q.name === 'high')?.job_count || 0)
const workerStatus = computed(() => systemHealth.value.workers?.[0]?.status || 'idle')
const jobsInProc = computed(() => systemHealth.value.workers?.[0]?.jobs_in_progress || 0)

// Filter scheduled jobs by selected type
const filteredScheduledJobs = computed(() => {
  if (!selectedType.value) return dashboardStore.scheduledJobs
  return dashboardStore.scheduledJobs.filter(j => j.job_type === selectedType.value)
})

async function onJobSaved(payload) {
  try {
    await api.post('/jobs/', payload);
    isFormModalOpen.value = false;
    await dashboardStore.fetchScheduledJobs();
    await dashboardStore.fetchRecentJobs();
  } catch (error) {
    // Optionally show error notification here
    console.error('Failed to create job:', error);
  }
}
</script> 