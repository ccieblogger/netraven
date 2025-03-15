<template>
  <MainLayout>
    <!-- Loading State -->
    <div v-if="jobLogStore.loading" class="flex justify-center my-8">
      <div class="spinner"></div>
    </div>
    
    <!-- Error State -->
    <div v-else-if="jobLogStore.error" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6">
      <p>{{ jobLogStore.error }}</p>
      <button @click="fetchJobLog" class="underline mt-2">Try Again</button>
    </div>
    
    <!-- Job Log Details -->
    <div v-else-if="jobLogStore.currentJobLog" class="space-y-6">
      <!-- Header with back button -->
      <div class="flex justify-between items-center">
        <div class="flex items-center space-x-4">
          <router-link to="/job-logs" class="text-blue-600 hover:text-blue-800">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd" />
            </svg>
          </router-link>
          <h1 class="text-2xl font-bold">Job Log Details</h1>
        </div>
        <button 
          @click="confirmDeleteJobLog" 
          class="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
        >
          Delete Log
        </button>
      </div>
      
      <!-- Job Log Summary Card -->
      <div class="bg-white rounded-lg shadow p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h2 class="text-lg font-semibold mb-4">Job Information</h2>
            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-gray-600">Job Type:</span>
                <span class="font-medium">{{ formatJobType(jobLogStore.currentJobLog.job_type) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Status:</span>
                <span 
                  class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                  :class="{
                    'bg-yellow-100 text-yellow-800': jobLogStore.currentJobLog.status === 'running',
                    'bg-green-100 text-green-800': jobLogStore.currentJobLog.status === 'completed',
                    'bg-red-100 text-red-800': jobLogStore.currentJobLog.status === 'failed',
                    'bg-gray-100 text-gray-800': !['running', 'completed', 'failed'].includes(jobLogStore.currentJobLog.status)
                  }"
                >
                  {{ jobLogStore.currentJobLog.status }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Session ID:</span>
                <span class="font-mono text-sm">{{ jobLogStore.currentJobLog.session_id }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Device ID:</span>
                <span>{{ jobLogStore.currentJobLog.device_id || 'N/A' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Created By:</span>
                <span>{{ jobLogStore.currentJobLog.created_by || 'System' }}</span>
              </div>
            </div>
          </div>
          
          <div>
            <h2 class="text-lg font-semibold mb-4">Execution Details</h2>
            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-gray-600">Start Time:</span>
                <span>{{ formatDateTime(jobLogStore.currentJobLog.start_time) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">End Time:</span>
                <span>{{ jobLogStore.currentJobLog.end_time ? formatDateTime(jobLogStore.currentJobLog.end_time) : 'In Progress' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Duration:</span>
                <span>{{ calculateDuration(jobLogStore.currentJobLog.start_time, jobLogStore.currentJobLog.end_time) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Result:</span>
                <span>{{ jobLogStore.currentJobLog.result_message || 'N/A' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Retention Days:</span>
                <span>{{ jobLogStore.currentJobLog.retention_days }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Job Data (if available) -->
        <div v-if="jobLogStore.currentJobLog.job_data" class="mt-6 pt-6 border-t border-gray-200">
          <h2 class="text-lg font-semibold mb-4">Job Data</h2>
          <pre class="bg-gray-100 p-4 rounded overflow-auto text-sm">{{ JSON.stringify(jobLogStore.currentJobLog.job_data, null, 2) }}</pre>
        </div>
      </div>
      
      <!-- Log Entries -->
      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-lg font-semibold">Log Entries</h2>
          <button 
            @click="fetchJobLogEntries" 
            class="text-blue-600 hover:text-blue-800 flex items-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
            </svg>
            Refresh
          </button>
        </div>
        
        <!-- Loading Entries -->
        <div v-if="loadingEntries" class="flex justify-center my-8">
          <div class="spinner"></div>
        </div>
        
        <!-- Empty Entries -->
        <div v-else-if="jobLogStore.currentJobLogEntries.length === 0" class="text-center py-8">
          <p class="text-gray-500">No log entries found for this job.</p>
        </div>
        
        <!-- Entries Table -->
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Level
                </th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Message
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="entry in jobLogStore.currentJobLogEntries" :key="entry.id" class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDateTime(entry.timestamp) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                    :class="{
                      'bg-red-100 text-red-800': entry.level === 'ERROR',
                      'bg-yellow-100 text-yellow-800': entry.level === 'WARNING',
                      'bg-blue-100 text-blue-800': entry.level === 'INFO',
                      'bg-gray-100 text-gray-800': entry.level === 'DEBUG'
                    }">
                    {{ entry.level }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ entry.category || 'N/A' }}
                </td>
                <td class="px-6 py-4 text-sm text-gray-500">
                  <div class="max-w-lg break-words">{{ entry.message }}</div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    
    <!-- Not Found State -->
    <div v-else class="bg-white rounded-lg shadow p-8 text-center">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <h3 class="mt-2 text-lg font-medium text-gray-900">Job Log Not Found</h3>
      <p class="mt-1 text-gray-500">The job log you're looking for doesn't exist or has been deleted.</p>
      <div class="mt-6">
        <router-link to="/job-logs" class="text-blue-600 hover:text-blue-800">
          Back to Job Logs
        </router-link>
      </div>
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
import { useRoute, useRouter } from 'vue-router'
import MainLayout from '../components/MainLayout.vue'
import { useJobLogStore } from '../store/job-logs'

export default {
  name: 'JobLogDetail',
  components: {
    MainLayout
  },
  
  setup() {
    const jobLogStore = useJobLogStore()
    const route = useRoute()
    const router = useRouter()
    
    const jobLogId = computed(() => route.params.id)
    const showDeleteModal = ref(false)
    const loadingEntries = ref(false)
    
    // Fetch job log and entries on component mount
    onMounted(async () => {
      await fetchJobLog()
      await fetchJobLogEntries()
    })
    
    const fetchJobLog = async () => {
      if (jobLogId.value) {
        await jobLogStore.fetchJobLog(jobLogId.value)
      }
    }
    
    const fetchJobLogEntries = async () => {
      if (jobLogId.value) {
        loadingEntries.value = true
        try {
          await jobLogStore.fetchJobLogEntries(jobLogId.value)
        } finally {
          loadingEntries.value = false
        }
      }
    }
    
    const confirmDeleteJobLog = () => {
      showDeleteModal.value = true
    }
    
    const deleteJobLog = async () => {
      if (jobLogId.value) {
        const success = await jobLogStore.deleteJobLog(jobLogId.value)
        if (success) {
          router.push('/job-logs')
        }
        showDeleteModal.value = false
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
    
    const calculateDuration = (startTime, endTime) => {
      if (!startTime) return 'Unknown'
      if (!endTime) return 'In Progress'
      
      const start = new Date(startTime)
      const end = new Date(endTime)
      const durationMs = end - start
      
      // Format duration
      if (durationMs < 1000) {
        return `${durationMs}ms`
      } else if (durationMs < 60000) {
        return `${Math.floor(durationMs / 1000)}s`
      } else if (durationMs < 3600000) {
        const minutes = Math.floor(durationMs / 60000)
        const seconds = Math.floor((durationMs % 60000) / 1000)
        return `${minutes}m ${seconds}s`
      } else {
        const hours = Math.floor(durationMs / 3600000)
        const minutes = Math.floor((durationMs % 3600000) / 60000)
        return `${hours}h ${minutes}m`
      }
    }
    
    return {
      jobLogStore,
      jobLogId,
      showDeleteModal,
      loadingEntries,
      fetchJobLog,
      fetchJobLogEntries,
      confirmDeleteJobLog,
      deleteJobLog,
      formatJobType,
      formatDateTime,
      calculateDuration
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