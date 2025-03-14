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
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- Status Card -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-xl font-semibold mb-4">System Status</h2>
          <div class="flex items-center space-x-2 mb-2">
            <div class="w-3 h-3 rounded-full bg-green-500"></div>
            <span>API: Online</span>
          </div>
          <div class="flex items-center space-x-2">
            <div class="w-3 h-3 rounded-full bg-green-500"></div>
            <span>Database: Connected</span>
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
      </div>
      
      <!-- Recent Activity -->
      <div class="mt-8 bg-white rounded-lg shadow p-6">
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
      
      <!-- Quick Actions -->
      <div class="mt-8 bg-white rounded-lg shadow p-6">
        <h2 class="text-xl font-semibold mb-4">Quick Actions</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <router-link to="/devices" class="bg-blue-50 hover:bg-blue-100 p-4 rounded border border-blue-200 text-center">
            <div class="font-medium text-blue-700">Add Device</div>
          </router-link>
          <router-link to="/devices" class="bg-green-50 hover:bg-green-100 p-4 rounded border border-green-200 text-center">
            <div class="font-medium text-green-700">Backup All Devices</div>
          </router-link>
          <router-link to="/backups" class="bg-purple-50 hover:bg-purple-100 p-4 rounded border border-purple-200 text-center">
            <div class="font-medium text-purple-700">Compare Backups</div>
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

export default {
  name: 'Dashboard',
  components: {
    MainLayout
  },
  
  setup() {
    const deviceStore = useDeviceStore()
    const backupStore = useBackupStore()
    const authStore = useAuthStore()
    
    const loading = ref(true)
    const error = ref(null)
    const renderError = ref(null)
    const appLoaded = ref(false)
    
    const isAuthenticated = computed(() => authStore.isAuthenticated)
    
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
          .slice(0, 5)
      } catch (e) {
        console.error('Error computing recentBackups:', e)
        return []
      }
    })
    
    // Error handling
    onErrorCaptured((err, instance, info) => {
      console.error('Dashboard Error Captured:', err)
      renderError.value = err.message || 'An error occurred while rendering the dashboard'
      return false // prevent propagation
    })
    
    const retryRender = () => {
      renderError.value = null
      // Re-fetch data to retry
      fetchDashboardData()
    }
    
    const fetchDashboardData = async () => {
      try {
        // Fetch devices and backups in parallel
        await Promise.all([
          deviceStore.fetchDevices(),
          backupStore.fetchBackups()
        ])
        
        console.log('Dashboard data loaded successfully')
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err)
        error.value = err.message || 'Failed to load dashboard data'
      }
    }
    
    onMounted(async () => {
      try {
        // Fetch data for dashboard
        await fetchDashboardData()
      } catch (err) {
        console.error('Dashboard failed to load:', err)
        error.value = err.message
      } finally {
        // Always mark as loaded, even if there were errors
        loading.value = false
        appLoaded.value = true
      }
    })
    
    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleString()
    }
    
    return {
      loading,
      error,
      renderError,
      deviceCount,
      onlineDeviceCount,
      backupCount,
      recentBackupCount,
      recentBackups,
      formatDate,
      retryRender,
      isAuthenticated,
      appLoaded
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