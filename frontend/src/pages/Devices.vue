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
             <td class="py-3 px-6 text-left">{{ device.port }}</td>
            <td class="py-3 px-6 text-left">
              <span v-for="tag in device.tags" :key="tag.id" class="bg-blue-100 text-blue-600 py-1 px-3 rounded-full text-xs mr-1">
                {{ tag.name }}
              </span>
              <span v-if="!device.tags || device.tags.length === 0">-</span>
            </td>
            <td class="py-3 px-6 text-left">
              <!-- TEMPORARY: Handle credential display until proper tag-based credential matching is implemented -->
              <span v-if="device.credential && device.credential.name">{{ device.credential.name }}</span>
              <span v-else-if="device.credential_id">ID: {{ device.credential_id }}</span>
              <span v-else class="text-gray-400">-</span>
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

onMounted(() => {
    // Fetch devices only if the list is empty initially
    if (devices.value.length === 0) {
         deviceStore.fetchDevices()
    }
})

// Form Modal Handlers
function openCreateModal() {
  selectedDevice.value = null // Ensure create mode
  isFormModalOpen.value = true
}

function openEditModal(device) {
  selectedDevice.value = { ...device } // Pass a copy to avoid reactivity issues
  isFormModalOpen.value = true
}

function closeFormModal() {
  isFormModalOpen.value = false
  selectedDevice.value = null
}

async function handleSaveDevice(deviceData) {
  console.log("Saving device:", deviceData)
  let success = false; // Flag to track success
  try {
      if (deviceData.id) {
        await deviceStore.updateDevice(deviceData.id, deviceData);
      } else {
        await deviceStore.createDevice(deviceData);
      }
      success = true; // Mark as successful
      closeFormModal();
      // Refresh list might still be needed if store isn't fully reactive
      // await deviceStore.fetchDevices();
  } catch (error) {
       console.error("Failed to save device:", error);
       // Show error from the store action directly
       alert(`Error saving device: ${deviceStore.error || 'An unknown error occurred.'}`);
       // Do NOT close the modal on error
  } finally {
      // Optional: Add logic here if needed regardless of success/fail
      // For example, re-enable save button is handled in the modal itself
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

  console.log("Deleting device:", deviceToDelete.value.id)
   let success = false;
  try {
      await deviceStore.deleteDevice(deviceToDelete.value.id);
      success = true;
      closeDeleteModal();
      // Refresh list might still be needed
      // await deviceStore.fetchDevices();
  } catch (error) {
      console.error("Failed to delete device:", error);
      alert(`Error deleting device: ${deviceStore.error || 'An unknown error occurred.'}`);
      // Close modal even on error to avoid being stuck
      closeDeleteModal();
  }
}

</script>

<style scoped>
/* Add any page-specific styles */
</style>
