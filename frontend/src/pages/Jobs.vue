<template>
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-semibold mb-4">Manage Jobs</h1>

    <!-- Add Job Button -->
    <div class="mb-4 text-right">
      <button @click="openCreateModal" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
        + Add Job
      </button>
    </div>

    <!-- Loading/Error Indicators -->
    <div v-if="jobStore.isLoading" class="text-center py-4">Loading Jobs...</div>
    <div v-if="jobStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
       Error loading jobs: {{ jobStore.error }}
    </div>
    <!-- Job Run Status Indicator -->
     <div v-if="jobStore.runStatus" :class="runStatusClass" class="px-4 py-3 rounded relative mb-4" role="alert">
       <span v-if="jobStore.runStatus.status === 'running'">Triggering job {{ jobStore.runStatus.jobId }}...</span>
       <span v-if="jobStore.runStatus.status === 'queued'">Job {{ jobStore.runStatus.jobId }} queued successfully (RQ ID: {{ jobStore.runStatus.data?.queue_job_id }}).</span>
       <span v-if="jobStore.runStatus.status === 'failed'">Failed to trigger job {{ jobStore.runStatus.jobId }}: {{ jobStore.runStatus.error }}</span>
    </div>

    <!-- Jobs Table -->
    <div v-if="!jobStore.isLoading && jobs.length > 0" class="bg-white shadow-md rounded my-6">
      <table class="min-w-max w-full table-auto">
        <thead>
          <tr class="bg-gray-200 text-gray-600 uppercase text-sm leading-normal">
            <th class="py-3 px-6 text-left">ID</th>
            <th class="py-3 px-6 text-left">Name</th>
            <th class="py-3 px-6 text-left">Description</th>
            <th class="py-3 px-6 text-center">Enabled</th>
            <th class="py-3 px-6 text-left">Schedule</th>
            <th class="py-3 px-6 text-left">Tags</th>
             <th class="py-3 px-6 text-left">Last Status</th>
            <th class="py-3 px-6 text-center">Actions</th>
          </tr>
        </thead>
        <tbody class="text-gray-600 text-sm font-light">
          <tr v-for="job in jobs" :key="job.id" class="border-b border-gray-200 hover:bg-gray-100">
            <td class="py-3 px-6 text-left whitespace-nowrap">{{ job.id }}</td>
            <td class="py-3 px-6 text-left">{{ job.name }}</td>
            <td class="py-3 px-6 text-left">{{ job.description || '-' }}</td>
            <td class="py-3 px-6 text-center">
               <span :class="job.is_enabled ? 'bg-green-200 text-green-600' : 'bg-gray-200 text-gray-600'" class="py-1 px-3 rounded-full text-xs">
                {{ job.is_enabled ? 'Yes' : 'No' }}
               </span>
            </td>
            <td class="py-3 px-6 text-left text-xs">
                <div v-if="job.schedule_type === 'interval'">Interval: {{ job.interval_seconds }}s</div>
                <div v-else-if="job.schedule_type === 'cron'">Cron: {{ job.cron_string }}</div>
                <div v-else-if="job.schedule_type === 'onetime'">Once @ {{ formatDateTime(job.scheduled_for) }}</div>
                <div v-else>-</div>
            </td>
            <td class="py-3 px-6 text-left">
               <span v-for="tag in job.tags" :key="tag.id" class="bg-blue-100 text-blue-600 py-1 px-3 rounded-full text-xs mr-1">
                 {{ tag.name }}
               </span>
               <span v-if="!job.tags || job.tags.length === 0">-</span>
            </td>
             <td class="py-3 px-6 text-left">
                <span :class="statusClass(job.status)" class="py-1 px-3 rounded-full text-xs">
                    {{ job.status }}
                </span>
            </td>
            <td class="py-3 px-6 text-center">
              <div class="flex item-center justify-center">
                 <button @click="triggerRun(job)" title="Run Job Now" class="w-4 mr-2 transform hover:text-green-500 hover:scale-110">▶️</button>
                 <button @click="openEditModal(job)" title="Edit Job" class="w-4 mr-2 transform hover:text-purple-500 hover:scale-110">✏️</button>
                 <button @click="confirmDelete(job)" title="Delete Job" class="w-4 mr-2 transform hover:text-red-500 hover:scale-110">🗑️</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- No Jobs Message -->
    <div v-if="!jobStore.isLoading && jobs.length === 0" class="text-center text-gray-500 py-6">
      No jobs found. Add one!
    </div>

    <!-- TODO: Add Create/Edit Modal Component (requires tag selection, schedule inputs) -->

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useJobStore } from '../store/job'

const jobStore = useJobStore()
const jobs = computed(() => jobStore.jobs)

// Modal state placeholders
const showModal = ref(false)
const selectedJob = ref(null)
const isEditMode = ref(false)

onMounted(() => {
  jobStore.fetchJobs()
})

// --- Helper Functions ---
function formatDateTime(dateTimeString) {
  if (!dateTimeString) return '-';
  try {
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(dateTimeString).toLocaleString(undefined, options);
  } catch (e) {
    return dateTimeString; // Return original if formatting fails
  }
}

function statusClass(status) {
  if (!status) return 'bg-gray-200 text-gray-600';
  status = status.toLowerCase();
  if (status.includes('success')) return 'bg-green-200 text-green-600';
  if (status.includes('fail') || status.includes('error')) return 'bg-red-200 text-red-600';
  if (status.includes('running') || status.includes('pending') || status.includes('queued')) return 'bg-yellow-200 text-yellow-600';
  return 'bg-gray-200 text-gray-600'; // Default
}

const runStatusClass = computed(() => {
  if (!jobStore.runStatus) return '';
  switch (jobStore.runStatus.status) {
    case 'running': return 'bg-yellow-100 border border-yellow-400 text-yellow-700';
    case 'queued': return 'bg-blue-100 border border-blue-400 text-blue-700';
    case 'failed': return 'bg-red-100 border border-red-400 text-red-700';
    default: return '';
  }
});

// --- Action Handlers ---
function openCreateModal() {
  alert('Placeholder: Open Create Job Modal');
}
function openEditModal(job) {
   alert(`Placeholder: Open Edit Job Modal for ${job.name}`);
}
function confirmDelete(job) {
  if (confirm(`Are you sure you want to delete the job "${job.name}"? This cannot be undone.`)) {
     alert(`Placeholder: Delete job ${job.id}`);
     // jobStore.deleteJob(job.id);
  }
}

function triggerRun(job) {
   if (confirm(`Trigger job "${job.name}" to run now?`)) {
     jobStore.runJobNow(job.id);
   }
}

function closeModal() { /* ... */ }
async function handleSave(data) { /* ... */ }

</script>

<style scoped>
/* Add any page-specific styles */
</style>
