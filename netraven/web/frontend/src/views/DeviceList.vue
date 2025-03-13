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
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Serial Number</th>
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
              {{ device.serial_number || 'Unknown' }}
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
    
    <!-- Add/Edit Device Modal -->
    <div v-if="showAddDeviceModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center">
      <div class="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div class="p-6">
          <h3 class="text-lg font-medium mb-4">{{ editingDevice ? 'Edit Device' : 'Add Device' }}</h3>
          
          <form @submit.prevent="saveDevice">
            <div class="space-y-4">
              <div>
                <label for="hostname" class="block text-sm font-medium text-gray-700">Hostname</label>
                <input
                  type="text"
                  id="hostname"
                  v-model="deviceForm.hostname"
                  required
                  class="mt-1 block w-full border rounded-md shadow-sm py-2 px-3"
                  :class="{'border-red-300': errors.hostname}"
                >
                <p v-if="errors.hostname" class="mt-1 text-sm text-red-600">{{ errors.hostname }}</p>
              </div>
              
              <div>
                <label for="ip_address" class="block text-sm font-medium text-gray-700">IP Address</label>
                <input
                  type="text"
                  id="ip_address"
                  v-model="deviceForm.ip_address"
                  required
                  class="mt-1 block w-full border rounded-md shadow-sm py-2 px-3"
                  :class="{'border-red-300': errors.ip_address}"
                >
                <p v-if="errors.ip_address" class="mt-1 text-sm text-red-600">{{ errors.ip_address }}</p>
              </div>
              
              <div>
                <label for="device_type" class="block text-sm font-medium text-gray-700">Device Type</label>
                <select
                  id="device_type"
                  v-model="deviceForm.device_type"
                  required
                  class="mt-1 block w-full border rounded-md shadow-sm py-2 px-3"
                  :class="{'border-red-300': errors.device_type}"
                >
                  <option value="cisco_ios">Cisco IOS</option>
                  <option value="juniper_junos">Juniper JunOS</option>
                  <option value="arista_eos">Arista EOS</option>
                </select>
                <p v-if="errors.device_type" class="mt-1 text-sm text-red-600">{{ errors.device_type }}</p>
              </div>
              
              <div>
                <label for="port" class="block text-sm font-medium text-gray-700">Port</label>
                <input
                  type="number"
                  id="port"
                  v-model="deviceForm.port"
                  class="mt-1 block w-full border rounded-md shadow-sm py-2 px-3"
                  :class="{'border-red-300': errors.port}"
                >
                <p v-if="errors.port" class="mt-1 text-sm text-red-600">{{ errors.port }}</p>
              </div>
              
              <div>
                <label for="description" class="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  id="description"
                  v-model="deviceForm.description"
                  rows="3"
                  class="mt-1 block w-full border rounded-md shadow-sm py-2 px-3"
                  :class="{'border-red-300': errors.description}"
                ></textarea>
                <p v-if="errors.description" class="mt-1 text-sm text-red-600">{{ errors.description }}</p>
              </div>
              
              <div>
                <label for="username" class="block text-sm font-medium text-gray-700">Username</label>
                <input
                  type="text"
                  id="username"
                  v-model="deviceForm.username"
                  required
                  class="mt-1 block w-full border rounded-md shadow-sm py-2 px-3"
                  :class="{'border-red-300': errors.username}"
                >
                <p v-if="errors.username" class="mt-1 text-sm text-red-600">{{ errors.username }}</p>
              </div>
              
              <div>
                <label for="password" class="block text-sm font-medium text-gray-700">Password</label>
                <input
                  type="password"
                  id="password"
                  v-model="deviceForm.password"
                  required
                  class="mt-1 block w-full border rounded-md shadow-sm py-2 px-3"
                  :class="{'border-red-300': errors.password}"
                >
                <p v-if="errors.password" class="mt-1 text-sm text-red-600">{{ errors.password }}</p>
              </div>
              
              <div class="flex items-center">
                <input
                  type="checkbox"
                  id="enabled"
                  v-model="deviceForm.enabled"
                  class="h-4 w-4 text-blue-600 border-gray-300 rounded"
                >
                <label for="enabled" class="ml-2 block text-sm text-gray-900">Device Enabled</label>
              </div>
            </div>
            
            <div class="mt-6 flex justify-end space-x-3">
              <button
                type="button"
                @click="showAddDeviceModal = false"
                class="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                :disabled="saving"
                class="bg-blue-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                {{ saving ? 'Saving...' : (editingDevice ? 'Save Changes' : 'Add Device') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
    
    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center">
      <div class="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div class="p-6">
          <h3 class="text-lg font-medium mb-4">Delete Device</h3>
          <p class="text-gray-600 mb-4">
            Are you sure you want to delete {{ deviceToDelete?.hostname }}? This action cannot be undone.
          </p>
          
          <div class="flex justify-end space-x-3">
            <button
              @click="showDeleteModal = false"
              class="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              @click="deleteDevice"
              :disabled="deleting"
              class="bg-red-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-red-700"
            >
              {{ deleting ? 'Deleting...' : 'Delete' }}
            </button>
          </div>
        </div>
      </div>
    </div>
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
    const saving = ref(false)
    const deleting = ref(false)
    const searchQuery = ref('')
    const deviceTypeFilter = ref('')
    const showAddDeviceModal = ref(false)
    const editingDevice = ref(null)
    const showDeleteModal = ref(false)
    const deviceToDelete = ref(null)
    const backingUp = ref(null)
    const errors = ref({})
    
    const deviceForm = ref({
      hostname: '',
      ip_address: '',
      device_type: 'cisco_ios',
      port: 22,
      description: '',
      enabled: true,
      username: '',
      password: ''
    })
    
    const resetForm = () => {
      deviceForm.value = {
        hostname: '',
        ip_address: '',
        device_type: 'cisco_ios',
        port: 22,
        description: '',
        enabled: true,
        username: '',
        password: ''
      }
      errors.value = {}
    }
    
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
      deviceForm.value = {
        hostname: device.hostname,
        ip_address: device.ip_address,
        device_type: device.device_type,
        port: device.port || 22,
        description: device.description || '',
        enabled: device.enabled,
        username: device.username || '',
        password: device.password || ''
      }
      showAddDeviceModal.value = true
    }
    
    const saveDevice = async () => {
      saving.value = true
      errors.value = {}
      
      try {
        console.log('Saving device with data:', deviceForm.value)
        if (editingDevice.value) {
          await deviceStore.updateDevice(editingDevice.value.id, deviceForm.value)
        } else {
          await deviceStore.createDevice(deviceForm.value)
        }
        showAddDeviceModal.value = false
        resetForm()
      } catch (error) {
        console.error('Failed to save device:', error)
        console.error('Error response:', error.response?.data)
        if (error.response?.data?.detail) {
          // Handle validation errors from the API
          if (Array.isArray(error.response.data.detail)) {
            // Handle FastAPI validation errors
            error.response.data.detail.forEach(err => {
              const field = err.loc[err.loc.length - 1]
              errors.value[field] = err.msg
            })
          } else if (typeof error.response.data.detail === 'object') {
            errors.value = error.response.data.detail
          } else {
            errors.value = { general: error.response.data.detail }
          }
        }
      } finally {
        saving.value = false
      }
    }
    
    const confirmDelete = (device) => {
      deviceToDelete.value = device
      showDeleteModal.value = true
    }
    
    const deleteDevice = async () => {
      if (!deviceToDelete.value) return
      
      deleting.value = true
      try {
        await deviceStore.deleteDevice(deviceToDelete.value.id)
        showDeleteModal.value = false
        deviceToDelete.value = null
      } catch (error) {
        console.error('Failed to delete device:', error)
      } finally {
        deleting.value = false
      }
    }
    
    return {
      loading,
      saving,
      deleting,
      searchQuery,
      deviceTypeFilter,
      showAddDeviceModal,
      editingDevice,
      showDeleteModal,
      deviceToDelete,
      backingUp,
      deviceForm,
      errors,
      filteredDevices,
      formatDeviceType,
      formatDate,
      backupDevice,
      editDevice,
      saveDevice,
      confirmDelete,
      deleteDevice
    }
  }
}
</script> 