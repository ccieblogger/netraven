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
      <DeviceTable
        :devices="devices"
        :loading="deviceStore.isLoading"
        :page-size="10"
        :filters="{}"
        @timeline="openTimelinePanel"
        @edit="openEditModal"
        @delete="openDeleteModal"
        @check-reachability="checkReachability"
        @credential-check="showCredentialPopover"
        @view-configs="() => {}"
      />
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

     <!-- Timeline Panel -->
     <TimelinePanel
        :isOpen="showTimelinePanel"
        :device="timelineDevice"
        @close="closeTimelinePanel"
      />

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useDeviceStore } from '../store/device'
import DeviceFormModal from '../components/DeviceFormModal.vue'
import DeleteConfirmationModal from '../components/DeleteConfirmationModal.vue'
import TimelinePanel from '../components/TimelinePanel.vue'
import DeviceTable from '../components/DeviceTable.vue'
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

// Timeline Panel States
const showTimelinePanel = ref(false);
const timelineDevice = ref(null);

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

// Timeline Panel Handlers
function openTimelinePanel(device) {
  timelineDevice.value = device;
  showTimelinePanel.value = true;
}

function closeTimelinePanel() {
  showTimelinePanel.value = false;
  timelineDevice.value = null;
}

</script>

<style scoped>
/* Add any page-specific styles */
</style>
