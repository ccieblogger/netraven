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
            
            <!-- Tags -->
            <div class="mb-6">
              <div class="flex justify-between items-center mb-2">
                <h3 class="text-lg font-medium">Tags</h3>
                <button 
                  @click.stop.prevent="openTagModal" 
                  class="text-sm bg-indigo-600 hover:bg-indigo-700 text-white py-1 px-3 rounded transition-colors"
                >
                  Manage Tags
                </button>
              </div>
              
              <div class="flex flex-wrap gap-2">
                <span 
                  v-for="tag in deviceTags" 
                  :key="tag.id"
                  class="px-3 py-1 rounded-full text-sm"
                  :style="{ backgroundColor: tag.color || '#6366F1', color: 'white' }"
                >
                  {{ formatTagName(tag.name) }}
                </span>
                <span v-if="!deviceTags || deviceTags.length === 0" class="text-gray-500 italic">
                  No tags assigned
                </span>
              </div>
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
    
    <!-- Edit Device Modal -->
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
    
    <!-- Tag Management Modal -->
    <TagModal 
      :show="showTagModal" 
      :device-id="deviceId"
      @close="closeTagModal"
      @update:tags="updateDeviceTags"
      @open-create-tag="showCreateTagModal = true"
    />
    
    <!-- Create Tag Modal -->
    <div v-if="showCreateTagModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div class="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md p-6 mx-4 overflow-hidden" @click.stop>
        <button 
          class="absolute top-4 right-4 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200" 
          @click="showCreateTagModal = false"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
        
        <h2 class="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Create New Tag</h2>
        
        <form @submit.prevent="createTag">
          <div class="space-y-4">
            <div>
              <label for="tagName" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Tag Name</label>
              <input
                type="text"
                id="tagName"
                v-model="newTag.name"
                required
                class="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-gray-900 bg-white"
              />
            </div>
            
            <div>
              <label for="tagColor" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Color</label>
              <div class="flex items-center mt-1">
                <input
                  type="color"
                  id="tagColor"
                  v-model="newTag.color"
                  class="w-10 h-10 rounded border border-gray-300 dark:border-gray-600"
                />
                <span class="ml-2 text-sm text-gray-600 dark:text-gray-400">{{ newTag.color }}</span>
              </div>
            </div>
            
            <div>
              <label for="tagDescription" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Description (optional)</label>
              <textarea
                id="tagDescription"
                v-model="newTag.description"
                rows="2"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-gray-900 bg-white"
              ></textarea>
            </div>
          </div>
          
          <div class="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              @click="showCreateTagModal = false"
              class="py-2 px-4 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
            >
              Cancel
            </button>
            <button
              type="submit"
              :disabled="creatingTag"
              class="py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {{ creatingTag ? 'Creating...' : 'Create Tag' }}
            </button>
          </div>
          
          <div 
            v-if="createTagError" 
            class="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-md"
          >
            {{ createTagError }}
          </div>
        </form>
      </div>
    </div>
  </MainLayout>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Teleport } from 'vue'
import MainLayout from '@/components/MainLayout.vue'
import TagBadge from '@/components/TagBadge.vue'
import { useDeviceStore } from '@/store/devices'
import { useBackupStore } from '@/store/backups'
import { useTagStore } from '@/store/tags'
import TagModal from '@/components/TagModal.vue'

export default {
  name: 'DeviceDetail',
  components: {
    MainLayout,
    TagBadge,
    TagModal
  },
  props: {
    id: {
      type: String,
      required: false
    }
  },
  setup(props) {
    const route = useRoute()
    const deviceStore = useDeviceStore()
    const backupStore = useBackupStore()
    const tagStore = useTagStore()
    
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
    
    const deviceTags = ref([])
    const allTags = computed(() => tagStore.tags)
    const loadingTags = computed(() => tagStore.loading)
    const showTagModal = ref(false)
    const selectedTagId = ref('')
    
    const showCreateTagModal = ref(false)
    const creatingTag = ref(false)
    const createTagError = ref(null)
    const newTag = ref({
      name: '',
      color: '#6366F1', // Default indigo color
      description: ''
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
      
      // Fetch tags for the device
      await fetchDeviceTags()
      // Fetch all tags
      await tagStore.fetchTags()
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
    
    // Format tag name by removing "tag-" prefix if present
    const formatTagName = (name) => {
      if (!name) return ''
      return name.startsWith('tag-') ? name.substring(4) : name
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
    
    const availableTags = computed(() => {
      if (!deviceTags.value || !allTags.value) return []
      
      // Filter out tags that are already assigned to the device
      return allTags.value.filter(tag => !deviceTags.value.some(dt => dt.id === tag.id))
    })
    
    const addTagToDevice = async (tagId) => {
      if (!tagId) return
      
      try {
        await tagStore.assignTagToDevice(deviceId.value, tagId)
        
        // Refresh device tags
        await fetchDeviceTags()
        // Refresh device data
        await deviceStore.fetchDevice(deviceId.value)
      } catch (error) {
        console.error('Error adding tag to device:', error)
        alert(`Failed to add tag: ${error.response?.data?.detail || error.message}`)
      }
    }
    
    const removeTagFromDevice = async (tagId) => {
      if (!tagId) return
      
      try {
        await tagStore.removeTagFromDevice(deviceId.value, tagId)
        
        // Refresh device tags
        await fetchDeviceTags()
        // Refresh device data
        await deviceStore.fetchDevice(deviceId.value)
      } catch (error) {
        console.error('Error removing tag from device:', error)
        alert(`Failed to remove tag: ${error.response?.data?.detail || error.message}`)
      }
    }
    
    const fetchDeviceTags = async () => {
      if (!deviceId.value) return
      
      try {
        const tags = await tagStore.fetchTagsForDevice(deviceId.value)
        deviceTags.value = tags
      } catch (error) {
        console.error('Failed to fetch device tags:', error)
      }
    }
    
    const openTagModal = (event) => {
      if (event) {
        event.preventDefault()
        event.stopPropagation()
      }
      showTagModal.value = true
      return false // Prevent link navigation
    }
    
    const closeTagModal = () => {
      console.log('Closing tag modal');
      showTagModal.value = false;
    }
    
    const updateDeviceTags = (tags) => {
      console.log('Updating device tags:', tags);
      deviceTags.value = tags || [];
    }
    
    const createTag = async () => {
      if (!newTag.value.name) {
        console.error('Tag name is required');
        createTagError.value = 'Tag name is required';
        return;
      }
      
      console.log('Creating new tag:', newTag.value);
      creatingTag.value = true;
      createTagError.value = null;
      
      try {
        // Create the tag
        const tag = await tagStore.createTag(newTag.value);
        console.log('Tag created successfully:', tag);
        
        // Close the modal
        showCreateTagModal.value = false;
        
        // Reset form
        newTag.value = {
          name: '',
          color: '#6366F1',
          description: ''
        };
        
        // Refresh tags list
        await tagStore.fetchTags();
        
        // If device id exists, assign the tag to the device
        if (deviceId.value && tag) {
          await tagStore.assignTagToDevice(deviceId.value, tag.id);
          await fetchDeviceTags();
        }
        
        // If the tag modal is open, close it and reopen to refresh
        if (showTagModal.value) {
          showTagModal.value = false;
          setTimeout(() => {
            showTagModal.value = true;
          }, 100);
        }
      } catch (error) {
        console.error('Failed to create tag:', error);
        createTagError.value = 'Failed to create tag. Please try again.';
      } finally {
        creatingTag.value = false;
      }
    }
    
    return {
      device,
      loading,
      deviceBackups,
      loadingBackups,
      backingUp,
      showEditModal,
      deviceForm,
      saving,
      errors,
      formatDeviceType,
      formatDate,
      formatTagName,
      backupDevice,
      restoreBackup,
      saveDevice,
      deviceTags,
      loadingTags,
      showTagModal,
      openTagModal,
      closeTagModal,
      updateDeviceTags,
      availableTags,
      addTagToDevice,
      removeTagFromDevice,
      showCreateTagModal,
      creatingTag,
      createTagError,
      newTag,
      createTag,
      deviceId
    }
  }
}
</script> 