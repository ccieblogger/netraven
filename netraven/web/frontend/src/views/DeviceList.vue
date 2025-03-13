<template>
  <MainLayout>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Devices</h1>
      <button @click="showAddDeviceModal = true" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
        Add Device
      </button>
    </div>
    
    <!-- Filters -->
    <div class="bg-white rounded-lg shadow p-4 mb-6">
      <div class="flex flex-wrap items-center gap-4">
        <div>
          <label for="search" class="block text-sm font-medium text-gray-700 mb-1">Search</label>
          <input 
            type="text" 
            id="search" 
            v-model="searchQuery" 
            placeholder="Search devices..."
            class="border rounded px-3 py-2 w-64"
          >
        </div>
        
        <div>
          <label for="deviceType" class="block text-sm font-medium text-gray-700 mb-1">Device Type</label>
          <select 
            id="deviceType" 
            v-model="deviceTypeFilter"
            class="border rounded px-3 py-2 w-40"
          >
            <option value="">All Types</option>
            <option value="cisco_ios">Cisco IOS</option>
            <option value="juniper_junos">Juniper JunOS</option>
            <option value="arista_eos">Arista EOS</option>
          </select>
        </div>
      </div>
    </div>
    
    <!-- Devices Table -->
    <div class="bg-white rounded-lg shadow overflow-hidden">
      <div v-if="loading" class="p-8 text-center">
        <p>Loading devices...</p>
      </div>
      
      <div v-else-if="filteredDevices.length === 0" class="p-8 text-center">
        <p v-if="searchQuery || deviceTypeFilter" class="text-gray-600">
          No devices match the current filters.
        </p>
        <p v-else class="text-gray-600">
          No devices found. Add your first device to get started.
        </p>
      </div>
      
      <table v-else class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Hostname</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IP Address</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Device Type</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Backup</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="device in filteredDevices" :key="device.id">
            <td class="px-6 py-4 whitespace-nowrap">
              <router-link :to="`/devices/${device.id}`" class="text-blue-600 hover:text-blue-900 font-medium">
                {{ device.hostname }}
              </router-link>
              <p v-if="device.description" class="text-sm text-gray-500">{{ device.description }}</p>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              {{ device.ip_address }}
              <span v-if="device.port !== 22" class="text-gray-500 text-sm">:{{ device.port }}</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              {{ formatDeviceType(device.device_type) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span 
                class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                :class="device.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'"
              >
                {{ device.enabled ? 'Enabled' : 'Disabled' }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span v-if="device.last_backup_at">
                {{ formatDate(device.last_backup_at) }}
                <div 
                  :class="device.last_backup_status === 'success' ? 'text-green-600' : 'text-red-600'"
                  class="text-sm"
                >
                  {{ device.last_backup_status || 'unknown' }}
                </div>
              </span>
              <span v-else class="text-gray-500">Never</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="flex space-x-2">
                <button 
                  @click="backupDevice(device.id)"
                  class="text-blue-600 hover:text-blue-900"
                  :disabled="backingUp === device.id"
                >
                  {{ backingUp === device.id ? 'Backing up...' : 'Backup' }}
                </button>
                <button 
                  @click="editDevice(device)"
                  class="text-green-600 hover:text-green-900"
                >
                  Edit
                </button>
                <button 
                  @click="confirmDelete(device)"
                  class="text-red-600 hover:text-red-900"
                >
                  Delete
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- Add/Edit Device Modal would go here -->
    
    <!-- Delete Confirmation Modal would go here -->
  </MainLayout>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import MainLayout from '../components/MainLayout.vue'
import { useDeviceStore } from '../store/devices'

export default {
  name: 'DeviceList',
  components: {
    MainLayout
  },
  
  setup() {
    const deviceStore = useDeviceStore()
    
    const loading = ref(true)
    const searchQuery = ref('')
    const deviceTypeFilter = ref('')
    const showAddDeviceModal = ref(false)
    const editingDevice = ref(null)
    const showDeleteModal = ref(false)
    const deviceToDelete = ref(null)
    const backingUp = ref(null)
    
    const filteredDevices = computed(() => {
      let devices = deviceStore.devices
      
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        devices = devices.filter(device => 
          device.hostname.toLowerCase().includes(query) ||
          device.ip_address.toLowerCase().includes(query) ||
          (device.description && device.description.toLowerCase().includes(query))
        )
      }
      
      if (deviceTypeFilter.value) {
        devices = devices.filter(device => device.device_type === deviceTypeFilter.value)
      }
      
      return devices
    })
    
    onMounted(async () => {
      loading.value = true
      await deviceStore.fetchDevices()
      loading.value = false
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
    
    const backupDevice = async (deviceId) => {
      backingUp.value = deviceId
      try {
        await deviceStore.backupDevice(deviceId)
        // Refresh the device to get updated backup status
        await deviceStore.fetchDevice(deviceId)
      } catch (error) {
        console.error('Failed to backup device:', error)
      } finally {
        backingUp.value = null
      }
    }
    
    const editDevice = (device) => {
      editingDevice.value = device
      showAddDeviceModal.value = true
    }
    
    const confirmDelete = (device) => {
      deviceToDelete.value = device
      showDeleteModal.value = true
    }
    
    return {
      loading,
      searchQuery,
      deviceTypeFilter,
      filteredDevices,
      showAddDeviceModal,
      editingDevice,
      showDeleteModal,
      deviceToDelete,
      backingUp,
      formatDeviceType,
      formatDate,
      backupDevice,
      editDevice,
      confirmDelete
    }
  }
}
</script> 