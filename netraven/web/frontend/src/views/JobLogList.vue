<template>
  <MainLayout>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Job Logs</h1>
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
            v-model="filters.status" 
            class="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md p-2"
          >
            <option value="">All Statuses</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Date Range</label>
          <div class="flex space-x-2">
            <input 
              type="date" 
              v-model="filters.start_date" 
              class="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md p-2"
            />
            <input 
              type="date" 
              v-model="filters.end_date" 
              class="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md p-2"
            />
          </div>
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
    <div v-if="jobLogStore.loading" class="flex justify-center my-8">
      <div class="spinner"></div>
    </div>
    
    <!-- Error State -->
    <div v-else-if="jobLogStore.error" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6">
      <p>{{ jobLogStore.error }}</p>
      <button @click="fetchJobLogs" class="underline mt-2">Try Again</button>
    </div>
    
    <!-- Empty State -->
    <div v-else-if="jobLogStore.jobLogs.length === 0" class="bg-white rounded-lg shadow p-8 text-center">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <h3 class="mt-2 text-lg font-medium text-gray-900">No job logs found</h3>
      <p class="mt-1 text-gray-500">No job logs match your current filters.</p>
    </div>
    
    <!-- Job Logs Table -->
    <div v-else class="bg-white rounded-lg shadow overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Job Type
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Start Time
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              End Time
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Device
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Result
            </th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="jobLog in jobLogStore.jobLogs" :key="jobLog.id" class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap">
              <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                :class="{
                  'bg-blue-100 text-blue-800': jobLog.job_type === 'device_backup',
                  'bg-green-100 text-green-800': jobLog.job_type === 'config_compliance',
                  'bg-purple-100 text-purple-800': jobLog.job_type === 'device_discovery',
                  'bg-yellow-100 text-yellow-800': jobLog.job_type === 'system_maintenance',
                  'bg-gray-100 text-gray-800': !['device_backup', 'config_compliance', 'device_discovery', 'system_maintenance'].includes(jobLog.job_type)
                }">
                {{ formatJobType(jobLog.job_type) }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                :class="{
                  'bg-yellow-100 text-yellow-800': jobLog.status === 'running',
                  'bg-green-100 text-green-800': jobLog.status === 'completed',
                  'bg-red-100 text-red-800': jobLog.status === 'failed',
                  'bg-gray-100 text-gray-800': !['running', 'completed', 'failed'].includes(jobLog.status)
                }">
                {{ jobLog.status }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ formatDateTime(jobLog.start_time) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ jobLog.end_time ? formatDateTime(jobLog.end_time) : '-' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ jobLog.device_id ? jobLog.device_id : '-' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              <span :title="jobLog.result_message">
                {{ truncateText(jobLog.result_message, 30) || '-' }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
              <router-link :to="`/job-logs/${jobLog.id}`" class="text-blue-600 hover:text-blue-900 mr-3">
                View
              </router-link>
              <button @click="confirmDeleteJobLog(jobLog)" class="text-red-600 hover:text-red-900">
                Delete
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 max-w-md w-full">
        <h3 class="text-lg font-medium text-gray-900 mb-4">Confirm Delete</h3>
        <p class="text-gray-500 mb-6">
          Are you sure you want to delete this job log? This action cannot be undone.
        </p>
        <div class="flex justify-end space-x-3">
          <button 
            @click="showDeleteModal = false" 
            class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded"
          >
            Cancel
          </button>
          <button 
            @click="deleteJobLog" 
            class="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
          >
            Delete
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
import { useJobLogStore } from '../store/job-logs'

export default {
  name: 'JobLogList',
  components: {
    MainLayout
  },
  
  setup() {
    const jobLogStore = useJobLogStore()
    const router = useRouter()
    
    const filters = ref({
      job_type: '',
      status: '',
      start_date: '',
      end_date: ''
    })
    
    const showDeleteModal = ref(false)
    const jobLogToDelete = ref(null)
    
    // Fetch job logs on component mount
    onMounted(async () => {
      await fetchJobLogs()
    })
    
    const fetchJobLogs = async () => {
      await jobLogStore.fetchJobLogs()
    }
    
    const applyFilters = async () => {
      // Convert filters to the format expected by the API
      const apiFilters = {}
      
      if (filters.value.job_type) {
        apiFilters.job_type = filters.value.job_type
      }
      
      if (filters.value.status) {
        apiFilters.status = filters.value.status
      }
      
      if (filters.value.start_date) {
        apiFilters.start_date = filters.value.start_date
      }
      
      if (filters.value.end_date) {
        apiFilters.end_date = filters.value.end_date
      }
      
      // Update store filters and fetch job logs
      jobLogStore.setFilters(apiFilters)
      await jobLogStore.fetchJobLogs()
    }
    
    const clearFilters = () => {
      filters.value = {
        job_type: '',
        status: '',
        start_date: '',
        end_date: ''
      }
      
      jobLogStore.clearFilters()
      fetchJobLogs()
    }
    
    const confirmDeleteJobLog = (jobLog) => {
      jobLogToDelete.value = jobLog
      showDeleteModal.value = true
    }
    
    const deleteJobLog = async () => {
      if (jobLogToDelete.value) {
        await jobLogStore.deleteJobLog(jobLogToDelete.value.id)
        showDeleteModal.value = false
        jobLogToDelete.value = null
      }
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
    
    const truncateText = (text, maxLength) => {
      if (!text) return ''
      if (text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    }
    
    return {
      jobLogStore,
      filters,
      showDeleteModal,
      fetchJobLogs,
      applyFilters,
      clearFilters,
      confirmDeleteJobLog,
      deleteJobLog,
      formatJobType,
      formatDateTime,
      truncateText
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