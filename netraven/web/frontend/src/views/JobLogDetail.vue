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
                  :class="statusClass"
                >
                  {{ jobLogStore.currentJobLog.status }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Session ID:</span>
                <span class="font-mono text-sm">{{ jobLogStore.currentJobLog.session_id }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Device:</span>
                <span v-if="jobLogStore.currentJobLog.device_id">
                  <router-link 
                    :to="`/devices/${jobLogStore.currentJobLog.device_id}`" 
                    class="text-blue-600 hover:underline"
                  >
                    {{ jobLogStore.currentJobLog.device_id }}
                  </router-link>
                </span>
                <span v-else>N/A</span>
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
                <span>{{ formattedDuration }}</span>
              </div>
                <div class="flex justify-between">
                <span class="text-gray-600">Result:</span>
                  <span 
                    :class="{
                      'text-red-600 font-semibold': jobLogStore.currentJobLog.status === 'failed',
                      'text-green-600 font-semibold': jobLogStore.currentJobLog.status === 'completed'
                    }"
                  >
                  {{ jobLogStore.currentJobLog.result_message || jobLogStore.currentJobLog.status }}
                      </span>
              </div>
            </div>
          </div>
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
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Level
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Message
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="(entry, index) in jobLogStore.currentJobLogEntries" :key="entry.id" class="hover:bg-gray-50">
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
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <button 
                    v-if="hasSessionLog(entry)"
                    @click="toggleDetails(index)" 
                    class="text-blue-600 hover:text-blue-800"
                  >
                    {{ expandedEntries[index] ? 'Hide' : 'View' }} Details
                  </button>
                </td>
              </tr>
              <!-- Details row that appears when expanded -->
              <tr v-for="(entry, index) in jobLogStore.currentJobLogEntries" :key="`${entry.id}-details`" v-show="expandedEntries[index]">
                <td colspan="5" class="px-6 py-4 bg-gray-50">
                  <!-- Session Log Content -->
                  <div v-if="entry.session_log_content">
                    <h3 class="font-semibold text-gray-700 mb-2">Session Log</h3>
                    <pre class="bg-black text-green-400 p-4 rounded text-sm overflow-x-auto whitespace-pre-wrap">{{ entry.session_log_content }}</pre>
                  </div>
                  
                  <!-- Fallback Session Log from Details -->
                  <div v-else-if="entry.details && entry.details.fallback_log">
                    <h3 class="font-semibold text-gray-700 mb-2">Session Log</h3>
                    <pre class="bg-black text-green-400 p-4 rounded text-sm overflow-x-auto whitespace-pre-wrap">{{ entry.details.fallback_log }}</pre>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    
    <!-- Not Found State -->
    <div v-else class="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow">
      <div class="text-center py-8">
        <h2 class="text-xl font-semibold text-gray-800 mb-2">Job Log Not Found</h2>
        <p class="text-gray-500">The requested job log could not be found or you don't have permission to access it.</p>
        <button @click="router.push('/job-logs')" class="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          Back to Job Logs
        </button>
      </div>
    </div>
    
    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="fixed inset-0 flex items-center justify-center z-50">
      <div class="absolute inset-0 bg-black opacity-50"></div>
      <div class="relative z-10 bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
        <h3 class="text-lg font-medium text-gray-900 mb-4">Confirm Deletion</h3>
        <p class="text-gray-600 mb-6">Are you sure you want to delete this job log? This action cannot be undone.</p>
        <div class="flex justify-end space-x-3">
          <button 
            @click="showDeleteModal = false" 
            class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button 
            @click="deleteJobLog" 
            class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useJobLogStore } from '../store/job-logs'
import MainLayout from '../components/MainLayout.vue'

export default {
  name: 'JobLogDetail',
  components: {
    MainLayout
  },
  
  setup() {
    const jobLogStore = useJobLogStore()
    const route = useRoute()
    const router = useRouter()
    
    // Basic state
    const jobLogId = computed(() => route.params.id?.toString())
    const showDeleteModal = ref(false)
    const loadingEntries = ref(false)
    const expandedEntries = ref({})
    
    // Computed values
    const statusClass = computed(() => {
      if (!jobLogStore.currentJobLog) return ''
      
      switch (jobLogStore.currentJobLog.status) {
        case 'completed': return 'bg-green-100 text-green-800'
        case 'failed': return 'bg-red-100 text-red-800'
        case 'running': return 'bg-blue-100 text-blue-800'
        default: return 'bg-gray-100 text-gray-800'
      }
    })
    
    const formattedDuration = computed(() => {
      if (!jobLogStore.currentJobLog || !jobLogStore.currentJobLog.start_time) return '0s'
      
      const start = new Date(jobLogStore.currentJobLog.start_time).getTime()
      const end = jobLogStore.currentJobLog.end_time 
        ? new Date(jobLogStore.currentJobLog.end_time).getTime()
        : Date.now()
      
      const ms = end - start
      
      if (ms < 1000) return `${ms}ms`
      const sec = Math.floor(ms / 1000)
      if (sec < 60) return `${sec}s`
      
      const min = Math.floor(sec / 60)
      const secRem = sec % 60
      return `${min}m ${secRem}s`
    })
    
    // Helper methods
    const hasSessionLog = (entry) => {
      return Boolean(entry.session_log_content) || 
        (entry.details && entry.details.fallback_log)
    }
    
    const toggleDetails = (index) => {
      expandedEntries.value[index] = !expandedEntries.value[index]
    }
    
    const formatJobType = (jobType) => {
      if (!jobType) return 'Unknown'
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
    
    // Data fetching
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
    
    // Delete operation
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
    
    // Initialize component
    onMounted(() => {
      fetchJobLog()
      fetchJobLogEntries()
    })
    
    return {
      jobLogStore,
      jobLogId,
      statusClass,
      formattedDuration,
      showDeleteModal,
      loadingEntries,
      expandedEntries,
      hasSessionLog,
      toggleDetails,
      fetchJobLog,
      fetchJobLogEntries,
      confirmDeleteJobLog,
      deleteJobLog,
      formatJobType,
      formatDateTime,
      router
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