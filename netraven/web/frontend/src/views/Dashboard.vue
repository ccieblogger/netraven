<template>
  <MainLayout>
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
    
    <!-- Debug Tools (hidden by default) -->
    <div v-if="showDebugInfo" class="mt-8 bg-yellow-50 rounded-lg shadow p-6 border border-yellow-200">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-medium text-yellow-800">Development Tools</h2>
        <button @click="toggleDebugInfo" class="text-sm bg-yellow-200 text-yellow-800 px-3 py-1 rounded hover:bg-yellow-300">
          Hide Debug Tools
        </button>
      </div>
      
      <pre class="text-xs bg-white p-4 rounded border border-yellow-200 overflow-auto max-h-80">{{ debugInfo }}</pre>
      
      <div class="flex gap-2 mt-4">
        <button @click="testClick" class="bg-blue-600 text-white px-4 py-2 rounded">
          Test Button
        </button>
        <button @click="goToDebugPage" class="bg-gray-600 text-white px-4 py-2 rounded">
          Debug Page
        </button>
        <button @click="testLocalStorage" class="bg-green-600 text-white px-4 py-2 rounded">
          Test Storage
        </button>
      </div>
    </div>
    
    <div v-else class="mt-8 text-center">
      <button @click="toggleDebugInfo" class="text-sm bg-gray-200 text-gray-700 px-3 py-1 rounded hover:bg-gray-300">
        Show Debug Tools
      </button>
    </div>
  </MainLayout>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import MainLayout from '../components/MainLayout.vue'
import { useDeviceStore } from '../store/devices'
import { useBackupStore } from '../store/backups'

export default {
  name: 'Dashboard',
  components: {
    MainLayout
  },
  
  setup() {
    const deviceStore = useDeviceStore()
    const backupStore = useBackupStore()
    
    const loading = ref(true)
    const error = ref(null)
    
    // Debug state
    const testResult = ref(null)
    const storageTest = ref(null)
    const showDebugInfo = ref(false)
    
    const deviceCount = computed(() => deviceStore.devices.length)
    const onlineDeviceCount = computed(() => {
      // Only count devices that are both enabled and online
      return deviceStore.devices.filter(d => d.enabled && d.status === 'online').length
    })
    
    const backupCount = computed(() => backupStore.backups.length)
    const recentBackupCount = computed(() => {
      const oneDayAgo = new Date()
      oneDayAgo.setDate(oneDayAgo.getDate() - 1)
      
      return backupStore.backups.filter(backup => {
        const backupDate = new Date(backup.created_at)
        return backupDate >= oneDayAgo
      }).length
    })
    
    const recentBackups = computed(() => {
      // Map backups to include device information
      return backupStore.backups
        .map(backup => {
          const device = deviceStore.devices.find(d => d.id === backup.device_id)
          // If device exists, use its hostname, otherwise show device ID
          return {
            ...backup,
            device_hostname: device ? device.hostname : `Device ${backup.device_id.slice(0, 8)}...`
          }
        })
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .slice(0, 5)
    })
    
    onMounted(async () => {
      loading.value = true
      error.value = null
      
      try {
        // Fetch devices and backups in parallel for better performance
        await Promise.all([
          deviceStore.fetchDevices(),
          backupStore.fetchBackups()
        ])
      } catch (err) {
        console.error('Failed to load dashboard data:', err)
        error.value = 'Failed to load dashboard data. Please try refreshing the page.'
      } finally {
        loading.value = false
      }
      
      // Check URL parameters for debug mode
      const urlParams = new URLSearchParams(window.location.search)
      if (urlParams.get('debug') === 'true') {
        showDebugInfo.value = true
      }
    })
    
    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleString()
    }
    
    const debugInfo = computed(() => {
      return {
        currentUrl: window.location.href,
        pathName: window.location.pathname,
        hasToken: !!localStorage.getItem('access_token'),
        deviceCount: deviceCount.value,
        onlineDeviceCount: onlineDeviceCount.value,
        backupCount: backupCount.value,
        recentBackupCount: recentBackupCount.value,
        testResult: testResult.value,
        storageTest: storageTest.value,
        browser: {
          userAgent: navigator.userAgent,
          platform: navigator.platform
        }
      }
    })
    
    const toggleDebugInfo = () => {
      showDebugInfo.value = !showDebugInfo.value
    }
    
    const testClick = () => {
      testResult.value = 'Button clicked at ' + new Date().toLocaleTimeString()
    }
    
    const testLocalStorage = () => {
      try {
        const testKey = 'dashboard_test_' + Date.now()
        localStorage.setItem(testKey, 'Test value')
        const readValue = localStorage.getItem(testKey)
        localStorage.removeItem(testKey)
        
        storageTest.value = {
          success: readValue === 'Test value',
          value: readValue,
          timestamp: new Date().toISOString()
        }
      } catch (error) {
        storageTest.value = {
          success: false,
          error: error.message,
          timestamp: new Date().toISOString()
        }
      }
    }
    
    const goToDebugPage = () => {
      window.location.href = '/debug.html'
    }
    
    return {
      loading,
      error,
      deviceCount,
      onlineDeviceCount,
      backupCount,
      recentBackupCount,
      recentBackups,
      showDebugInfo,
      debugInfo,
      testResult,
      storageTest,
      formatDate,
      toggleDebugInfo,
      testClick,
      testLocalStorage,
      goToDebugPage
    }
  }
}
</script> 