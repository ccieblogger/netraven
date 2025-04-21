<template>
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-semibold mb-4">Manage Devices</h1>

    <!-- Add Device Button -->
    <div class="mb-4 text-right">
      <button @click="openCreateModal" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
        + Add Device
      </button>
    </div>

    <!-- Loading/Error Indicators -->
    <div v-if="deviceStore.isLoading && devices.length === 0" class="text-center py-4">Loading devices...</div>
    <div v-if="deviceStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
       Error fetching devices: {{ deviceStore.error }}
    </div>

    <!-- Devices Table -->
    <!-- Show skeleton or previous data while loading updates -->
    <div v-if="devices.length > 0" class="bg-white shadow-md rounded my-6" :class="{ 'opacity-50': deviceStore.isLoading }">
      <table class="min-w-max w-full table-auto">
        <thead>
          <tr class="bg-gray-200 text-gray-600 uppercase text-sm leading-normal">
            <th class="py-3 px-6 text-left">ID</th>
            <th class="py-3 px-6 text-left">Hostname</th>
            <th class="py-3 px-6 text-left">IP Address</th>
            <th class="py-3 px-6 text-left">Type</th>
            <th class="py-3 px-6 text-left">Reachability</th>
            <th class="py-3 px-6 text-left">Description</th>
            <th class="py-3 px-6 text-left">Port</th>
            <th class="py-3 px-6 text-left">Tags</th>
            <th class="py-3 px-6 text-left">Credential</th>
            <th class="py-3 px-6 text-center">Actions</th>
          </tr>
        </thead>
        <tbody class="text-gray-600 text-sm font-light">
          <tr v-for="device in devices" :key="device.id" class="border-b border-gray-200 hover:bg-gray-100">
            <td class="py-3 px-6 text-left whitespace-nowrap">{{ device.id }}</td>
            <td class="py-3 px-6 text-left">{{ device.hostname }}</td>
            <td class="py-3 px-6 text-left">{{ device.ip_address }}</td>
            <td class="py-3 px-6 text-left">{{ device.device_type }}</td>
            <td class="py-3 px-6 text-left">
              <span
                @mouseenter="activeReachabilityPopover = device.id"
                @mouseleave="activeReachabilityPopover = null"
                class="relative cursor-pointer"
              >
                <svg v-if="device.last_reachability_status === 'success'" class="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                <svg v-else-if="device.last_reachability_status === 'failure'" class="h-5 w-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                <svg v-else class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"/></svg>
                <!-- Popover -->
                <div
                  v-if="activeReachabilityPopover === device.id"
                  class="absolute z-10 left-0 mt-2 bg-white border border-gray-200 rounded shadow-lg p-3 w-64"
                >
                  <div class="font-medium mb-1">
                    <span v-if="device.last_reachability_status === 'success'" class="text-green-600">Reachable</span>
                    <span v-else-if="device.last_reachability_status === 'failure'" class="text-red-600">Unreachable</span>
                    <span v-else class="text-gray-400">Never Checked</span>
                  </div>
                  <div v-if="device.last_reachability_timestamp" class="text-xs text-gray-500 mb-1">
                    Last checked: {{ formatDateTime(device.last_reachability_timestamp) }}
                  </div>
                  <div v-if="device.last_reachability_message" class="text-xs text-gray-700">
                    {{ device.last_reachability_message }}
                  </div>
                </div>
              </span>
            </td>
            <td class="py-3 px-6 text-left">{{ device.description || '-' }}</td>
            <td class="py-3 px-6 text-left">{{ device.port }}</td>
            <td class="py-3 px-6 text-left">
              <span v-for="tag in device.tags" :key="tag.id" class="bg-blue-100 text-blue-600 py-1 px-3 rounded-full text-xs mr-1">
                {{ tag.name }}
              </span>
              <span v-if="!device.tags || device.tags.length === 0">-</span>
            </td>
            <td class="py-3 px-6 text-left">
              <!-- Updated credential display with count and hover -->
              <div v-if="device.matching_credentials_count > 0" class="relative">
                <span 
                  @mouseenter="showCredentialPopover(device.id)" 
                  @mouseleave="hideCredentialPopover()"
                  class="text-blue-600 cursor-pointer hover:text-blue-800 underline"
                >
                  {{ device.matching_credentials_count }} credential(s)
                </span>
                <!-- Popover that appears on hover -->
                <div 
                  v-if="activeCredentialPopover === device.id"
                  class="absolute z-10 left-0 mt-1 bg-white border border-gray-200 rounded shadow-lg p-2 w-64"
                >
                  <h3 class="text-sm font-medium mb-1">Matching Credentials:</h3>
                  <div v-if="isLoadingDeviceCredentials" class="text-sm text-gray-500">Loading...</div>
                  <ul v-else class="text-xs max-h-48 overflow-y-auto">
                    <li v-for="cred in deviceCredentials" :key="cred.id" class="py-1 border-b border-gray-100 last:border-b-0">
                      <div class="font-medium">{{ cred.username }} (ID: {{ cred.id }})</div>
                      <div class="text-gray-500">Priority: {{ cred.priority }}</div>
                    </li>
                  </ul>
                </div>
              </div>
              <span v-else class="text-red-500 font-semibold">No credentials found.</span>
            </td>
            <td class="py-3 px-6 text-center">
              <div class="flex item-center justify-center">
                 <button @click="openEditModal(device)" class="w-4 mr-2 transform hover:text-purple-500 hover:scale-110">
                    <PencilIcon class="h-4 w-4" />
                 </button>
                 <button @click="openDeleteModal(device)" class="w-4 mr-2 transform hover:text-red-500 hover:scale-110">
                    <TrashIcon class="h-4 w-4" />
                 </button>
                 <!-- Check Reachability Button -->
                 <button
                   :disabled="device.status === 'offline' || reachabilityLoading[device.id]"
                   @click="checkReachability(device)"
                   class="w-6 h-6 flex items-center justify-center rounded-full bg-green-100 hover:bg-green-200 text-green-700 ml-2 disabled:opacity-50 disabled:cursor-not-allowed"
                   :title="device.status === 'offline' ? 'Device offline' : 'Check Reachability'"
                 >
                   <span v-if="reachabilityLoading[device.id]">
                     <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/></svg>
                   </span>
                   <span v-else>
                     <!-- Network check icon -->
                     <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2l4-4m5 2a9 9 0 11-18 0a9 9 0 0118 0z" /></svg>
                   </span>
                 </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- No Devices Message -->
    <div v-if="!deviceStore.isLoading && devices.length === 0" class="text-center py-12">
      <div class="text-gray-500 mb-4">
        <h3 class="text-lg font-medium">No devices found</h3>
        <p>Get started by adding your first network device</p>
      </div>
      <button @click="openCreateModal" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
        + Add Device
      </button>
    </div>

    <!-- Create/Edit Modal -->
     <DeviceFormModal
        :is-open="isFormModalOpen"
        :device-to-edit="selectedDevice"
        :backend-error="deviceStore.error"
        @close="closeFormModal"
        @save="handleSaveDevice"
      />

     <!-- Delete Confirmation Modal -->
      <DeleteConfirmationModal
        :is-open="isDeleteModalOpen"
        item-type="device"
        :item-name="deviceToDelete?.hostname"
        @close="closeDeleteModal"
        @confirm="handleDeleteConfirm"
      />

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useDeviceStore } from '../store/device'
import DeviceFormModal from '../components/DeviceFormModal.vue'
import DeleteConfirmationModal from '../components/DeleteConfirmationModal.vue'
import { PencilIcon, TrashIcon } from '@heroicons/vue/24/outline' // Using outline icons
import api from '../services/api' // assumed API service
import { useRouter } from 'vue-router'
import { useNotificationStore } from '../store/notifications'
import { useJobStore } from '../store/job'

const deviceStore = useDeviceStore()
const devices = computed(() => deviceStore.devices)

// Modal States
const isFormModalOpen = ref(false)
const selectedDevice = ref(null) // null for create, device object for edit
const isDeleteModalOpen = ref(false)
const deviceToDelete = ref(null)

// Add credential popover logic
const activeCredentialPopover = ref(null);
const deviceCredentials = ref([]);
const isLoadingDeviceCredentials = ref(false);

const router = useRouter()
const notificationStore = useNotificationStore()
const reachabilityLoading = ref({}) // Track loading state per device
const jobStore = useJobStore()

const activeReachabilityPopover = ref(null);

onMounted(() => {
    // Fetch devices only if the list is empty initially
    if (devices.value.length === 0) {
         deviceStore.fetchDevices()
    }
})

// Form Modal Handlers
function openCreateModal() {
  selectedDevice.value = null // Ensure create mode
  deviceStore.error = null // Clear error before opening
  isFormModalOpen.value = true
}

function openEditModal(device) {
  selectedDevice.value = { ...device } // Pass a copy to avoid reactivity issues
  deviceStore.error = null // Clear error before opening
  isFormModalOpen.value = true
}

function closeFormModal() {
  isFormModalOpen.value = false
  selectedDevice.value = null
}

async function handleSaveDevice(deviceData) {
  let success = false; // Flag to track success
  try {
      if (deviceData.id) {
        success = await deviceStore.updateDevice(deviceData.id, deviceData);
      } else {
        success = await deviceStore.createDevice(deviceData);
      }
      if (success) {
        closeFormModal();
        await deviceStore.fetchDevices(); // Always refresh after create/update
      }
  } catch (error) {
       // Pass error to modal for inline display
       // The modal will handle displaying the error
       // No alert here
  }
}


// Delete Modal Handlers
function openDeleteModal(device) {
  deviceToDelete.value = device
  isDeleteModalOpen.value = true
}

function closeDeleteModal() {
  isDeleteModalOpen.value = false
  deviceToDelete.value = null
}

async function handleDeleteConfirm() {
  if (!deviceToDelete.value) return;
  let success = false;
  try {
      success = await deviceStore.deleteDevice(deviceToDelete.value.id);
      if (success) {
        closeDeleteModal();
        await deviceStore.fetchDevices(); // Always refresh after delete
      }
  } catch (error) {
      // No alert here; could be handled inline if needed
      closeDeleteModal();
  }
}

async function showCredentialPopover(deviceId) {
  activeCredentialPopover.value = deviceId;
  if (deviceId) {
    isLoadingDeviceCredentials.value = true;
    try {
      const credentials = await deviceStore.fetchDeviceCredentials(deviceId);
      // Debugging statement removed to avoid unintended console output in production.
      deviceCredentials.value = credentials;
      // Removed debug logging of credential details to avoid exposing sensitive information in production.
    } catch (error) {
      console.error("Error fetching device credentials:", error);
    } finally {
      isLoadingDeviceCredentials.value = false;
    }
  }
}

function hideCredentialPopover() {
  activeCredentialPopover.value = null;
}

async function checkReachability(device) {
  reachabilityLoading.value[device.id] = true
  try {
    // Debug: log device and jobs
    console.log('Device:', device);
    if (!jobStore.jobs.length) {
      await jobStore.fetchJobs();
    }
    console.log('Jobs:', jobStore.jobs);
    // 2. Find a reachability job for this device (prefer device_id match, then tag match)
    let reachJob = jobStore.jobs.find(j => j.job_type === 'reachability' && j.device_id === device.id);
    if (!reachJob && device.tags && device.tags.length > 0) {
      const deviceTagIds = device.tags.map(t => t.id);
      reachJob = jobStore.jobs.find(j => j.job_type === 'reachability' && j.tags && j.tags.some(tag => deviceTagIds.includes(tag.id)));
    }
    if (!reachJob) {
      notificationStore.error('No reachability job found for this device.');
      return;
    }
    // 3. Trigger the job
    const ok = await jobStore.runJobNow(reachJob.id);
    if (ok && jobStore.runStatus && jobStore.runStatus.data && jobStore.runStatus.data.job_id) {
      notificationStore.success('Reachability job started!');
      router.push(`/jobs/${jobStore.runStatus.data.job_id}`);
    } else {
      notificationStore.error(jobStore.runStatus?.error || 'Failed to start reachability job');
    }
  } catch (err) {
    notificationStore.error('Failed to start reachability job');
  } finally {
    reachabilityLoading.value[device.id] = false;
  }
}

function formatDateTime(dateTimeString) {
  if (!dateTimeString) return '-';
  try {
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(dateTimeString).toLocaleString(undefined, options);
  } catch (e) {
    return dateTimeString; // Return original if formatting fails
  }
}

function reachabilityTooltip(device, statusText) {
  if (device.last_reachability_timestamp) {
    return `${statusText} (${formatDateTime(device.last_reachability_timestamp)})`;
  }
  return statusText;
}

</script>

<style scoped>
/* Add any page-specific styles */
</style>
