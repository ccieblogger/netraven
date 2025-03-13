<template>
  <MainLayout>
    <div v-if="loading" class="text-center py-8">
      <p>Loading device details...</p>
    </div>
    
    <div v-else-if="!device" class="text-center py-8">
      <p class="text-red-600">Device not found</p>
      <router-link to="/devices" class="text-blue-600 hover:underline mt-4 inline-block">
        Back to Devices
      </router-link>
    </div>
    
    <div v-else>
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold">Device: {{ device.hostname }}</h1>
        <div class="flex space-x-2">
          <button 
            @click="backupDevice" 
            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
            :disabled="backingUp"
          >
            {{ backingUp ? 'Backing up...' : 'Backup Now' }}
          </button>
          <button 
            @click="showEditModal = true" 
            class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded"
          >
            Edit Device
          </button>
        </div>
      </div>
      
      <!-- Device Details -->
      <div class="bg-white rounded-lg shadow p-6 mb-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h2 class="text-lg font-semibold mb-4">Basic Information</h2>
            <div class="space-y-2">
              <div class="flex justify-between">
                <span class="text-gray-600">Hostname:</span>
                <span class="font-medium">{{ device.hostname }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">IP Address:</span>
                <span class="font-medium">{{ device.ip_address }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Port:</span>
                <span class="font-medium">{{ device.port || 22 }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Device Type:</span>
                <span class="font-medium">{{ formatDeviceType(device.device_type) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Status:</span>
                <span 
                  class="font-medium"
                  :class="device.enabled ? 'text-green-600' : 'text-gray-600'"
                >
                  {{ device.enabled ? 'Enabled' : 'Disabled' }}
                </span>
              </div>
            </div>
          </div>
          
          <div>
            <h2 class="text-lg font-semibold mb-4">Backup Information</h2>
            <div class="space-y-2">
              <div class="flex justify-between">
                <span class="text-gray-600">Last Backup:</span>
                <span class="font-medium">{{ device.last_backup_at ? formatDate(device.last_backup_at) : 'Never' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Backup Status:</span>
                <span 
                  class="font-medium"
                  :class="device.last_backup_status === 'success' ? 'text-green-600' : 'text-red-600'"
                >
                  {{ device.last_backup_status || 'N/A' }}
                </span>
              </div>
            </div>
            
            <div class="mt-4">
              <h3 class="text-md font-semibold mb-2">Description</h3>
              <p class="text-gray-700">{{ device.description || 'No description provided.' }}</p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Recent Backups -->
      <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-lg font-semibold mb-4">Recent Backups</h2>
        <div v-if="loadingBackups" class="text-center py-4">
          <p>Loading backups...</p>
        </div>
        <div v-else-if="deviceBackups.length === 0" class="text-center py-4 text-gray-500">
          <p>No backups found for this device.</p>
        </div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Version</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="backup in deviceBackups" :key="backup.id">
                <td class="px-6 py-4 whitespace-nowrap">
                  {{ formatDate(backup.created_at) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                    :class="backup.status === 'complete' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'">
                    {{ backup.status }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  {{ backup.version }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex space-x-2">
                    <router-link :to="`/backups/${backup.id}`" class="text-blue-600 hover:text-blue-900">
                      View
                    </router-link>
                    <button @click="restoreBackup(backup.id)" class="text-green-600 hover:text-green-900">
                      Restore
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    
    <!-- Edit Device Modal would go here -->
  </MainLayout>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import MainLayout from '../components/MainLayout.vue'
import { useDeviceStore } from '../store/devices'
import { useBackupStore } from '../store/backups'

export default {
  name: 'DeviceDetail',
  components: {
    MainLayout
  },
  
  props: {
    id: {
      type: String,
      required: true
    }
  },
  
  setup(props) {
    const route = useRoute()
    const deviceStore = useDeviceStore()
    const backupStore = useBackupStore()
    
    const loading = ref(true)
    const loadingBackups = ref(true)
    const backingUp = ref(false)
    const showEditModal = ref(false)
    
    const deviceId = computed(() => props.id || route.params.id)
    
    const device = computed(() => deviceStore.currentDevice)
    
    const deviceBackups = computed(() => {
      return backupStore.backupsByDevice(deviceId.value)
    })
    
    onMounted(async () => {
      loading.value = true
      try {
        await deviceStore.fetchDevice(deviceId.value)
      } catch (error) {
        console.error('Failed to fetch device:', error)
      } finally {
        loading.value = false
      }
      
      loadingBackups.value = true
      try {
        await backupStore.fetchBackups({ device_id: deviceId.value })
      } catch (error) {
        console.error('Failed to fetch backups:', error)
      } finally {
        loadingBackups.value = false
      }
    })
    
    const formatDeviceType = (type) => {
      const typeMap = {
        'cisco_ios': 'Cisco IOS',
        'juniper_junos': 'Juniper JunOS',
        'arista_eos': 'Arista EOS'
      }
      return typeMap[type] || type
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return 'Never'
      const date = new Date(dateString)
      return date.toLocaleString()
    }
    
    const backupDevice = async () => {
      backingUp.value = true
      try {
        await deviceStore.backupDevice(deviceId.value)
        // Refresh the device to get updated backup status
        await deviceStore.fetchDevice(deviceId.value)
        // Refresh backups
        await backupStore.fetchBackups({ device_id: deviceId.value })
      } catch (error) {
        console.error('Failed to backup device:', error)
      } finally {
        backingUp.value = false
      }
    }
    
    const restoreBackup = async (backupId) => {
      try {
        await backupStore.restoreBackup(backupId)
        // Refresh the device to get updated status
        await deviceStore.fetchDevice(deviceId.value)
      } catch (error) {
        console.error('Failed to restore backup:', error)
      }
    }
    
    return {
      loading,
      loadingBackups,
      device,
      deviceBackups,
      backingUp,
      showEditModal,
      formatDeviceType,
      formatDate,
      backupDevice,
      restoreBackup
    }
  }
}
</script> 