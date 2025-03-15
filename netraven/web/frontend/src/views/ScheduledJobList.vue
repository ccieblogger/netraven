<template>
  <MainLayout>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Scheduled Jobs</h1>
      <button @click="showAddJobModal = true" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
        Add Scheduled Job
      </button>
    </div>
    
    <!-- Filters -->
    <div class="bg-white rounded-lg shadow p-4 mb-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Job Type</label>
          <select 
            v-model="filters.job_type" 
            class="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md p-2"
          >
            <option value="">All Types</option>
            <option value="device_backup">Device Backup</option>
            <option value="config_compliance">Config Compliance</option>
            <option value="device_discovery">Device Discovery</option>
            <option value="system_maintenance">System Maintenance</option>
          </select>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Status</label>
          <select 
            v-model="filters.enabled" 
            class="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md p-2"
          >
            <option value="">All Statuses</option>
            <option value="true">Enabled</option>
            <option value="false">Disabled</option>
          </select>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Device</label>
          <select 
            v-model="filters.device_id" 
            class="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md p-2"
          >
            <option value="">All Devices</option>
            <option v-for="device in devices" :key="device.id" :value="device.id">
              {{ device.hostname }}
            </option>
          </select>
        </div>
      </div>
      
      <div class="flex justify-end mt-4">
        <button 
          @click="clearFilters" 
          class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded mr-2"
        >
          Clear Filters
        </button>
        <button 
          @click="applyFilters" 
          class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Apply Filters
        </button>
      </div>
    </div>
    
    <!-- Loading State -->
    <div v-if="scheduledJobStore.loading" class="flex justify-center my-8">
      <div class="spinner"></div>
    </div>
    
    <!-- Error State -->
    <div v-else-if="scheduledJobStore.error" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6">
      <p>{{ scheduledJobStore.error }}</p>
      <button @click="fetchScheduledJobs" class="underline mt-2">Try Again</button>
    </div>
    
    <!-- Empty State -->
    <div v-else-if="scheduledJobStore.scheduledJobs.length === 0" class="bg-white rounded-lg shadow p-8 text-center">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <h3 class="mt-2 text-lg font-medium text-gray-900">No scheduled jobs found</h3>
      <p class="mt-1 text-gray-500">No scheduled jobs match your current filters.</p>
      <div class="mt-6">
        <button 
          @click="showAddJobModal = true" 
          class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
        >
          Add Your First Scheduled Job
        </button>
      </div>
    </div>
    
    <!-- Scheduled Jobs Table -->
    <div v-else class="bg-white rounded-lg shadow overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Name
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Job Type
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Schedule
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Device
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Last Run
            </th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="job in scheduledJobStore.scheduledJobs" :key="job.id" class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm font-medium text-gray-900">{{ job.name }}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                :class="{
                  'bg-blue-100 text-blue-800': job.job_type === 'device_backup',
                  'bg-green-100 text-green-800': job.job_type === 'config_compliance',
                  'bg-purple-100 text-purple-800': job.job_type === 'device_discovery',
                  'bg-yellow-100 text-yellow-800': job.job_type === 'system_maintenance',
                  'bg-gray-100 text-gray-800': !['device_backup', 'config_compliance', 'device_discovery', 'system_maintenance'].includes(job.job_type)
                }">
                {{ formatJobType(job.job_type) }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ formatSchedule(job.schedule_interval) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                :class="{
                  'bg-green-100 text-green-800': job.enabled,
                  'bg-gray-100 text-gray-800': !job.enabled
                }">
                {{ job.enabled ? 'Enabled' : 'Disabled' }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ job.device_id ? getDeviceName(job.device_id) : 'N/A' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ job.last_run ? formatDateTime(job.last_run) : 'Never' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
              <button 
                @click="runJob(job)" 
                class="text-blue-600 hover:text-blue-900 mr-3"
                :disabled="isRunningJob(job.id)"
              >
                {{ isRunningJob(job.id) ? 'Running...' : 'Run Now' }}
              </button>
              <button 
                @click="toggleJob(job)" 
                class="text-indigo-600 hover:text-indigo-900 mr-3"
                :disabled="isTogglingJob(job.id)"
              >
                {{ isTogglingJob(job.id) ? 'Updating...' : (job.enabled ? 'Disable' : 'Enable') }}
              </button>
              <button @click="editJob(job)" class="text-green-600 hover:text-green-900 mr-3">
                Edit
              </button>
              <button @click="confirmDeleteJob(job)" class="text-red-600 hover:text-red-900">
                Delete
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- Add/Edit Job Modal -->
    <div v-if="showAddJobModal || showEditJobModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 max-w-2xl w-full">
        <h3 class="text-lg font-medium text-gray-900 mb-4">
          {{ showEditJobModal ? 'Edit Scheduled Job' : 'Add Scheduled Job' }}
        </h3>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input 
              type="text" 
              v-model="jobForm.name" 
              class="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md p-2"
              placeholder="Enter job name"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Job Type</label>
            <select 
              v-model="jobForm.job_type" 
              class="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md p-2"
            >
              <option value="device_backup">Device Backup</option>
              <option value="config_compliance">Config Compliance</option>
              <option value="device_discovery">Device Discovery</option>
              <option value="system_maintenance">System Maintenance</option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Schedule Interval (minutes)</label>
            <input 
              type="number" 
              v-model="jobForm.schedule_interval" 
              min="1"
              class="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md p-2"
              placeholder="Enter interval in minutes"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Device</label>
            <select 
              v-model="jobForm.device_id" 
              class="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md p-2"
            >
              <option value="">None (System-wide job)</option>
              <option v-for="device in devices" :key="device.id" :value="device.id">
                {{ device.hostname }}
              </option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Job Parameters (JSON)</label>
            <textarea 
              v-model="jobForm.job_params_json" 
              rows="4"
              class="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md p-2"
              placeholder='{"param1": "value1", "param2": "value2"}'
            ></textarea>
          </div>
          
          <div class="flex items-center">
            <input 
              type="checkbox" 
              id="job-enabled" 
              v-model="jobForm.enabled"
              class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label for="job-enabled" class="ml-2 block text-sm text-gray-900">
              Enabled
            </label>
          </div>
        </div>
        
        <div class="flex justify-end space-x-3 mt-6">
          <button 
            @click="closeJobModal" 
            class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded"
          >
            Cancel
          </button>
          <button 
            @click="saveJob" 
            class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            :disabled="isSavingJob"
          >
            {{ isSavingJob ? 'Saving...' : 'Save' }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 max-w-md w-full">
        <h3 class="text-lg font-medium text-gray-900 mb-4">Confirm Delete</h3>
        <p class="text-gray-500 mb-6">
          Are you sure you want to delete this scheduled job? This action cannot be undone.
        </p>
        <div class="flex justify-end space-x-3">
          <button 
            @click="showDeleteModal = false" 
            class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded"
          >
            Cancel
          </button>
          <button 
            @click="deleteJob" 
            class="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
            :disabled="isDeletingJob"
          >
            {{ isDeletingJob ? 'Deleting...' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import MainLayout from '../components/MainLayout.vue'
import { useScheduledJobStore } from '../store/scheduled-jobs'
import { useDeviceStore } from '../store/devices'

export default {
  name: 'ScheduledJobList',
  components: {
    MainLayout
  },
  
  setup() {
    const scheduledJobStore = useScheduledJobStore()
    const deviceStore = useDeviceStore()
    const router = useRouter()
    
    const filters = ref({
      job_type: '',
      enabled: '',
      device_id: ''
    })
    
    const showAddJobModal = ref(false)
    const showEditJobModal = ref(false)
    const showDeleteModal = ref(false)
    const jobToDelete = ref(null)
    const isSavingJob = ref(false)
    const isDeletingJob = ref(false)
    const runningJobs = ref([])
    const togglingJobs = ref([])
    
    const jobForm = ref({
      id: null,
      name: '',
      job_type: 'device_backup',
      schedule_interval: 60,
      device_id: '',
      job_params_json: '{}',
      enabled: true
    })
    
    const devices = computed(() => deviceStore.devices)
    
    // Fetch scheduled jobs and devices on component mount
    onMounted(async () => {
      await Promise.all([
        fetchScheduledJobs(),
        deviceStore.fetchDevices()
      ])
    })
    
    const fetchScheduledJobs = async () => {
      await scheduledJobStore.fetchScheduledJobs()
    }
    
    const applyFilters = async () => {
      // Convert filters to the format expected by the API
      const apiFilters = {}
      
      if (filters.value.job_type) {
        apiFilters.job_type = filters.value.job_type
      }
      
      if (filters.value.enabled !== '') {
        apiFilters.enabled = filters.value.enabled === 'true'
      }
      
      if (filters.value.device_id) {
        apiFilters.device_id = filters.value.device_id
      }
      
      // Update store filters and fetch scheduled jobs
      scheduledJobStore.setFilters(apiFilters)
      await scheduledJobStore.fetchScheduledJobs()
    }
    
    const clearFilters = () => {
      filters.value = {
        job_type: '',
        enabled: '',
        device_id: ''
      }
      
      scheduledJobStore.clearFilters()
      fetchScheduledJobs()
    }
    
    const editJob = (job) => {
      jobForm.value = {
        id: job.id,
        name: job.name,
        job_type: job.job_type,
        schedule_interval: job.schedule_interval,
        device_id: job.device_id || '',
        job_params_json: job.job_params ? JSON.stringify(job.job_params, null, 2) : '{}',
        enabled: job.enabled
      }
      
      showEditJobModal.value = true
    }
    
    const confirmDeleteJob = (job) => {
      jobToDelete.value = job
      showDeleteModal.value = true
    }
    
    const deleteJob = async () => {
      if (jobToDelete.value) {
        isDeletingJob.value = true
        try {
          await scheduledJobStore.deleteScheduledJob(jobToDelete.value.id)
          showDeleteModal.value = false
          jobToDelete.value = null
        } finally {
          isDeletingJob.value = false
        }
      }
    }
    
    const closeJobModal = () => {
      showAddJobModal.value = false
      showEditJobModal.value = false
      resetJobForm()
    }
    
    const resetJobForm = () => {
      jobForm.value = {
        id: null,
        name: '',
        job_type: 'device_backup',
        schedule_interval: 60,
        device_id: '',
        job_params_json: '{}',
        enabled: true
      }
    }
    
    const saveJob = async () => {
      isSavingJob.value = true
      
      try {
        // Parse job parameters from JSON string
        let jobParams = {}
        try {
          jobParams = JSON.parse(jobForm.value.job_params_json)
        } catch (error) {
          alert('Invalid JSON in job parameters')
          return
        }
        
        const jobData = {
          name: jobForm.value.name,
          job_type: jobForm.value.job_type,
          schedule_interval: parseInt(jobForm.value.schedule_interval),
          device_id: jobForm.value.device_id || null,
          job_params: jobParams,
          enabled: jobForm.value.enabled
        }
        
        if (showEditJobModal.value) {
          // Update existing job
          await scheduledJobStore.updateScheduledJob(jobForm.value.id, jobData)
        } else {
          // Create new job
          await scheduledJobStore.createScheduledJob(jobData)
        }
        
        closeJobModal()
      } catch (error) {
        console.error('Error saving job:', error)
      } finally {
        isSavingJob.value = false
      }
    }
    
    const runJob = async (job) => {
      runningJobs.value.push(job.id)
      
      try {
        await scheduledJobStore.runScheduledJob(job.id)
      } finally {
        runningJobs.value = runningJobs.value.filter(id => id !== job.id)
      }
    }
    
    const toggleJob = async (job) => {
      togglingJobs.value.push(job.id)
      
      try {
        await scheduledJobStore.toggleScheduledJob(job.id, !job.enabled)
      } finally {
        togglingJobs.value = togglingJobs.value.filter(id => id !== job.id)
      }
    }
    
    const isRunningJob = (jobId) => {
      return runningJobs.value.includes(jobId)
    }
    
    const isTogglingJob = (jobId) => {
      return togglingJobs.value.includes(jobId)
    }
    
    const formatJobType = (jobType) => {
      if (!jobType) return 'Unknown'
      
      // Convert snake_case to Title Case
      return jobType
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
    }
    
    const formatDateTime = (dateTimeStr) => {
      if (!dateTimeStr) return '-'
      
      const date = new Date(dateTimeStr)
      return date.toLocaleString()
    }
    
    const formatSchedule = (minutes) => {
      if (!minutes) return 'Unknown'
      
      if (minutes < 60) {
        return `Every ${minutes} minute${minutes === 1 ? '' : 's'}`
      } else if (minutes === 60) {
        return 'Hourly'
      } else if (minutes % 60 === 0) {
        const hours = minutes / 60
        return `Every ${hours} hour${hours === 1 ? '' : 's'}`
      } else {
        const hours = Math.floor(minutes / 60)
        const mins = minutes % 60
        return `Every ${hours}h ${mins}m`
      }
    }
    
    const getDeviceName = (deviceId) => {
      const device = deviceStore.getDeviceById(deviceId)
      return device ? device.hostname : deviceId
    }
    
    return {
      scheduledJobStore,
      deviceStore,
      devices,
      filters,
      showAddJobModal,
      showEditJobModal,
      showDeleteModal,
      jobForm,
      isSavingJob,
      isDeletingJob,
      fetchScheduledJobs,
      applyFilters,
      clearFilters,
      editJob,
      confirmDeleteJob,
      deleteJob,
      closeJobModal,
      saveJob,
      runJob,
      toggleJob,
      isRunningJob,
      isTogglingJob,
      formatJobType,
      formatDateTime,
      formatSchedule,
      getDeviceName
    }
  }
}
</script>

<style scoped>
.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border-left-color: #3b82f6;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style> 