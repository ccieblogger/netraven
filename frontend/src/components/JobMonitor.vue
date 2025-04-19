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
              <span v-if="job && job.job_type === 'reachability'" class="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                <svg class="h-4 w-4 mr-1 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2l4-4m5 2a9 9 0 11-18 0a9 9 0 0118 0z" /></svg>
                Check Reachability
              </span>
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
          
          <!-- Reachability Job Table -->
          <table v-else-if="job && job.job_type === 'reachability'" class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Device</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reachability Results</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Started</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Completed</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="result in deviceResults" :key="result.device_id">
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="font-medium text-gray-900">{{ result.device_name || `Device #${result.device_id}` }}</div>
                  <div class="text-xs text-gray-500">{{ result.device_ip || '' }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex flex-col space-y-1">
                    <!-- ICMP Ping -->
                    <div class="flex items-center">
                      <span v-if="result.icmp_ping && result.icmp_ping.success" class="text-green-600 mr-1" title="Ping Success">
                        <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                      </span>
                      <span v-else class="text-red-600 mr-1" title="Ping Failed">
                        <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                      </span>
                      <span class="font-semibold">ICMP:</span>
                      <span v-if="result.icmp_ping && result.icmp_ping.success" class="ml-1">{{ result.icmp_ping.latency }} ms</span>
                      <span v-else-if="result.icmp_ping && result.icmp_ping.error" class="ml-1 text-xs text-gray-500">{{ result.icmp_ping.error }}</span>
                      <span v-else class="ml-1 text-xs text-gray-400">No data</span>
                    </div>
                    <!-- TCP 22 -->
                    <div class="flex items-center">
                      <span v-if="result.tcp_22 && result.tcp_22.success" class="text-green-600 mr-1" title="TCP 22 Success">
                        <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                      </span>
                      <span v-else class="text-red-600 mr-1" title="TCP 22 Failed">
                        <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                      </span>
                      <span class="font-semibold">TCP 22:</span>
                      <span v-if="result.tcp_22 && result.tcp_22.success" class="ml-1">Open</span>
                      <span v-else-if="result.tcp_22 && result.tcp_22.error" class="ml-1 text-xs text-gray-500">{{ result.tcp_22.error }}</span>
                      <span v-else class="ml-1 text-xs text-gray-400">No data</span>
                    </div>
                    <!-- TCP 443 -->
                    <div class="flex items-center">
                      <span v-if="result.tcp_443 && result.tcp_443.success" class="text-green-600 mr-1" title="TCP 443 Success">
                        <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                      </span>
                      <span v-else class="text-red-600 mr-1" title="TCP 443 Failed">
                        <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                      </span>
                      <span class="font-semibold">TCP 443:</span>
                      <span v-if="result.tcp_443 && result.tcp_443.success" class="ml-1">Open</span>
                      <span v-else-if="result.tcp_443 && result.tcp_443.error" class="ml-1 text-xs text-gray-500">{{ result.tcp_443.error }}</span>
                      <span v-else class="ml-1 text-xs text-gray-400">No data</span>
                    </div>
                    <!-- General Errors -->
                    <div v-if="result.errors && result.errors.length" class="flex items-center mt-1">
                      <span class="text-red-500 mr-1">
                        <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                      </span>
                      <span class="text-xs text-red-500">{{ result.errors.join('; ') }}</span>
                    </div>
                  </div>
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
                  <template v-if="job && jobTypeRegistry[job.job_type] && jobTypeRegistry[job.job_type].logComponents">
                    <button v-if="jobTypeRegistry[job.job_type].logComponents.job" @click="openJobLogModal(result)" class="text-indigo-600 hover:text-indigo-900 cursor-pointer mr-2" title="View Job Log">
                      <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2a4 4 0 014-4h2a4 4 0 014 4v2" /></svg>
                      Job Log
                    </button>
                    <button v-if="jobTypeRegistry[job.job_type].logComponents.connection" @click="openConnLogModal(result)" class="text-green-600 hover:text-green-900 cursor-pointer" title="View Connection Log">
                      <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V4a2 2 0 10-4 0v1.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5" /></svg>
                      Conn Log
                    </button>
                  </template>
                  <template v-else>
                    <a v-if="result.has_log" @click="viewDeviceLog(result)" class="text-indigo-600 hover:text-indigo-900 cursor-pointer">View Log</a>
                  </template>
                </td>
              </tr>
            </tbody>
          </table>
          <!-- Default Table for Other Job Types -->
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
                  <template v-if="job && jobTypeRegistry[job.job_type] && jobTypeRegistry[job.job_type].logComponents">
                    <button v-if="jobTypeRegistry[job.job_type].logComponents.job" @click="openJobLogModal(result)" class="text-indigo-600 hover:text-indigo-900 cursor-pointer mr-2" title="View Job Log">
                      <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2a4 4 0 014-4h2a4 4 0 014 4v2" /></svg>
                      Job Log
                    </button>
                    <button v-if="jobTypeRegistry[job.job_type].logComponents.connection" @click="openConnLogModal(result)" class="text-green-600 hover:text-green-900 cursor-pointer" title="View Connection Log">
                      <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V4a2 2 0 10-4 0v1.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5" /></svg>
                      Conn Log
                    </button>
                  </template>
                  <template v-else>
                    <a v-if="result.has_log" @click="viewDeviceLog(result)" class="text-indigo-600 hover:text-indigo-900 cursor-pointer">View Log</a>
                  </template>
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

    <!-- Job Log Modal -->
    <BaseModal :is-open="isJobLogModalOpen" :title="`Job Log: ${logModalDevice ? logModalDevice.device_name || `Device #${logModalDevice.device_id}` : ''}`" @close="closeJobLogModal">
      <template #content>
        <JobLogTable v-if="isJobLogModalOpen && logModalDevice" :job-id="jobId" :device-id="logModalDevice.device_id" />
      </template>
    </BaseModal>
    <!-- Connection Log Modal -->
    <BaseModal :is-open="isConnLogModalOpen" :title="`Connection Log: ${logModalDevice ? logModalDevice.device_name || `Device #${logModalDevice.device_id}` : ''}`" @close="closeConnLogModal">
      <template #content>
        <ConnectionLogTable v-if="isConnLogModalOpen && logModalDevice" :job-id="jobId" :device-id="logModalDevice.device_id" />
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
import api from '../services/api';
import JobLogTable from './JobLogTable.vue'
import ConnectionLogTable from './ConnectionLogTable.vue'
import { jobTypeRegistry } from '../jobTypeRegistry'

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
const isJobLogModalOpen = ref(false)
const isConnLogModalOpen = ref(false)
const logModalDevice = ref(null)

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
    // Fetch job details using the shared API service
    const jobResponse = await api.get(`/jobs/${props.jobId}`);
    job.value = jobResponse.data;
    
    // Fetch device results for this job
    const deviceResponse = await api.get(`/jobs/${props.jobId}/devices`);
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
  logModalDevice.value = device
  isJobLogModalOpen.value = true
}

function openJobLogModal(device) {
  logModalDevice.value = device
  isJobLogModalOpen.value = true
}

function openConnLogModal(device) {
  logModalDevice.value = device
  isConnLogModalOpen.value = true
}

function closeJobLogModal() {
  isJobLogModalOpen.value = false
  logModalDevice.value = null
}

function closeConnLogModal() {
  isConnLogModalOpen.value = false
  logModalDevice.value = null
}

async function retryFailedDevices() {
  try {
    await api.post(`/jobs/${props.jobId}/retry-failed`);
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