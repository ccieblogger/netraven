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

</script>

<style scoped>
/* Add any page-specific styles */
</style>
