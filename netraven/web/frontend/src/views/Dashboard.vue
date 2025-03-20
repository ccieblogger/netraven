<template>
  <MainLayout>
    <!-- Error fallback -->
    <div v-if="renderError" class="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800">Dashboard Error</h3>
          <div class="mt-2 text-sm text-red-700">
            <p>{{ renderError }}</p>
            <button 
              @click="retryRender" 
              class="mt-2 bg-red-200 hover:bg-red-300 text-red-800 px-3 py-1 rounded"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="text-center py-8">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
      <p class="mt-4 text-gray-600">Loading dashboard...</p>
    </div>
    
    <div v-else-if="!renderError" class="dashboard-content">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <!-- Status Card -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-xl font-semibold mb-4">System Status</h2>
          <div class="flex items-center space-x-2 mb-2">
            <div class="w-3 h-3 rounded-full bg-green-500"></div>
            <span>API: Online</span>
          </div>
          <div class="flex items-center space-x-2 mb-2">
            <div class="w-3 h-3 rounded-full bg-green-500"></div>
            <span>Database: Connected</span>
          </div>
          <div class="flex items-center space-x-2 mb-2">
            <div class="w-3 h-3 rounded-full bg-green-500"></div>
            <span>Scheduler: Running</span>
          </div>
          <div class="flex items-center space-x-2">
            <div 
              class="w-3 h-3 rounded-full" 
              :class="gatewayStatus === 'running' ? 'bg-green-500' : 'bg-red-500'"
            ></div>
            <span>Gateway: {{ gatewayStatus === 'running' ? 'Online' : 'Offline' }}</span>
          </div>
          <div v-if="gatewayStatus === 'running'" class="mt-2 text-xs text-gray-500">
            <router-link to="/gateway" class="text-blue-500 hover:underline">View Gateway Dashboard</router-link>
          </div>
        </div>
        
        <!-- Devices Summary -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-xl font-semibold mb-4">Devices</h2>
          <div class="flex justify-between mb-2">
            <span>Total Devices:</span>
            <span class="font-semibold">{{ deviceCount }}</span>
          </div>
          <div class="flex justify-between">
            <span>Online:</span>
            <span class="font-semibold text-green-600">{{ onlineDeviceCount }}</span>
          </div>
          <div class="mt-4">
            <router-link 
              to="/devices" 
              class="text-blue-600 hover:text-blue-800 font-medium"
            >
              View All Devices →
            </router-link>
          </div>
        </div>
        
        <!-- Backups Summary -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-xl font-semibold mb-4">Backups</h2>
          <div class="flex justify-between mb-2">
            <span>Total Backups:</span>
            <span class="font-semibold">{{ backupCount }}</span>
          </div>
          <div class="flex justify-between">
            <span>Last 24 Hours:</span>
            <span class="font-semibold">{{ recentBackupCount }}</span>
          </div>
          <div class="mt-4">
            <router-link 
              to="/backups" 
              class="text-blue-600 hover:text-blue-800 font-medium"
            >
              View All Backups →
            </router-link>
          </div>
        </div>
        
        <!-- Jobs Summary -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-xl font-semibold mb-4">Scheduled Jobs</h2>
          <div class="flex justify-between mb-2">
            <span>Total Jobs:</span>
            <span class="font-semibold">{{ scheduledJobCount }}</span>
          </div>
          <div class="flex justify-between">
            <span>Enabled:</span>
            <span class="font-semibold text-green-600">{{ enabledJobCount }}</span>
          </div>
          <div class="mt-4">
            <router-link 
              to="/scheduled-jobs" 
              class="text-blue-600 hover:text-blue-800 font-medium"
            >
              Manage Scheduled Jobs →
            </router-link>
          </div>
        </div>
      </div>
      
      <!-- Recent Activity and Job Logs -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
        <!-- Recent Activity -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-xl font-semibold mb-4">Recent Activity</h2>
          <div v-if="loading" class="text-center py-4">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          </div>
          <div v-else-if="recentBackups.length === 0" class="text-center py-4 text-gray-500">
            <p>No recent activity to display</p>
          </div>
          <div v-else class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Device</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Activity</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="backup in recentBackups" :key="backup.id">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <router-link :to="`/devices/${backup.device_id}`" class="text-blue-600 hover:text-blue-900">
                      {{ backup.device_hostname }}
                    </router-link>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    Configuration Backup
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                      :class="backup.status === 'complete' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'">
                      {{ backup.status }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ formatDate(backup.created_at) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- Recent Job Logs -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-xl font-semibold mb-4">Recent Job Logs</h2>
          <div v-if="loadingJobLogs" class="text-center py-4">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          </div>
          <div v-else-if="recentJobLogs.length === 0" class="text-center py-4 text-gray-500">
            <p>No recent job logs to display</p>
          </div>
          <div v-else class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th class="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Job Type
                  </th>
                  <th class="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th class="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Time
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="log in recentJobLogs" :key="log.id" class="hover:bg-gray-50">
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {{ formatJobType(log.job_type) }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm">
                    <span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full"
                      :class="{
                        'bg-yellow-100 text-yellow-800': log.status === 'running',
                        'bg-green-100 text-green-800': log.status === 'completed',
                        'bg-red-100 text-red-800': log.status === 'failed',
                        'bg-gray-100 text-gray-800': !['running', 'completed', 'failed'].includes(log.status)
                      }">
                      {{ log.status }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ formatDateTime(log.start_time) }}
                  </td>
                </tr>
              </tbody>
            </table>
            <div class="mt-4 text-right">
              <router-link 
                to="/job-logs" 
                class="text-blue-600 hover:text-blue-800 font-medium"
              >
                View All Job Logs →
              </router-link>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Quick Actions -->
      <div class="mt-8 bg-white rounded-lg shadow p-6">
        <h2 class="text-xl font-semibold mb-4">Quick Actions</h2>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <router-link to="/devices" class="bg-blue-50 hover:bg-blue-100 p-4 rounded border border-blue-200 text-center">
            <div class="font-medium text-blue-700">Add Device</div>
          </router-link>
          <router-link to="/devices" class="bg-green-50 hover:bg-green-100 p-4 rounded border border-green-200 text-center">
            <div class="font-medium text-green-700">Backup All Devices</div>
          </router-link>
          <router-link to="/credentials/dashboard" class="bg-orange-50 hover:bg-orange-100 p-4 rounded border border-orange-200 text-center">
            <div class="font-medium text-orange-700">Credential Performance</div>
          </router-link>
          <router-link to="/scheduled-jobs" class="bg-yellow-50 hover:bg-yellow-100 p-4 rounded border border-yellow-200 text-center">
            <div class="font-medium text-yellow-700">Manage Scheduled Jobs</div>
          </router-link>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script>
import { ref, computed, onMounted, onErrorCaptured } from 'vue'
import MainLayout from '../components/MainLayout.vue'
import { useDeviceStore } from '../store/devices'
import { useBackupStore } from '../store/backups'
import { useAuthStore } from '../store/auth'
import { useJobLogStore } from '../store/job-logs'
import { useScheduledJobStore } from '../store/scheduled-jobs'
import api from '@/api/api'

export default {
  name: 'Dashboard',
  components: {
    MainLayout
  },
  
  setup() {
    const deviceStore = useDeviceStore()
    const backupStore = useBackupStore()
    const authStore = useAuthStore()
    const jobLogStore = useJobLogStore()
    const scheduledJobStore = useScheduledJobStore()
    
    const loading = ref(true)
    const loadingJobLogs = ref(true)
    const error = ref(null)
    const renderError = ref(null)
    const appLoaded = ref(false)
    const gatewayStatus = ref(null)
    
    const isAuthenticated = computed(() => authStore.isAuthenticated)
    
    // Device stats
    const deviceCount = computed(() => {
      try {
        return deviceStore.devices?.length || 0
      } catch (e) {
        console.error('Error computing deviceCount:', e)
        return 0
      }
    })
    
    const onlineDeviceCount = computed(() => {
      try {
        // Only count devices that are both enabled and online
        return deviceStore.devices?.filter(d => d.enabled && d.status === 'online').length || 0
      } catch (e) {
        console.error('Error computing onlineDeviceCount:', e)
        return 0
      }
    })
    
    // Backup stats
    const backupCount = computed(() => {
      try {
        return backupStore.backups?.length || 0
      } catch (e) {
        console.error('Error computing backupCount:', e)
        return 0
      }
    })
    
    const recentBackupCount = computed(() => {
      try {
        const oneDayAgo = new Date()
        oneDayAgo.setDate(oneDayAgo.getDate() - 1)
        
        return backupStore.backups?.filter(backup => {
          const backupDate = new Date(backup.created_at)
          return backupDate >= oneDayAgo
        }).length || 0
      } catch (e) {
        console.error('Error computing recentBackupCount:', e)
        return 0
      }
    })
    
    // Scheduled jobs stats
    const scheduledJobCount = computed(() => {
      try {
        return scheduledJobStore.scheduledJobs?.length || 0
      } catch (e) {
        console.error('Error computing scheduledJobCount:', e)
        return 0
      }
    })
    
    const enabledJobCount = computed(() => {
      try {
        return scheduledJobStore.scheduledJobs?.filter(job => job.enabled).length || 0
      } catch (e) {
        console.error('Error computing enabledJobCount:', e)
        return 0
      }
    })
    
    // Recent backups
    const recentBackups = computed(() => {
      try {
        // Map backups to include device information
        return (backupStore.backups || [])
          .map(backup => {
            const device = deviceStore.devices?.find(d => d.id === backup.device_id)
            // If device exists, use its hostname, otherwise show device ID
            return {
              ...backup,
              device_hostname: device ? device.hostname : `Device ${backup.device_id.slice(0, 8)}...`
            }
          })
          .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
          .slice(0, 5) // Show only the 5 most recent backups
      } catch (e) {
        console.error('Error computing recentBackups:', e)
        return []
      }
    })
    
    // Recent job logs
    const recentJobLogs = computed(() => {
      try {
        return (jobLogStore.jobLogs || [])
          .sort((a, b) => new Date(b.start_time) - new Date(a.start_time))
          .slice(0, 5) // Show only the 5 most recent job logs
      } catch (e) {
        console.error('Error computing recentJobLogs:', e)
        return []
      }
    })
    
    // Load data on component mount
    onMounted(async () => {
      try {
        loading.value = true
        
        // Load devices and backups in parallel
        await Promise.all([
          deviceStore.fetchDevices(),
          backupStore.fetchBackups()
        ])
        
        // Load job logs and scheduled jobs
        loadingJobLogs.value = true
        await Promise.all([
          jobLogStore.fetchJobLogs(),
          scheduledJobStore.fetchScheduledJobs()
        ])
        
        // Check gateway status
        const gatewayData = await api.getGatewayStatus()
        gatewayStatus.value = gatewayData.status
        
        appLoaded.value = true
      } catch (err) {
        console.error('Dashboard: Error loading data:', err)
        error.value = 'Failed to load dashboard data'
      } finally {
        loading.value = false
        loadingJobLogs.value = false
      }
    })
    
    // Error handling
    onErrorCaptured((err, instance, info) => {
      console.error('Dashboard error captured:', err, info)
      renderError.value = `${err.message || 'Unknown error'}`
      return false // prevent error from propagating further
    })
    
    const retryRender = async () => {
      renderError.value = null
      try {
        await Promise.all([
          deviceStore.fetchDevices(),
          backupStore.fetchBackups(),
          jobLogStore.fetchJobLogs(),
          scheduledJobStore.fetchScheduledJobs()
        ])
      } catch (err) {
        renderError.value = 'Still having issues loading the dashboard'
      }
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return ''
      
      const date = new Date(dateString)
      return date.toLocaleString()
    }
    
    const formatDateTime = (dateString) => {
      if (!dateString) return ''
      
      const date = new Date(dateString)
      return date.toLocaleString()
    }
    
    const formatJobType = (jobType) => {
      if (!jobType) return 'Unknown'
      
      // Convert snake_case to Title Case
      return jobType
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
    }
    
    return {
      loading,
      loadingJobLogs,
      error,
      renderError,
      deviceCount,
      onlineDeviceCount,
      backupCount,
      recentBackupCount,
      scheduledJobCount,
      enabledJobCount,
      recentBackups,
      recentJobLogs,
      isAuthenticated,
      retryRender,
      formatDate,
      formatDateTime,
      formatJobType,
      gatewayStatus
    }
  }
}
</script>

<style scoped>
.dashboard-content {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style> 