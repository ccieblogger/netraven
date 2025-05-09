<template>
  <PageContainer title="Jobs" subtitle="Manage and monitor automation jobs">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-semibold">Jobs</h2>
      <button class="btn btn-primary" @click="openCreateModal">+ Schedule Job</button>
    </div>
    <JobList
      :jobs="filteredJobsWithNextRun"
      :job-types="jobTypes"
      :is-loading="isLoading"
      :filters="filters"
      @run="runJob"
      @edit="openEditModal"
      @delete="openDeleteModal"
      @details="openDetailsModal"
      @update:filters="val => { filters.value = val }"
    />
    <JobFormModal
      v-if="showFormModal"
      :is-open="showFormModal"
      :job-to-edit="selectedJob"
      @close="closeFormModal"
      @save="handleSaveJob"
    />
    <BaseModal :isOpen="showDetailsModal" title="Job Details" @close="closeDetailsModal">
      <template #content>
        <div v-if="selectedDetails">
          <pre class="bg-gray-100 p-4 rounded text-xs">{{ JSON.stringify(selectedDetails, null, 2) }}</pre>
        </div>
      </template>
    </BaseModal>
    <BaseModal :isOpen="showDeleteModal" title="Delete Job" @close="closeDeleteModal">
      <template #content>
        <div>Are you sure you want to delete job <b>{{ selectedJob?.name }}</b>?</div>
        <div class="mt-4 flex gap-2">
          <button class="btn btn-danger" @click="confirmDeleteJob">Delete</button>
          <button class="btn" @click="closeDeleteModal">Cancel</button>
        </div>
      </template>
    </BaseModal>
  </PageContainer>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useJobStore } from '../store/job'
import { useJobsDashboardStore } from '../store/jobsDashboard'
import JobFormModal from '../components/JobFormModal.vue'
import BaseModal from '../components/BaseModal.vue'
import JobList from '../components/jobs-dashboard/JobList.vue'
import { CloudArrowDownIcon, SignalIcon, QuestionMarkCircleIcon } from '@heroicons/vue/24/outline'

const jobStore = useJobStore()
const jobsDashboardStore = useJobsDashboardStore()
const isLoading = computed(() => jobStore.isLoading)
const jobs = computed(() => jobStore.jobs)
const jobTypes = computed(() => jobsDashboardStore.jobTypes)
const scheduledJobs = computed(() => jobsDashboardStore.scheduledJobs)

const filters = ref({ name: '', type: '', status: '' })

const showFormModal = ref(false)
const showDetailsModal = ref(false)
const showDeleteModal = ref(false)
const selectedJob = ref(null)
const selectedDetails = ref(null)

function openCreateModal() {
  selectedJob.value = null
  showFormModal.value = true
}
function openEditModal(job) {
  selectedJob.value = { ...job }
  showFormModal.value = true
}
function closeFormModal() {
  showFormModal.value = false
  selectedJob.value = null
}
function openDetailsModal(job) {
  selectedDetails.value = job
  showDetailsModal.value = true
}
function closeDetailsModal() {
  showDetailsModal.value = false
  selectedDetails.value = null
}
function openDeleteModal(job) {
  selectedJob.value = job
  showDeleteModal.value = true
}
function closeDeleteModal() {
  showDeleteModal.value = false
  selectedJob.value = null
}
async function confirmDeleteJob() {
  if (!selectedJob.value) return
  await jobStore.deleteJob(selectedJob.value.id)
  closeDeleteModal()
  jobStore.fetchJobs()
}
async function handleSaveJob(payload) {
  let success = false;
  if (!selectedJob.value) {
    // Create mode
    success = await jobStore.createJob(payload);
  } else {
    // Edit mode
    success = await jobStore.updateJob(payload.id, payload);
  }
  if (success) {
    closeFormModal();
    jobStore.fetchJobs();
  }
}
async function runJob(job) {
  await jobStore.runJobNow(job.id)
  jobStore.fetchJobs()
}

// Join jobs with scheduledJobs by id to add next_run
const jobsWithNextRun = computed(() => {
  const schedMap = Object.fromEntries((scheduledJobs.value || []).map(j => [j.id, j.next_run]))
  return jobs.value.map(j => ({ ...j, next_run: schedMap[j.id] }))
})

const filteredJobsWithNextRun = computed(() => {
  let result = jobsWithNextRun.value
  if (filters.value.name) {
    result = result.filter(j => j.name && j.name.toLowerCase().includes(filters.value.name.toLowerCase()))
  }
  if (filters.value.type) {
    result = result.filter(j => j.job_type === filters.value.type)
  }
  if (filters.value.status) {
    result = result.filter(j => (j.status || '').toLowerCase() === filters.value.status.toLowerCase())
  }
  return result
})

function labelForType(jobType) {
  const type = jobTypes.value.find(t => t.job_type === jobType)
  return type ? type.label : jobType
}
function iconForType(jobType) {
  const type = jobTypes.value.find(t => t.job_type === jobType)
  if (!type) return QuestionMarkCircleIcon
  if (type.icon === 'BackupIcon') return CloudArrowDownIcon
  if (type.icon === 'NetworkCheckIcon') return SignalIcon
  return QuestionMarkCircleIcon
}
function formatDate(dt) {
  if (!dt) return '-'
  try {
    return new Date(dt).toLocaleString()
  } catch {
    return dt
  }
}
onMounted(() => {
  jobStore.fetchJobs()
  jobsDashboardStore.fetchJobTypes()
  jobsDashboardStore.fetchScheduledJobs()
})
</script>
