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
      <div v-else class="overflow-hidden">
        <DataTable
          :columns="columns"
          :data="recentBackups"
          default-sort="created_at"
          default-order="desc"
        >
          <template #device_hostname="{ item }">
            <router-link 
              :to="`/devices/${item.device_id}`" 
              class="text-blue-600 hover:text-blue-900 inline-flex items-center space-x-1"
            >
              <span>{{ item.device_hostname }}</span>
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </router-link>
          </template>
          <template #activity>
            Configuration Backup
          </template>
          <template #status="{ item }">
            <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                  :class="item.status === 'complete' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'">
              {{ item.status }}
            </span>
          </template>
          <template #created_at="{ item }">
            {{ formatDate(item.created_at) }}
          </template>
        </DataTable>
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
import DataTable from '../components/DataTable.vue'
import { useDeviceStore } from '../store/devices'
import { useBackupStore } from '../store/backups'

export default {
  name: 'Dashboard',
  components: {
    MainLayout,
    DataTable
  },
  
  setup() {
    const deviceStore = useDeviceStore()
    const backupStore = useBackupStore()
    
    const loading = ref(true)
    const error = ref(null)
    
    const columns = [
      { key: 'device_hostname', label: 'Device' },
      { key: 'activity', label: 'Activity' },
      { key: 'status', label: 'Status' },
      { key: 'created_at', label: 'Time' }
    ]
    
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
    })
    
    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleString()
    }
    
    return {
      loading,
      error,
      columns,
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