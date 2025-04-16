<template>
  <div class="job-monitor">
    <div class="bg-white shadow-md rounded-lg overflow-hidden">
      <!-- Header with job info -->
      <div class="bg-gray-100 p-4 border-b border-gray-200">
        <div class="flex justify-between items-center">
          <div>
            <h3 class="text-lg font-semibold">
              Job: {{ job ? job.name : 'Loading...' }}
              <span class="text-sm font-normal text-gray-500 ml-2">#{{ jobId }}</span>
            </h3>
            <div class="text-sm text-gray-600">
              <span v-if="job && job.description">{{ job.description }}</span>
            </div>
          </div>
          <div class="flex items-center">
            <span class="mr-3 text-sm">
              <span v-if="job">Status: </span>
              <span :class="statusClass">{{ statusText }}</span>
            </span>
            <button 
              v-if="canRefresh" 
              @click="fetchJobStatus"
              class="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 text-sm"
              :disabled="isLoading"
            >
              <span v-if="isLoading">Refreshing...</span>
              <span v-else>Refresh</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Loading indicator -->
      <div v-if="isLoading && !job" class="p-8 text-center">
        <div class="text-blue-500 font-semibold">Loading job status...</div>
      </div>

      <!-- Error display -->
      <div v-else-if="error" class="p-8 text-center">
        <div class="text-red-500">{{ error }}</div>
        <button 
          @click="fetchJobStatus" 
          class="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Try Again
        </button>
      </div>

      <!-- Job details -->
      <div v-else-if="job" class="p-4">
        <!-- Job metadata -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div class="bg-gray-50 p-3 rounded border border-gray-200">
            <div class="text-xs text-gray-500">Scheduled Time</div>
            <div>{{ formatDateTime(job.scheduled_for) || 'N/A' }}</div>
          </div>
          <div class="bg-gray-50 p-3 rounded border border-gray-200">
            <div class="text-xs text-gray-500">Start Time</div>
            <div>{{ formatDateTime(job.started_at) || 'Pending' }}</div>
          </div>
          <div class="bg-gray-50 p-3 rounded border border-gray-200">
            <div class="text-xs text-gray-500">End Time</div>
            <div>{{ formatDateTime(job.completed_at) || 'Running...' }}</div>
          </div>
        </div>

        <!-- Progress bar for overall completion -->
        <div v-if="!job.completed_at && deviceResults.length > 0" class="mb-6">
          <div class="flex justify-between items-center mb-1">
            <div class="text-sm font-medium">Overall Progress</div>
            <div class="text-sm text-gray-500">{{ completedCount }}/{{ deviceResults.length }} devices</div>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-2.5">
            <div 
              class="bg-blue-600 h-2.5 rounded-full" 
              :style="{ width: `${overallProgress}%` }"
            ></div>
          </div>
        </div>

        <!-- Device Results Table -->
        <div class="mt-6">
          <h4 class="text-md font-semibold mb-3">Device Status</h4>
          
          <div v-if="deviceResults.length === 0" class="text-center py-6 bg-gray-50 rounded border border-gray-200">
            <p v-if="job.status === 'PENDING'" class="text-gray-500">Job has not started processing devices yet</p>
            <p v-else class="text-gray-500">No device results available</p>
          </div>
          
          <table v-else class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Device</th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Started</th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Completed</th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="result in deviceResults" :key="result.device_id">
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="font-medium text-gray-900">{{ result.device_name || `Device #${result.device_id}` }}</div>
                  <div class="text-xs text-gray-500">{{ result.device_ip || '' }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="getStatusBadgeClass(result.status)" class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full">
                    {{ result.status }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDateTime(result.started_at) || 'Pending' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDateTime(result.completed_at) || '-' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <a 
                    v-if="result.has_log" 
                    @click="viewDeviceLog(result)" 
                    class="text-indigo-600 hover:text-indigo-900 cursor-pointer"
                  >View Log</a>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Actions -->
        <div class="mt-6 flex justify-end">
          <button 
            v-if="canRetry" 
            @click="retryFailedDevices"
            class="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2 mr-3"
          >
            Retry Failed Devices
          </button>
          <button 
            v-if="job.status === 'COMPLETED' || job.status === 'FAILED'"
            @click="navigateToDiff"
            class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
          >
            View Config Changes
          </button>
        </div>
      </div>
    </div>

    <!-- Device Log Modal -->
    <BaseModal 
      :is-open="isLogModalOpen" 
      :title="`Log: ${selectedDevice ? selectedDevice.device_name || `Device #${selectedDevice.device_id}` : ''}`"
      @close="closeLogModal"
    >
      <template #content>
        <div v-if="deviceLogLoading" class="text-center py-4">
          <div class="text-blue-500">Loading log data...</div>
        </div>
        <div v-else-if="deviceLogError" class="text-center py-4">
          <div class="text-red-500">{{ deviceLogError }}</div>
        </div>
        <div v-else-if="deviceLog" class="bg-gray-50 p-4 rounded overflow-auto max-h-96 font-mono text-sm">
          <pre>{{ deviceLog }}</pre>
        </div>
      </template>
    </BaseModal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useJobStore } from '../store/job';
import { useNotificationStore } from '../store/notifications';
import BaseModal from './BaseModal.vue';
import axios from 'axios';

const props = defineProps({
  jobId: {
    type: [Number, String],
    required: true
  },
  autoRefresh: {
    type: Boolean,
    default: true
  },
  refreshInterval: {
    type: Number,
    default: 5000 // 5 seconds
  }
});

// State
const router = useRouter();
const jobStore = useJobStore();
const notificationStore = useNotificationStore();
const job = ref(null);
const isLoading = ref(false);
const error = ref(null);
const deviceResults = ref([]);
const refreshTimer = ref(null);
const isLogModalOpen = ref(false);
const selectedDevice = ref(null);
const deviceLog = ref('');
const deviceLogLoading = ref(false);
const deviceLogError = ref(null);

// Computed properties
const statusText = computed(() => {
  if (!job.value) return 'Loading...';
  return job.value.status || 'UNKNOWN';
});

const statusClass = computed(() => {
  if (!job.value) return '';
  
  switch (job.value.status) {
    case 'COMPLETED_SUCCESS': return 'text-green-500';
    case 'RUNNING': return 'text-blue-500';
    case 'PENDING': return 'text-yellow-500';
    case 'COMPLETED_PARTIAL_FAILURE': return 'text-orange-500';
    case 'COMPLETED_FAILURE': return 'text-red-500';
    case 'FAILED_UNEXPECTED': return 'text-red-500';
    case 'FAILED_DISPATCHER_ERROR': return 'text-red-500';
    case 'COMPLETED_NO_DEVICES': return 'text-gray-500';
    // New credential-related statuses
    case 'COMPLETED_NO_CREDENTIALS': return 'text-yellow-500';
    case 'FAILED_CREDENTIAL_RESOLUTION': return 'text-red-500';
    default: return 'text-gray-500';
  }
});

const canRefresh = computed(() => {
  if (!job.value) return false;
  return ['RUNNING', 'PENDING'].includes(job.value.status);
});

const canRetry = computed(() => {
  if (!job.value) return false;
  // Check if there are any failed devices
  return deviceResults.value.some(device => device.status === 'FAILED');
});

const completedCount = computed(() => {
  return deviceResults.value.filter(device => 
    ['COMPLETED', 'FAILED'].includes(device.status)
  ).length;
});

const overallProgress = computed(() => {
  if (deviceResults.value.length === 0) return 0;
  return (completedCount.value / deviceResults.value.length) * 100;
});

// Methods
function formatDateTime(dateTime) {
  if (!dateTime) return null;
  return new Date(dateTime).toLocaleString();
}

function getStatusBadgeClass(status) {
  switch (status) {
    case 'COMPLETED': 
    case 'COMPLETED_SUCCESS': 
      return 'bg-green-100 text-green-800';
    case 'RUNNING': 
      return 'bg-blue-100 text-blue-800';
    case 'PENDING': 
      return 'bg-yellow-100 text-yellow-800';
    case 'COMPLETED_PARTIAL_FAILURE': 
      return 'bg-orange-100 text-orange-800';
    case 'COMPLETED_FAILURE': 
    case 'FAILED_UNEXPECTED': 
    case 'FAILED_DISPATCHER_ERROR': 
    case 'FAILED_CREDENTIAL_RESOLUTION':
      return 'bg-red-100 text-red-800';
    case 'COMPLETED_NO_DEVICES':
      return 'bg-gray-100 text-gray-800';
    case 'COMPLETED_NO_CREDENTIALS':
      return 'bg-yellow-100 text-yellow-800';
    default: 
      return 'bg-gray-100 text-gray-800';
  }
}

async function fetchJobStatus() {
  isLoading.value = true;
  error.value = null;
  
  try {
    // Fetch job details
    const jobResponse = await axios.get(`/api/jobs/${props.jobId}`);
    job.value = jobResponse.data;
    
    // Fetch device results for this job
    const deviceResponse = await axios.get(`/api/jobs/${props.jobId}/devices`);
    deviceResults.value = deviceResponse.data;
    
    // If job is complete, stop auto-refresh
    if (job.value.status === 'COMPLETED' || job.value.status === 'FAILED') {
      stopAutoRefresh();
    }
  } catch (err) {
    console.error('Error fetching job status:', err);
    error.value = err.response?.data?.detail || 'Failed to load job status';
    notificationStore.error('Failed to load job status');
  } finally {
    isLoading.value = false;
  }
}

function setupAutoRefresh() {
  if (props.autoRefresh) {
    refreshTimer.value = setInterval(() => {
      if (canRefresh.value) {
        fetchJobStatus();
      } else {
        stopAutoRefresh();
      }
    }, props.refreshInterval);
  }
}

function stopAutoRefresh() {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value);
    refreshTimer.value = null;
  }
}

async function viewDeviceLog(device) {
  selectedDevice.value = device;
  isLogModalOpen.value = true;
  deviceLogLoading.value = true;
  deviceLogError.value = null;
  
  try {
    const response = await axios.get(`/api/jobs/${props.jobId}/devices/${device.device_id}/logs`);
    deviceLog.value = response.data.log || 'No log data available';
  } catch (err) {
    console.error('Error fetching device log:', err);
    deviceLogError.value = 'Failed to load device log';
  } finally {
    deviceLogLoading.value = false;
  }
}

function closeLogModal() {
  isLogModalOpen.value = false;
  selectedDevice.value = null;
  deviceLog.value = '';
}

async function retryFailedDevices() {
  try {
    await axios.post(`/api/jobs/${props.jobId}/retry-failed`);
    notificationStore.success('Retry initiated for failed devices');
    await fetchJobStatus(); // Refresh the job status
  } catch (err) {
    console.error('Error retrying failed devices:', err);
    notificationStore.error('Failed to retry failed devices');
  }
}

function navigateToDiff() {
  // Extract device IDs from device results
  const deviceIds = deviceResults.value.map(result => result.device_id);
  
  if (deviceIds.length > 0) {
    router.push({
      name: 'ConfigDiff',
      query: { 
        deviceId: deviceIds[0], // Pre-select first device
        jobId: props.jobId // Pre-select this job for filtering
      }
    });
  } else {
    notificationStore.error('No devices found to view configurations');
  }
}

// Lifecycle hooks
onMounted(() => {
  fetchJobStatus();
  setupAutoRefresh();
});

onBeforeUnmount(() => {
  stopAutoRefresh();
});

// Watch for job ID changes
watch(() => props.jobId, () => {
  fetchJobStatus();
  setupAutoRefresh();
});
</script> 