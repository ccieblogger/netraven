<template>
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-semibold mb-4">Manage Jobs</h1>

    <!-- Add Job Button -->
    <div class="mb-4 text-right">
      <button @click="openCreateJobModal" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
        + Add Job
      </button>
    </div>

    <!-- Loading/Error Indicators -->
    <div v-if="jobStore.isLoading && jobs.length === 0" class="text-center py-4">Loading Jobs...</div>
    <div v-if="jobStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
       Error loading jobs: {{ jobStore.error }}
    </div>
    <!-- Job Run Status Indicator -->
     <div v-if="jobStore.runStatus" :class="runStatusClass" class="px-4 py-3 rounded relative mb-4 transition-opacity duration-300" role="alert">
       <span v-if="jobStore.runStatus.status === 'running'">Triggering job {{ jobStore.runStatus.jobId }}...</span>
       <span v-if="jobStore.runStatus.status === 'queued'">Job {{ jobStore.runStatus.jobId }} queued successfully (RQ ID: {{ jobStore.runStatus.data?.queue_job_id }}).</span>
       <span v-if="jobStore.runStatus.status === 'failed'">Failed to trigger job {{ jobStore.runStatus.jobId }}: {{ jobStore.runStatus.error }}</span>
    </div>

    <!-- Jobs Table -->
     <div v-if="jobs.length > 0" class="bg-white shadow-md rounded my-6" :class="{ 'opacity-50': jobStore.isLoading }">
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
                <span class="py-1 px-3 rounded-full text-xs bg-gray-200 text-gray-600">
                   N/A
                </span>
            </td>
            <td class="py-3 px-6 text-center">
              <div class="flex item-center justify-center">
                 <button @click="runJobNow(job)" title="Run Job Now" class="w-4 mr-2 transform hover:text-green-500 hover:scale-110">
                    <PlayIcon class="h-4 w-4" />
                 </button>
                 <router-link 
                   :to="`/jobs/${job.id}`" 
                   title="Monitor Job"
                   class="w-4 mr-2 transform hover:text-blue-500 hover:scale-110"
                 >
                   <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                   </svg>
                 </router-link>
                 <button 
                    @click="openEditJobModal(job)" 
                    title="Edit Job" 
                    class="w-4 mr-2 transform hover:text-purple-500 hover:scale-110"
                    :disabled="job.is_system_job"
                    :class="job.is_system_job ? 'opacity-40 cursor-not-allowed' : ''"
                 >
                    <PencilIcon class="h-4 w-4" />
                 </button>
                 <button 
                    @click="openDeleteJobModal(job)" 
                    title="Delete Job" 
                    class="w-4 mr-2 transform hover:text-red-500 hover:scale-110"
                    :disabled="job.is_system_job"
                    :class="job.is_system_job ? 'opacity-40 cursor-not-allowed' : ''"
                 >
                    <TrashIcon class="h-4 w-4" />
                 </button>
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

const jobStore = useJobStore()
const router = useRouter()
const jobs = computed(() => jobStore.jobs)

// Modal States
const isFormModalOpen = ref(false)
const selectedJob = ref(null) // null for create, job object for edit
const isDeleteModalOpen = ref(false)
const jobToDelete = ref(null)

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

</script>

<style scoped>
/* Add any page-specific styles */
</style>
