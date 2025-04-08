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
    <div v-if="deviceStore.isLoading" class="text-center py-4">Loading...</div>
    <div v-if="deviceStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
       Error: {{ deviceStore.error }}
    </div>

    <!-- Devices Table -->
    <div v-if="!deviceStore.isLoading && devices.length > 0" class="bg-white shadow-md rounded my-6">
      <table class="min-w-max w-full table-auto">
        <thead>
          <tr class="bg-gray-200 text-gray-600 uppercase text-sm leading-normal">
            <th class="py-3 px-6 text-left">ID</th>
            <th class="py-3 px-6 text-left">Hostname</th>
            <th class="py-3 px-6 text-left">IP Address</th>
            <th class="py-3 px-6 text-left">Type</th>
            <th class="py-3 px-6 text-left">Port</th>
            <th class="py-3 px-6 text-left">Tags</th>
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
            <td class="py-3 px-6 text-center">
              <div class="flex item-center justify-center">
                 <button @click="openEditModal(device)" class="w-4 mr-2 transform hover:text-purple-500 hover:scale-110">✏️</button>
                 <button @click="confirmDelete(device)" class="w-4 mr-2 transform hover:text-red-500 hover:scale-110">🗑️</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- No Devices Message -->
    <div v-if="!deviceStore.isLoading && devices.length === 0" class="text-center text-gray-500 py-6">
      No devices found. Add one!
    </div>

    <!-- TODO: Add Create/Edit Modal Component (requires tag selection) -->

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useDeviceStore } from '../store/device'

const deviceStore = useDeviceStore()
const devices = computed(() => deviceStore.devices)

// Modal state placeholders
const showModal = ref(false)
const selectedDevice = ref(null)
const isEditMode = ref(false)

onMounted(() => {
  deviceStore.fetchDevices()
})

// Placeholder actions
function openCreateModal() {
  alert('Placeholder: Open Create Device Modal');
}
function openEditModal(device) {
   alert(`Placeholder: Open Edit Device Modal for ${device.hostname}`);
}
function confirmDelete(device) {
  if (confirm(`Are you sure you want to delete the device "${device.hostname}"?`)) {
     alert(`Placeholder: Delete device ${device.id}`);
     // deviceStore.deleteDevice(device.id);
  }
}
function closeModal() { /* ... */ }
async function handleSave(data) { /* ... */ }

</script>

<style scoped>
/* Add any page-specific styles */
</style>
