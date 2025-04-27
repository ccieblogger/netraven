<template>
  <div class="w-full bg-content text-text-primary p-4">
    <h1 class="text-2xl font-semibold mb-4 text-text-primary">Manage Jobs</h1>

    <!-- Jobs Filter Bar (Theme-Aligned, Single Search, Flex Aligned) -->
    <div class="flex flex-row flex-wrap items-center gap-2 mb-2 px-2 bg-card rounded-card border border-divider shadow-md justify-center mx-auto">
      <ResourceFilter
        title=""
        :filterFields="[...filterFields, { name: 'search', label: 'Search', type: 'text', placeholder: 'Search jobs...' }]"
        :initialFilters="filters"
        @filter="applyFilters"
        @reset="resetFilters"
        class="flex flex-row gap-2 items-center min-w-0 mb-0"
        style="background:none; box-shadow:none; border:none; padding:0;"
      />
      <button @click="openCreateJobModal" class="bg-primary hover:bg-primary-dark text-white font-bold py-1 px-3 rounded whitespace-nowrap ml-2 text-sm h-10 flex items-center">
        + Add Job
      </button>
    </div>

    <!-- Loading/Error Indicators -->
    <div v-if="jobStore.isLoading && jobs.length === 0" class="text-center py-4">Loading Jobs...</div>
    <div v-if="jobStore.error" class="bg-error/10 border border-error text-error px-4 py-3 rounded relative mb-4" role="alert">
       Error loading jobs: {{ jobStore.error }}
    </div>
    <!-- Job Run Status Indicator -->
     <div v-if="jobStore.runStatus" :class="runStatusClass" class="px-4 py-3 rounded relative mb-4 transition-opacity duration-300" role="alert">
       <span v-if="jobStore.runStatus.status === 'running'">Triggering job {{ jobStore.runStatus.jobId }}...</span>
       <span v-if="jobStore.runStatus.status === 'queued'">Job {{ jobStore.runStatus.jobId }} queued successfully (RQ ID: {{ jobStore.runStatus.data?.queue_job_id }}).</span>
       <span v-if="jobStore.runStatus.status === 'failed'">Failed to trigger job {{ jobStore.runStatus.jobId }}: {{ jobStore.runStatus.error }}</span>
    </div>

    <!-- Jobs Table (Theme-Aligned, Improved Contrast & Status) -->
    <div v-if="jobs.length > 0" class="bg-card shadow-md rounded-card mb-4 overflow-x-auto border border-divider">
      <table class="min-w-max w-full table-auto text-sm">
        <thead>
          <tr class="bg-content text-text-secondary uppercase text-xs leading-tight">
            <th class="py-2 px-3 text-left">ID</th>
            <th class="py-2 px-3 text-left">Type</th>
            <th class="py-2 px-3 text-left">Devices</th>
            <th class="py-2 px-3 text-left">Status</th>
            <th class="py-2 px-3 text-left">Duration</th>
            <th class="py-2 px-3 text-center">Action</th>
          </tr>
        </thead>
        <tbody class="text-text-primary">
          <tr v-for="job in jobs" :key="job.id" class="border-b border-divider hover:bg-content/50">
            <td class="py-2 px-3 whitespace-nowrap">{{ job.id }}</td>
            <td class="py-2 px-3 whitespace-nowrap">{{ job.job_type || '-' }}</td>
            <td class="py-2 px-3 whitespace-nowrap">{{ job.devices ? job.devices.length : (job.device_count || '-') }}</td>
            <td class="py-2 px-3 whitespace-nowrap text-center align-middle">
              <span v-if="getStatusIcon(job.status)" :aria-label="getStatusIcon(job.status).label" :title="getStatusIcon(job.status).label" class="flex items-center justify-center h-6 w-6 mx-auto">
                <component :is="getStatusIcon(job.status).icon" :class="'h-6 w-6 ' + getStatusIcon(job.status).color" />
              </span>
            </td>
            <td class="py-2 px-3 whitespace-nowrap">{{ formatDuration(job.duration_secs || job.duration) }}</td>
            <td class="py-2 px-3 text-center whitespace-nowrap">
              <router-link 
                :to="`/jobs/${job.id}`" 
                title="Monitor Job"
                class="inline-flex items-center justify-center bg-primary/10 hover:bg-primary/20 text-primary font-semibold px-2 py-0.5 rounded-full transition-colors text-xs"
                aria-label="Monitor Job"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                Monitor
              </router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- No Jobs Message -->
    <div v-if="!jobStore.isLoading && jobs.length === 0" class="text-center text-gray-500 py-6">
      No jobs found. Add one!
    </div>

    <!-- Create/Edit Job Modal -->
     <JobFormModal
        :is-open="isFormModalOpen"
        :job-to-edit="selectedJob"
        @close="closeFormModal"
        @save="handleSaveJob"
      />

     <!-- Delete Confirmation Modal -->
      <DeleteConfirmationModal
        :is-open="isDeleteModalOpen"
        item-type="job"
        :item-name="jobToDelete?.name"
        @close="closeDeleteModal"
        @confirm="handleDeleteJobConfirm"
      />

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useJobStore } from '../store/job'
import { useRouter } from 'vue-router'
import JobFormModal from '../components/JobFormModal.vue'
import DeleteConfirmationModal from '../components/DeleteConfirmationModal.vue'
import { PencilIcon, TrashIcon, PlayIcon } from '@heroicons/vue/24/outline'
import ResourceFilter from '../components/ResourceFilter.vue'
// Import solid Heroicons for status
import { 
  CheckCircleIcon, 
  ExclamationCircleIcon, 
  XCircleIcon, 
  ArrowPathIcon, 
  ClockIcon, 
  QueueListIcon, 
  MinusCircleIcon, 
  QuestionMarkCircleIcon 
} from '@heroicons/vue/24/solid'

const jobStore = useJobStore()
const router = useRouter()
const jobs = computed(() => {
  // Apply filters to jobStore.jobs
  let filtered = jobStore.jobs
  if (!filtered) return []
  // Type filter
  if (filters.value.type) {
    filtered = filtered.filter(j => j.job_type === filters.value.type)
  }
  // Status filter
  if (filters.value.status) {
    filtered = filtered.filter(j => (j.status || j.last_status) === filters.value.status)
  }
  // Date filter (scheduled_for or started_at)
  if (filters.value.date) {
    const dateStr = filters.value.date
    filtered = filtered.filter(j => {
      const dt = j.scheduled_for || j.started_at
      if (!dt) return false
      return dt.startsWith(dateStr)
    })
  }
  // Search filter (name, description, id)
  if (filters.value.search) {
    const q = filters.value.search.toLowerCase()
    filtered = filtered.filter(j =>
      (j.name && j.name.toLowerCase().includes(q)) ||
      (j.description && j.description.toLowerCase().includes(q)) ||
      (String(j.id).includes(q))
    )
  }
  return filtered
})

// Modal States
const isFormModalOpen = ref(false)
const selectedJob = ref(null) // null for create, job object for edit
const isDeleteModalOpen = ref(false)
const jobToDelete = ref(null)

// Filter state
const filters = ref({ type: '', status: '', date: '', search: '' })
const filterFields = [
  { name: 'type', label: 'Type', type: 'select', options: [
    { value: '', label: 'All Types' },
    { value: 'device_backup', label: 'Device Backup' },
    { value: 'reachability', label: 'Reachability' },
    // Add more job types as needed
  ] },
  { name: 'status', label: 'Status', type: 'select', options: [
    { value: '', label: 'All Statuses' },
    { value: 'success', label: 'Success' },
    { value: 'failed', label: 'Failed' },
    { value: 'running', label: 'Running' },
    { value: 'queued', label: 'Queued' },
  ] },
  { name: 'date', label: 'Date', type: 'date' },
]

onMounted(() => {
    // Fetch jobs only if the list is empty initially
    if (jobs.value.length === 0) {
         jobStore.fetchJobs()
    }
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

// Status class based on job run status (API response)
const runStatusClass = computed(() => {
  if (!jobStore.runStatus) return '';
  switch (jobStore.runStatus.status) {
    case 'running': return 'bg-yellow-100 border border-yellow-400 text-yellow-700';
    case 'queued': return 'bg-blue-100 border border-blue-400 text-blue-700';
    case 'failed': return 'bg-red-100 border border-red-400 text-red-700';
    default: return '';
  }
});

// Add a helper for duration formatting
function formatDuration(seconds) {
  if (!seconds) return '-';
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return m > 0 ? `${m} min${m > 1 ? 's' : ''} ${s}s` : `${s}s`
}

// Add statusBadgeClass helper
function statusBadgeClass(status) {
  switch (status) {
    case 'success': return 'bg-green-100 text-green-800';
    case 'failed': return 'bg-red-100 text-red-800';
    case 'running':
    case 'queued': return 'bg-yellow-100 text-yellow-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}

// --- Helper Functions ---
function getStatusIcon(status) {
  // Map job.status to icon, color, label, and animation
  switch (status) {
    case 'completed_success':
    case 'success':
    case 'completed':
      return {
        icon: CheckCircleIcon,
        color: 'text-green-400',
        label: 'Completed (Success)'
      }
    case 'completed_failed':
      return {
        icon: ExclamationCircleIcon,
        color: 'text-yellow-400',
        label: 'Completed (Task Failed)'
      }
    case 'failed_error':
    case 'failed':
    case 'error':
      return {
        icon: XCircleIcon,
        color: 'text-red-400',
        label: 'Job Failed (Error)'
      }
    case 'running':
      return {
        icon: ArrowPathIcon,
        color: 'text-yellow-400 animate-spin',
        label: 'Running'
      }
    case 'pending':
      return {
        icon: ClockIcon,
        color: 'text-yellow-300',
        label: 'Pending'
      }
    case 'queued':
      return {
        icon: QueueListIcon,
        color: 'text-blue-400',
        label: 'Queued'
      }
    case 'cancelled':
      return {
        icon: MinusCircleIcon,
        color: 'text-gray-400',
        label: 'Cancelled'
      }
    case 'no_devices':
      return {
        icon: ExclamationCircleIcon,
        color: 'text-gray-400',
        label: 'No Devices'
      }
    default:
      return {
        icon: QuestionMarkCircleIcon,
        color: 'text-gray-400',
        label: 'Unknown'
      }
  }
}

// --- Action Handlers ---

// Form Modal
function openCreateJobModal() {
  selectedJob.value = null
  isFormModalOpen.value = true
}

function openEditJobModal(job) {
  selectedJob.value = { ...job } // Pass copy
  isFormModalOpen.value = true
}

function closeFormModal() {
  isFormModalOpen.value = false
  selectedJob.value = null
}

async function handleSaveJob(jobData) {
  console.log("Saving job:", jobData);
  let success = false;
  try {
      if (jobData.id) {
          await jobStore.updateJob(jobData.id, jobData);
      } else {
          await jobStore.createJob(jobData);
      }
      success = true;
      closeFormModal();
      // jobStore.fetchJobs(); // Refresh if not reactive
  } catch (error) {
      console.error("Failed to save job:", error);
      // Show error from store action directly
      alert(`Error saving job: ${jobStore.error || 'An unknown error occurred.'}`);
      // Do NOT close modal on error
  }
}

// Delete Modal
function openDeleteJobModal(job) {
  jobToDelete.value = job
  isDeleteModalOpen.value = true
}

function closeDeleteModal() {
  isDeleteModalOpen.value = false
  jobToDelete.value = null
}

async function handleDeleteJobConfirm() {
  if (!jobToDelete.value) return;
  console.log("Deleting job:", jobToDelete.value.id);
  let success = false;
  try {
      await jobStore.deleteJob(jobToDelete.value.id);
      success = true;
      closeDeleteModal();
      // jobStore.fetchJobs(); // Refresh if not reactive
  } catch (error) {
      console.error("Failed to delete job:", error);
      alert(`Error deleting job: ${jobStore.error || 'An unknown error occurred.'}`);
      // Close modal even on error
      closeDeleteModal();
  }
}

// Run Job
async function runJobNow(job) {
   if (confirm(`Trigger job "${job.name}" (ID: ${job.id}) to run now?`)) {
     try {
       await jobStore.runJobNow(job.id);
       // Navigate to the job monitor page if successfully queued
       if (jobStore.runStatus && jobStore.runStatus.status === 'queued') {
         router.push(`/jobs/${job.id}`);
       }
     } catch (error) {
       console.error("Failed to run job:", error);
     }
   }
}

function applyFilters(newFilters) {
  filters.value = { ...filters.value, ...newFilters }
  // Filtering logic will be implemented in the next step
}
function resetFilters() {
  filters.value = { type: '', status: '', date: '', search: '' }
  // Filtering logic will be implemented in the next step
}

</script>
