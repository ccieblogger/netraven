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
        <p>Loading...</p>
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
    
    const deviceCount = computed(() => deviceStore.devices.length)
    const onlineDeviceCount = computed(() => {
      // For demo purposes, we'll consider all devices online
      return deviceStore.devices.length
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
      // Sort backups by date (newest first) and take the first 5
      return [...backupStore.backups]
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .slice(0, 5)
    })
    
    onMounted(async () => {
      loading.value = true
      
      try {
        await Promise.all([
          deviceStore.fetchDevices(),
          backupStore.fetchBackups()
        ])
      } catch (error) {
        console.error('Failed to load dashboard data:', error)
      } finally {
        loading.value = false
      }
    })
    
    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleString()
    }
    
    return {
      loading,
      deviceCount,
      onlineDeviceCount,
      backupCount,
      recentBackupCount,
      recentBackups,
      formatDate
    }
  }
}
</script> 