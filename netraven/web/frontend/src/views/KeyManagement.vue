<template>
  <div class="key-management">
    <div class="mb-6">
      <h1 class="text-2xl font-semibold mb-2">Key Management</h1>
      <p class="text-gray-600">Manage API keys for external integrations</p>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex justify-center my-8">
      <div class="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]"></div>
    </div>

    <!-- Error message -->
    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Error!</strong>
      <span class="block sm:inline"> {{ error }}</span>
    </div>

    <!-- Key list -->
    <div v-if="!loading && keys.length > 0" class="bg-white shadow rounded-lg overflow-hidden mb-6">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Expires</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Scopes</th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="key in keys" :key="key.id">
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm font-medium text-gray-900">{{ key.name }}</div>
              <div class="text-sm text-gray-500">{{ key.prefix }}...</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm text-gray-900">{{ formatDate(key.created_at) }}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm text-gray-900">
                {{ key.expires_at ? formatDate(key.expires_at) : 'Never' }}
              </div>
            </td>
            <td class="px-6 py-4">
              <div class="flex flex-wrap gap-1">
                <span 
                  v-for="scope in key.scopes" 
                  :key="scope" 
                  class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                >
                  {{ scope }}
                </span>
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
              <button 
                @click="confirmRevokeKey(key)" 
                class="text-red-600 hover:text-red-900"
              >
                Revoke
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty state -->
    <div v-if="!loading && keys.length === 0" class="text-center my-12">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">No API Keys</h3>
      <p class="mt-1 text-sm text-gray-500">Get started by creating a new API key.</p>
    </div>

    <!-- Create Key Button -->
    <div class="mt-6">
      <button 
        @click="showCreateKeyModal = true" 
        class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        <svg class="-ml-1 mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path fill-rule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clip-rule="evenodd" />
        </svg>
        Create API Key
      </button>
    </div>

    <!-- Create Key Modal -->
    <div v-if="showCreateKeyModal" class="fixed z-10 inset-0 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true" @click="showCreateKeyModal = false"></div>

        <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
        <div class="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          <div>
            <div class="mt-3 text-center sm:mt-5">
              <h3 class="text-lg leading-6 font-medium text-gray-900" id="modal-title">Create New API Key</h3>
              <div class="mt-2">
                <p class="text-sm text-gray-500">
                  Create a new API key for external integrations. API keys provide programmatic access to the NetRaven API.
                </p>
              </div>
            </div>
          </div>

          <form class="mt-5 space-y-4" @submit.prevent="createKey">
            <div>
              <label for="key-name" class="block text-sm font-medium text-gray-700">Key Name</label>
              <input 
                type="text" 
                name="key-name" 
                id="key-name" 
                v-model="newKey.name"
                required
                class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="My API Key"
              />
            </div>

            <div>
              <label for="key-expiration" class="block text-sm font-medium text-gray-700">Expiration</label>
              <select 
                id="key-expiration" 
                name="key-expiration" 
                v-model="newKey.expiration"
                class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="never">Never</option>
                <option value="30days">30 Days</option>
                <option value="90days">90 Days</option>
                <option value="1year">1 Year</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700">Permissions</label>
              <div class="mt-2 space-y-2">
                <div class="flex items-start">
                  <div class="flex items-center h-5">
                    <input 
                      id="read-devices" 
                      name="read-devices" 
                      type="checkbox" 
                      v-model="newKey.scopes.readDevices"
                      class="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                  </div>
                  <div class="ml-3 text-sm">
                    <label for="read-devices" class="font-medium text-gray-700">Read Devices</label>
                    <p class="text-gray-500">View device information and status</p>
                  </div>
                </div>
                <div class="flex items-start">
                  <div class="flex items-center h-5">
                    <input 
                      id="write-devices" 
                      name="write-devices" 
                      type="checkbox" 
                      v-model="newKey.scopes.writeDevices"
                      class="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                  </div>
                  <div class="ml-3 text-sm">
                    <label for="write-devices" class="font-medium text-gray-700">Write Devices</label>
                    <p class="text-gray-500">Create and manage devices</p>
                  </div>
                </div>
                <div class="flex items-start">
                  <div class="flex items-center h-5">
                    <input 
                      id="read-backups" 
                      name="read-backups" 
                      type="checkbox" 
                      v-model="newKey.scopes.readBackups"
                      class="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                  </div>
                  <div class="ml-3 text-sm">
                    <label for="read-backups" class="font-medium text-gray-700">Read Backups</label>
                    <p class="text-gray-500">View and download device backups</p>
                  </div>
                </div>
                <div class="flex items-start">
                  <div class="flex items-center h-5">
                    <input 
                      id="run-jobs" 
                      name="run-jobs" 
                      type="checkbox" 
                      v-model="newKey.scopes.runJobs"
                      class="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                  </div>
                  <div class="ml-3 text-sm">
                    <label for="run-jobs" class="font-medium text-gray-700">Run Jobs</label>
                    <p class="text-gray-500">Trigger backup and other jobs</p>
                  </div>
                </div>
              </div>
            </div>

            <div class="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
              <button 
                type="submit" 
                class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:col-start-2 sm:text-sm"
                :disabled="createLoading"
              >
                <span v-if="createLoading" class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-current border-r-transparent align-[-0.125em] mr-2"></span>
                Create
              </button>
              <button 
                type="button" 
                class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:col-start-1 sm:text-sm"
                @click="showCreateKeyModal = false"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Display New Key Modal -->
    <div v-if="newKeyCreated" class="fixed z-10 inset-0 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>

        <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
        <div class="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          <div>
            <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
              <svg class="h-6 w-6 text-green-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div class="mt-3 text-center sm:mt-5">
              <h3 class="text-lg leading-6 font-medium text-gray-900" id="modal-title">API Key Created</h3>
              <div class="mt-2">
                <p class="text-sm text-gray-500">
                  Your new API key has been created. Please copy it now as you won't be able to see it again.
                </p>
                <div class="mt-4">
                  <label for="api-key" class="sr-only">API Key</label>
                  <div class="mt-1 relative rounded-md shadow-sm">
                    <input 
                      id="api-key" 
                      ref="apiKeyInput"
                      type="text" 
                      class="block w-full pr-10 border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      :value="newKeyValue" 
                      readonly
                    />
                    <div class="absolute inset-y-0 right-0 flex items-center pr-3">
                      <button 
                        @click="copyApiKey" 
                        class="text-gray-400 hover:text-gray-500 focus:outline-none"
                      >
                        <span v-if="keyCopied" class="text-green-500 text-sm">Copied!</span>
                        <svg v-else class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                          <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" />
                          <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="mt-5 sm:mt-6">
            <button 
              type="button" 
              class="inline-flex justify-center w-full rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm"
              @click="closeNewKeyModal"
            >
              I've Saved My Key
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Confirm Revocation Modal -->
    <div v-if="keyToRevoke" class="fixed z-10 inset-0 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true" @click="keyToRevoke = null"></div>

        <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
        <div class="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          <div>
            <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
              <svg class="h-6 w-6 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div class="mt-3 text-center sm:mt-5">
              <h3 class="text-lg leading-6 font-medium text-gray-900" id="modal-title">Revoke API Key</h3>
              <div class="mt-2">
                <p class="text-sm text-gray-500">
                  Are you sure you want to revoke the API key "{{ keyToRevoke?.name }}"? This action cannot be undone.
                </p>
              </div>
            </div>
          </div>
          <div class="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
            <button 
              type="button" 
              class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:col-start-2 sm:text-sm"
              @click="revokeKey"
              :disabled="revokeLoading"
            >
              <span v-if="revokeLoading" class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-current border-r-transparent align-[-0.125em] mr-2"></span>
              Revoke
            </button>
            <button 
              type="button" 
              class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:col-start-1 sm:text-sm"
              @click="keyToRevoke = null"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import { useNotificationStore } from '../views/notification.js';
import apiClient from '../api/api';

export default {
  name: 'KeyManagement',
  
  setup() {
    const notificationStore = useNotificationStore();
    
    // State variables
    const keys = ref([]);
    const loading = ref(true);
    const error = ref(null);
    const showCreateKeyModal = ref(false);
    const createLoading = ref(false);
    const newKeyCreated = ref(false);
    const newKeyValue = ref('');
    const keyCopied = ref(false);
    const keyToRevoke = ref(null);
    const revokeLoading = ref(false);
    const apiKeyInput = ref(null);
    
    const newKey = ref({
      name: '',
      expiration: 'never',
      scopes: {
        readDevices: false,
        writeDevices: false,
        readBackups: false,
        runJobs: false
      }
    });
    
    // Fetch API keys
    const fetchKeys = async () => {
      loading.value = true;
      error.value = null;
      
      try {
        const response = await apiClient.get('/api/keys');
        keys.value = response.data;
      } catch (err) {
        console.error('Error fetching API keys:', err);
        error.value = err.response?.data?.message || err.message || 'Failed to fetch API keys';
        notificationStore.error(error.value);
      } finally {
        loading.value = false;
      }
    };
    
    // Create a new API key
    const createKey = async () => {
      createLoading.value = true;
      
      try {
        // Convert scopes from object to array
        const scopes = [];
        if (newKey.value.scopes.readDevices) scopes.push('read:devices');
        if (newKey.value.scopes.writeDevices) scopes.push('write:devices');
        if (newKey.value.scopes.readBackups) scopes.push('read:backups');
        if (newKey.value.scopes.runJobs) scopes.push('run:jobs');
        
        // Calculate expiration date based on selection
        let expiresAt = null;
        if (newKey.value.expiration !== 'never') {
          const now = new Date();
          
          switch (newKey.value.expiration) {
            case '30days':
              expiresAt = new Date(now.setDate(now.getDate() + 30));
              break;
            case '90days':
              expiresAt = new Date(now.setDate(now.getDate() + 90));
              break;
            case '1year':
              expiresAt = new Date(now.setFullYear(now.getFullYear() + 1));
              break;
          }
        }
        
        // API request
        const response = await apiClient.post('/api/keys', {
          name: newKey.value.name,
          expires_at: expiresAt ? expiresAt.toISOString() : null,
          scopes
        });
        
        // Store the full key value to display to user
        newKeyValue.value = response.data.key;
        
        // Update the keys list
        await fetchKeys();
        
        // Reset form
        newKey.value = {
          name: '',
          expiration: 'never',
          scopes: {
            readDevices: false,
            writeDevices: false,
            readBackups: false,
            runJobs: false
          }
        };
        
        // Show the new key modal
        showCreateKeyModal.value = false;
        newKeyCreated.value = true;
        
      } catch (err) {
        console.error('Error creating API key:', err);
        const errorMessage = err.response?.data?.message || err.message || 'Failed to create API key';
        notificationStore.error(errorMessage);
      } finally {
        createLoading.value = false;
      }
    };
    
    // Copy API key to clipboard
    const copyApiKey = () => {
      if (apiKeyInput.value) {
        apiKeyInput.value.select();
        document.execCommand('copy');
        keyCopied.value = true;
        
        setTimeout(() => {
          keyCopied.value = false;
        }, 2000);
      }
    };
    
    // Close the new key modal
    const closeNewKeyModal = () => {
      newKeyCreated.value = false;
      newKeyValue.value = '';
    };
    
    // Confirm key revocation
    const confirmRevokeKey = (key) => {
      keyToRevoke.value = key;
    };
    
    // Revoke an API key
    const revokeKey = async () => {
      if (!keyToRevoke.value) return;
      
      revokeLoading.value = true;
      
      try {
        await apiClient.delete(`/api/keys/${keyToRevoke.value.id}`);
        
        // Update the keys list
        await fetchKeys();
        
        // Close the modal
        keyToRevoke.value = null;
        
        // Show notification
        notificationStore.success('API key revoked successfully');
      } catch (err) {
        console.error('Error revoking API key:', err);
        const errorMessage = err.response?.data?.message || err.message || 'Failed to revoke API key';
        notificationStore.error(errorMessage);
      } finally {
        revokeLoading.value = false;
      }
    };
    
    // Format date for display
    const formatDate = (dateString) => {
      if (!dateString) return '';
      
      const date = new Date(dateString);
      return date.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    };
    
    // Lifecycle hooks
    onMounted(() => {
      fetchKeys();
    });
    
    return {
      keys,
      loading,
      error,
      newKey,
      showCreateKeyModal,
      createLoading,
      newKeyCreated,
      newKeyValue,
      keyCopied,
      keyToRevoke,
      revokeLoading,
      apiKeyInput,
      createKey,
      copyApiKey,
      closeNewKeyModal,
      confirmRevokeKey,
      revokeKey,
      formatDate
    };
  }
};
</script> 