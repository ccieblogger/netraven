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
    <div v-if="showEditModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center">
      <div class="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div class="p-6">
          <h3 class="text-lg font-medium mb-4">Edit Device</h3>
          
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
                  placeholder="Leave blank to keep current username"
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
                  placeholder="Leave blank to keep current password"
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
                @click="showEditModal = false"
                class="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                :disabled="saving"
                class="bg-blue-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                {{ saving ? 'Saving...' : 'Save Changes' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
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
    const saving = ref(false)
    const errors = ref({})
    
    const deviceId = computed(() => props.id || route.params.id)
    
    const device = computed(() => deviceStore.currentDevice)
    
    const deviceBackups = computed(() => {
      return backupStore.backupsByDevice(deviceId.value)
    })

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
    
    onMounted(async () => {
      loading.value = true
      try {
        await deviceStore.fetchDevice(deviceId.value)
        // Initialize the form with current device data
        if (device.value) {
          deviceForm.value = {
            hostname: device.value.hostname,
            ip_address: device.value.ip_address,
            device_type: device.value.device_type,
            port: device.value.port || 22,
            description: device.value.description || '',
            enabled: device.value.enabled,
            username: '',  // We don't get these from the API for security
            password: ''   // Instead, we'll make them optional in the update
          }
        }
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
    
    const saveDevice = async () => {
      saving.value = true
      errors.value = {}
      
      try {
        console.log('Saving device with data:', deviceForm.value)
        // Remove empty credentials if not provided (they're optional for updates)
        const updateData = { ...deviceForm.value }
        if (!updateData.username) delete updateData.username
        if (!updateData.password) delete updateData.password
        
        await deviceStore.updateDevice(deviceId.value, updateData)
        showEditModal.value = false
        
        // Refresh the device data
        await deviceStore.fetchDevice(deviceId.value)
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
      deviceForm,
      saving,
      errors,
      formatDeviceType,
      formatDate,
      backupDevice,
      restoreBackup,
      saveDevice
    }
  }
}
</script> 