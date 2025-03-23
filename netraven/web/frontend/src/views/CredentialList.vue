<template>
  <MainLayout>
    <div>
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold">Credentials</h1>
        <div class="flex space-x-2">
          <button 
            @click="openCredentialModal()" 
            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded flex items-center"
          >
            <i class="fas fa-plus mr-2"></i> Add Credential
          </button>
        </div>
      </div>

      <!-- Loading state -->
      <div v-if="loading" class="flex justify-center items-center h-64">
        <div class="spinner"></div>
      </div>

      <!-- Empty state -->
      <div v-else-if="credentials.length === 0" class="bg-white rounded-lg shadow p-6 text-center">
        <div class="text-gray-500 mb-4">
          <i class="fas fa-key text-5xl mb-4"></i>
          <h3 class="text-xl font-medium">No credentials found</h3>
          <p class="text-gray-500 mt-2">Add your first credential to get started.</p>
        </div>
        <button 
          @click="openCredentialModal()" 
          class="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded inline-flex items-center"
        >
          <i class="fas fa-plus mr-2"></i> Add Credential
        </button>
      </div>

      <!-- Credentials table -->
      <div v-else class="bg-white rounded-lg shadow overflow-hidden">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Credential Name
              </th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Username
              </th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Tags
              </th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Success/Failure
              </th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="credential in credentials" :key="credential.id">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ credential.name }}</div>
                <div class="text-sm text-gray-500">{{ credential.description || 'No description' }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ credential.username }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span v-if="credential.key_file_path" class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                  Key File
                </span>
                <span v-else class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                  Password
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex flex-wrap gap-1">
                  <span 
                    v-for="tag in credential.tags" 
                    :key="tag.id" 
                    :style="{ backgroundColor: tag.color + '33', color: tag.color }"
                    class="px-2 py-1 rounded text-xs"
                  >
                    {{ tag.name }}
                  </span>
                  <span 
                    v-if="!credential.tags || credential.tags.length === 0" 
                    class="text-xs text-gray-500"
                  >
                    No tags
                  </span>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center space-x-1">
                  <span class="text-green-600 font-medium">{{ credential.success_count || 0 }}</span>
                  <span>/</span>
                  <span class="text-red-600 font-medium">{{ credential.failure_count || 0 }}</span>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {{ formatDate(credential.created_at) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <div class="flex space-x-2">
                  <button @click="openTestModal(credential)" class="text-indigo-600 hover:text-indigo-900">
                    <i class="fas fa-vial"></i>
                  </button>
                  <button @click="openCredentialModal(credential)" class="text-blue-600 hover:text-blue-900">
                    <i class="fas fa-edit"></i>
                  </button>
                  <button @click="openDeleteConfirmation(credential)" class="text-red-600 hover:text-red-900">
                    <i class="fas fa-trash"></i>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Credential modal -->
      <div v-if="showCredentialModal" class="fixed inset-0 z-50 overflow-auto bg-black bg-opacity-50 flex items-center justify-center">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4">
          <div class="flex justify-between items-center p-4 border-b">
            <h3 class="text-xl font-medium">{{ editingCredential ? 'Edit' : 'Add' }} Credential</h3>
            <button @click="closeCredentialModal" class="text-gray-500 hover:text-gray-700">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <form @submit.prevent="saveCredential">
            <div class="p-4 space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Name</label>
                <input 
                  v-model="credentialForm.name" 
                  type="text" 
                  required
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Description</label>
                <textarea 
                  v-model="credentialForm.description" 
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  rows="2"
                ></textarea>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Username</label>
                <input 
                  v-model="credentialForm.username" 
                  type="text" 
                  required
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
              </div>
              <div v-if="!editingCredential || !credentialForm.key_file_path">
                <label class="block text-sm font-medium text-gray-700">Password</label>
                <input 
                  v-model="credentialForm.password" 
                  :type="showPassword ? 'text' : 'password'" 
                  :required="!credentialForm.key_file_path && !editingCredential"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                <div class="mt-1 flex items-center">
                  <input 
                    id="showPassword" 
                    type="checkbox" 
                    v-model="showPassword" 
                    class="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                  >
                  <label for="showPassword" class="ml-2 block text-sm text-gray-700">Show password</label>
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Key File Path</label>
                <input 
                  v-model="credentialForm.key_file_path" 
                  type="text" 
                  placeholder="Path to SSH key file (optional)"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Tags</label>
                <div v-if="loadingTags" class="mt-1 text-sm text-gray-500">Loading tags...</div>
                <div v-else-if="availableTags.length === 0" class="mt-1 text-sm text-gray-500">No tags available</div>
                <div v-else class="mt-1">
                  <select 
                    v-model="selectedTagId" 
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  >
                    <option value="">Select a tag</option>
                    <option v-for="tag in availableTags" :key="tag.id" :value="tag.id">{{ tag.name }}</option>
                  </select>
                  <button 
                    v-if="selectedTagId" 
                    @click.prevent="addTagToCredential" 
                    class="mt-2 inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Add Tag
                  </button>
                </div>
                <div class="mt-2 flex flex-wrap gap-2">
                  <div 
                    v-for="tag in credentialForm.tags" 
                    :key="tag.id" 
                    :style="{ backgroundColor: tag.color + '33', color: tag.color }"
                    class="inline-flex items-center px-2 py-1 rounded text-sm"
                  >
                    {{ tag.name }}
                    <button 
                      @click.prevent="removeTagFromCredential(tag.id)" 
                      class="ml-1 text-gray-500 hover:text-gray-700"
                    >
                      <i class="fas fa-times-circle"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
            <div class="px-4 py-3 bg-gray-50 text-right sm:px-6 flex justify-end space-x-2">
              <button 
                type="button" 
                @click="closeCredentialModal" 
                class="inline-flex justify-center py-2 px-4 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </button>
              <button 
                type="submit" 
                class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                :disabled="saving"
              >
                {{ saving ? 'Saving...' : 'Save' }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Test modal -->
      <div v-if="showTestModal" class="fixed inset-0 z-50 overflow-auto bg-black bg-opacity-50 flex items-center justify-center">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
          <div class="flex justify-between items-center p-4 border-b">
            <h3 class="text-xl font-medium">Test Credential</h3>
            <button @click="closeTestModal" class="text-gray-500 hover:text-gray-700">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <form @submit.prevent="testCredential">
            <div class="p-4 space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Hostname</label>
                <input 
                  v-model="testForm.hostname" 
                  type="text" 
                  required
                  placeholder="e.g., 192.168.1.1"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Device Type</label>
                <select 
                  v-model="testForm.deviceType" 
                  required
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value="cisco_ios">Cisco IOS</option>
                  <option value="cisco_ios_xe">Cisco IOS XE</option>
                  <option value="cisco_nxos">Cisco NX-OS</option>
                  <option value="juniper_junos">Juniper JunOS</option>
                  <option value="arista_eos">Arista EOS</option>
                  <option value="linux">Linux</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Port</label>
                <input 
                  v-model.number="testForm.port" 
                  type="number" 
                  min="1"
                  max="65535"
                  class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
              </div>
              <div v-if="testResult" class="mt-4 p-4 rounded" :class="testResult.success ? 'bg-green-100' : 'bg-red-100'">
                <div class="flex items-center">
                  <i class="fas" :class="testResult.success ? 'fa-check-circle text-green-600' : 'fa-times-circle text-red-600'"></i>
                  <span class="ml-2 font-medium" :class="testResult.success ? 'text-green-800' : 'text-red-800'">
                    {{ testResult.success ? 'Connection successful' : 'Connection failed' }}
                  </span>
                </div>
                <div class="mt-2 text-sm" :class="testResult.success ? 'text-green-700' : 'text-red-700'">
                  Time: {{ testResult.time_taken }}ms
                </div>
              </div>
            </div>
            <div class="px-4 py-3 bg-gray-50 text-right sm:px-6 flex justify-end space-x-2">
              <button 
                type="button" 
                @click="closeTestModal" 
                class="inline-flex justify-center py-2 px-4 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Close
              </button>
              <button 
                type="submit" 
                class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                :disabled="testing"
              >
                {{ testing ? 'Testing...' : 'Test Connection' }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Delete confirmation dialog -->
      <div v-if="showDeleteConfirmation" class="fixed inset-0 z-50 overflow-auto bg-black bg-opacity-50 flex items-center justify-center">
        <div class="bg-white rounded-lg shadow-xl max-w-md mx-4 w-full">
          <div class="p-4">
            <div class="flex items-start">
              <div class="flex-shrink-0 text-red-600">
                <i class="fas fa-exclamation-triangle text-2xl"></i>
              </div>
              <div class="ml-3">
                <h3 class="text-lg font-medium text-gray-900">Delete Credential</h3>
                <div class="mt-2">
                  <p class="text-sm text-gray-500">
                    Are you sure you want to delete the credential "{{ credentialToDelete?.name }}"? This action cannot be undone.
                  </p>
                </div>
              </div>
            </div>
          </div>
          <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button 
              @click="confirmDelete" 
              class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm"
              :disabled="deleting"
            >
              {{ deleting ? 'Deleting...' : 'Delete' }}
            </button>
            <button 
              @click="cancelDelete" 
              class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { useCredentialStore } from '../store/credential'
import { useTagStore } from '../store/tag'
import { format } from 'date-fns'
import MainLayout from '../components/MainLayout.vue'

export default {
  name: 'CredentialList',
  components: {
    MainLayout
  },
  
  setup() {
    const credentialStore = useCredentialStore()
    const tagStore = useTagStore()
    
    // State
    const credentials = computed(() => credentialStore.credentials)
    const availableTags = computed(() => tagStore.tags)
    const loading = computed(() => credentialStore.loading || tagStore.loading)
    const error = computed(() => credentialStore.error || tagStore.error)
    
    const saving = ref(false)
    const testing = ref(false)
    const deleting = ref(false)
    
    // Modals
    const showCredentialModal = ref(false)
    const showTestModal = ref(false)
    const showDeleteConfirmation = ref(false)
    const showPassword = ref(false)
    
    // Forms
    const credentialForm = reactive({
      name: '',
      description: '',
      username: '',
      password: '',
      key_file_path: '',
      tags: []
    })
    
    const testForm = reactive({
      hostname: '',
      deviceType: 'cisco_ios',
      port: 22
    })
    
    // Selected values
    const selectedTagId = ref('')
    const editingCredential = ref(null)
    const testingCredential = ref(null)
    const credentialToDelete = ref(null)
    const testResult = computed(() => credentialStore.testResults)
    
    // Load data
    const loadCredentials = async () => {
      await credentialStore.fetchCredentials()
    }
    
    const loadTags = async () => {
      await tagStore.fetchTags()
    }
    
    // Modal functions
    const openCredentialModal = (credential = null) => {
      resetCredentialForm()
      
      if (credential) {
        editingCredential.value = credential
        credentialForm.name = credential.name
        credentialForm.description = credential.description || ''
        credentialForm.username = credential.username
        credentialForm.key_file_path = credential.key_file_path || ''
        credentialForm.tags = [...(credential.tags || [])]
      } else {
        editingCredential.value = null
      }
      
      showCredentialModal.value = true
    }
    
    const closeCredentialModal = () => {
      showCredentialModal.value = false
      resetCredentialForm()
    }
    
    const resetCredentialForm = () => {
      credentialForm.name = ''
      credentialForm.description = ''
      credentialForm.username = ''
      credentialForm.password = ''
      credentialForm.key_file_path = ''
      credentialForm.tags = []
      selectedTagId.value = ''
      editingCredential.value = null
      showPassword.value = false
    }
    
    const openTestModal = (credential) => {
      testingCredential.value = credential
      resetTestForm()
      showTestModal.value = true
    }
    
    const closeTestModal = () => {
      showTestModal.value = false
      testingCredential.value = null
    }
    
    const resetTestForm = () => {
      testForm.hostname = ''
      testForm.deviceType = 'cisco_ios'
      testForm.port = 22
    }
    
    const openDeleteConfirmation = (credential) => {
      credentialToDelete.value = credential
      showDeleteConfirmation.value = true
    }
    
    const cancelDelete = () => {
      showDeleteConfirmation.value = false
      credentialToDelete.value = null
    }
    
    // Form actions
    const addTagToCredential = () => {
      if (!selectedTagId.value) return
      
      const tagExists = credentialForm.tags.some(tag => tag.id === selectedTagId.value)
      if (tagExists) return
      
      const tagToAdd = availableTags.value.find(tag => tag.id === selectedTagId.value)
      if (tagToAdd) {
        credentialForm.tags.push({...tagToAdd})
        selectedTagId.value = ''
      }
    }
    
    const removeTagFromCredential = (tagId) => {
      credentialForm.tags = credentialForm.tags.filter(tag => tag.id !== tagId)
    }
    
    const saveCredential = async () => {
      saving.value = true
      
      try {
        const credentialData = {
          name: credentialForm.name,
          description: credentialForm.description,
          username: credentialForm.username,
          password: credentialForm.password,
          key_file_path: credentialForm.key_file_path,
          tags: credentialForm.tags.map(tag => tag.id)
        }
        
        if (editingCredential.value) {
          // Update existing credential
          await credentialStore.updateCredential(editingCredential.value.id, credentialData)
        } else {
          // Create new credential
          await credentialStore.createCredential(credentialData)
        }
        
        // Close modal
        closeCredentialModal()
      } catch (error) {
        console.error('Error saving credential:', error)
      } finally {
        saving.value = false
      }
    }
    
    const testCredential = async () => {
      if (!testingCredential.value) return
      
      testing.value = true
      
      try {
        await credentialStore.testCredential(testingCredential.value.id, {
          hostname: testForm.hostname,
          device_type: testForm.deviceType,
          port: testForm.port
        })
      } catch (error) {
        console.error('Error testing credential:', error)
      } finally {
        testing.value = false
      }
    }
    
    const confirmDelete = async () => {
      if (!credentialToDelete.value) return
      
      deleting.value = true
      
      try {
        await credentialStore.deleteCredential(credentialToDelete.value.id)
        
        // Close modal
        cancelDelete()
      } catch (error) {
        console.error('Error deleting credential:', error)
      } finally {
        deleting.value = false
      }
    }
    
    // Helper functions
    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return format(date, 'MMM d, yyyy')
    }
    
    // Lifecycle hooks
    onMounted(async () => {
      await Promise.all([loadCredentials(), loadTags()])
    })
    
    return {
      credentials,
      availableTags,
      loading,
      error,
      saving,
      testing,
      deleting,
      showCredentialModal,
      showTestModal,
      showDeleteConfirmation,
      showPassword,
      credentialForm,
      testForm,
      selectedTagId,
      editingCredential,
      testingCredential,
      credentialToDelete,
      testResult,
      openCredentialModal,
      closeCredentialModal,
      resetCredentialForm,
      openTestModal,
      closeTestModal,
      resetTestForm,
      openDeleteConfirmation,
      cancelDelete,
      addTagToCredential,
      removeTagFromCredential,
      saveCredential,
      testCredential,
      confirmDelete,
      formatDate
    }
  }
}
</script>

<style scoped>
.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border-left-color: #3b82f6;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style> 