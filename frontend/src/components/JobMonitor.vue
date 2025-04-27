<template>
  <div class="job-monitor space-y-8">
    <!-- Job Overview Card -->
    <div class="bg-card shadow-lg rounded-xl p-8 flex flex-col md:flex-row md:justify-between md:items-center">
      <div>
        <div class="flex items-center space-x-4 mb-3">
          <h2 class="text-3xl font-bold text-on-card">{{ job ? job.name : 'Loading...' }}</h2>
          <span class="text-lg font-normal text-on-card/60">#{{ jobId }}</span>
          <span v-if="job" :class="['inline-flex items-center px-4 py-1 rounded-full text-base font-semibold', statusBadgeClass]">
            <svg v-if="statusIcon" :class="['h-6 w-6 mr-2', statusIconColor]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path :d="statusIcon" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
            </svg>
            {{ statusText }}
          </span>
        </div>
        <div v-if="lastCheckedDisplay" class="text-sm text-on-card/60 mb-2">{{ lastCheckedDisplay }}</div>
        <div class="text-on-card/80 mb-2 text-lg" v-if="job && job.description">{{ job.description }}</div>
        <div class="flex space-x-4 mt-2">
          <button 
            v-if="canRefresh" 
            @click="fetchJobStatus"
            class="px-5 py-2 bg-primary text-on-primary rounded-lg hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 text-base shadow"
            :disabled="isLoading"
            title="Refresh job status"
          >
            <span v-if="isLoading">Refreshing...</span>
            <span v-else>Refresh</span>
          </button>
          <button 
            v-if="canRetry" 
            @click="retryFailedDevices"
            class="px-5 py-2 bg-warning text-on-warning rounded-lg hover:bg-warning-dark focus:outline-none focus:ring-2 focus:ring-warning focus:ring-offset-2 text-base shadow"
          >
            Retry Failed Devices
          </button>
        </div>
      </div>
      <div class="flex flex-col items-end mt-8 md:mt-0">
        <div v-if="deviceResults.length > 0" class="flex flex-col items-end">
          <span class="text-sm text-on-card/60 mb-1">Percent Complete</span>
          <span class="text-4xl font-bold text-primary">{{ percentComplete }}%</span>
          <div class="w-48 bg-on-card/10 rounded-full h-3 mt-2">
            <div class="bg-primary h-3 rounded-full" :style="{ width: `${percentComplete}%` }"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Live Log Stream Card -->
    <div class="bg-card shadow-lg rounded-xl p-8 mt-8">
      <h3 class="text-2xl font-semibold mb-4 flex items-center text-on-card">
        <svg class="h-7 w-7 mr-3 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V4a2 2 0 10-4 0v1.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5"/></svg>
        Live Log Stream
      </h3>
      <LiveLog :job-id="jobId" />
    </div>

    <!-- Execution Times Card -->
    <div class="bg-card shadow-lg rounded-xl p-8">
      <h3 class="text-2xl font-semibold mb-6 flex items-center text-on-card">
        <svg class="h-7 w-7 mr-3 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
        Execution Times
      </h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="flex items-center space-x-4 bg-on-card/5 p-5 rounded-xl border border-on-card/10" title="The time this job is scheduled to run (if applicable)">
          <svg class="h-7 w-7 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3"/></svg>
          <div>
            <div class="text-sm text-on-card/60 mb-1">Scheduled Time</div>
            <div class="font-medium text-lg text-on-card">{{ formatDateTime(job?.scheduled_for) || 'Not Scheduled' }}</div>
          </div>
        </div>
        <div class="flex items-center space-x-4 bg-on-card/5 p-5 rounded-xl border border-on-card/10" title="The time this job started running">
          <svg class="h-7 w-7 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10"/></svg>
          <div>
            <div class="text-sm text-on-card/60 mb-1">Start Time</div>
            <div class="font-medium text-lg text-on-card">{{ formatDateTime(job?.started_at) || 'Not Started' }}</div>
          </div>
        </div>
        <div class="flex items-center space-x-4 bg-on-card/5 p-5 rounded-xl border border-on-card/10" title="The time this job finished running">
          <svg class="h-7 w-7 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
          <div>
            <div class="text-sm text-on-card/60 mb-1">End Time</div>
            <div class="font-medium text-lg text-on-card">{{ formatDateTime(job?.completed_at) || 'Not Completed' }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Device Results Card -->
    <div class="bg-card shadow-lg rounded-xl p-8">
      <h3 class="text-2xl font-semibold mb-6 flex items-center text-on-card">
        <svg class="h-7 w-7 mr-3 text-info" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2a4 4 0 014-4h2a4 4 0 014 4v2"/></svg>
        Device Results
      </h3>
      <div v-if="deviceResults.length === 0" class="flex flex-col items-center justify-center py-16">
        <svg class="h-16 w-16 text-on-card/10 mb-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2a4 4 0 014-4h2a4 4 0 014 4v2"/></svg>
        <p class="text-on-card/70 text-xl font-medium">No device results available</p>
        <p class="text-on-card/50 text-base">The job may not have started or completed yet.</p>
      </div>
      <div v-else>
        <div class="flex flex-wrap gap-6 mb-6">
          <div class="bg-info/10 text-info px-6 py-3 rounded-xl font-semibold flex items-center text-lg">
            <svg class="h-6 w-6 mr-3 text-info" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2a4 4 0 014-4h2a4 4 0 014 4v2"/></svg>
            {{ deviceResults.length }} Devices
          </div>
          <div class="bg-success/10 text-success px-6 py-3 rounded-xl font-semibold flex items-center text-lg">
            <svg class="h-6 w-6 mr-3 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            {{ completedCount }} Completed
          </div>
          <div class="bg-error/10 text-error px-6 py-3 rounded-xl font-semibold flex items-center text-lg">
            <svg class="h-6 w-6 mr-3 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            {{ failedCount }} Failed
          </div>
        </div>
        <!-- Device Results Table -->
        <table v-if="job && job.job_type === 'reachability'" class="min-w-full divide-y divide-on-card/10 mt-6">
          <thead class="bg-on-card/5">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-on-card/500 uppercase tracking-wider">Device</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-on-card/500 uppercase tracking-wider">Reachability Results</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-on-card/500 uppercase tracking-wider">Status</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-on-card/500 uppercase tracking-wider">Started</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-on-card/500 uppercase tracking-wider">Completed</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-on-card/500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody class="bg-on-card divide-y divide-on-card/10">
            <tr v-for="result in deviceResults" :key="result.device_id">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="font-medium text-on-card/900">{{ result.device_name || `Device #${result.device_id}` }}</div>
                <div class="text-xs text-on-card/500">{{ result.device_ip || '' }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex flex-col space-y-1">
                  <!-- ICMP Ping -->
                  <div class="flex items-center">
                    <span v-if="result.icmp_ping && result.icmp_ping.success" class="text-success-600 mr-1" title="Ping Success">
                      <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                    </span>
                    <span v-else class="text-error-600 mr-1" title="Ping Failed">
                      <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                    </span>
                    <span class="font-semibold">ICMP:</span>
                    <span v-if="result.icmp_ping && result.icmp_ping.success" class="ml-1">{{ result.icmp_ping.latency }} ms</span>
                    <span v-else-if="result.icmp_ping && result.icmp_ping.error" class="ml-1 text-xs text-on-card/500">{{ result.icmp_ping.error }}</span>
                    <span v-else class="ml-1 text-xs text-on-card/400">No data</span>
                  </div>
                  <!-- TCP 22 -->
                  <div class="flex items-center">
                    <span v-if="result.tcp_22 && result.tcp_22.success" class="text-success-600 mr-1" title="TCP 22 Success">
                      <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                    </span>
                    <span v-else class="text-error-600 mr-1" title="TCP 22 Failed">
                      <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                    </span>
                    <span class="font-semibold">TCP 22:</span>
                    <span v-if="result.tcp_22 && result.tcp_22.success" class="ml-1">Open</span>
                    <span v-else-if="result.tcp_22 && result.tcp_22.error" class="ml-1 text-xs text-on-card/500">{{ result.tcp_22.error }}</span>
                    <span v-else class="ml-1 text-xs text-on-card/400">No data</span>
                  </div>
                  <!-- TCP 443 -->
                  <div class="flex items-center">
                    <span v-if="result.tcp_443 && result.tcp_443.success" class="text-success-600 mr-1" title="TCP 443 Success">
                      <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                    </span>
                    <span v-else class="text-error-600 mr-1" title="TCP 443 Failed">
                      <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                    </span>
                    <span class="font-semibold">TCP 443:</span>
                    <span v-if="result.tcp_443 && result.tcp_443.success" class="ml-1">Open</span>
                    <span v-else-if="result.tcp_443 && result.tcp_443.error" class="ml-1 text-xs text-on-card/500">{{ result.tcp_443.error }}</span>
                    <span v-else class="ml-1 text-xs text-on-card/400">No data</span>
                  </div>
                  <!-- General Errors -->
                  <div v-if="result.errors && result.errors.length" class="flex items-center mt-1">
                    <span class="text-error-500 mr-1">
                      <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                    </span>
                    <span class="text-xs text-error-500">{{ result.errors.join('; ') }}</span>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="getStatusBadgeClass(result.status)" class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full">
                  {{ result.status }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-on-card/500">
                {{ formatDateTime(result.started_at) || 'Pending' }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-on-card/500">
                {{ formatDateTime(result.completed_at) || '-' }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <template v-if="job && jobTypeRegistry[job.job_type] && jobTypeRegistry[job.job_type].logComponents">
                  <button v-if="jobTypeRegistry[job.job_type].logComponents.job" @click="openJobLogModal(result)" class="text-info-600 hover:text-info-900 cursor-pointer mr-2" title="View Job Log">
                    <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2a4 4 0 014-4h2a4 4 0 014 4v2" /></svg>
                    Job Log
                  </button>
                  <button v-if="jobTypeRegistry[job.job_type].logComponents.connection" @click="openConnLogModal(result)" class="text-success-600 hover:text-success-900 cursor-pointer" title="View Connection Log">
                    <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V4a2 2 0 10-4 0v1.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5" /></svg>
                    Conn Log
                  </button>
                </template>
                <template v-else>
                  <a v-if="result.has_log" @click="viewDeviceLog(result)" class="text-info-600 hover:text-info-900 cursor-pointer">View Log</a>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
        <!-- Default Table for Other Job Types -->
        <table v-else class="min-w-full divide-y divide-on-card/10 mt-6">
          <thead class="bg-on-card/5">
            <tr>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-on-card/500 uppercase tracking-wider">Device</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-on-card/500 uppercase tracking-wider">Status</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-on-card/500 uppercase tracking-wider">Started</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-on-card/500 uppercase tracking-wider">Completed</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-on-card/500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody class="bg-on-card divide-y divide-on-card/10">
            <tr v-for="result in deviceResults" :key="result.device_id">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="font-medium text-on-card/900">{{ result.device_name || `Device #${result.device_id}` }}</div>
                <div class="text-xs text-on-card/500">{{ result.device_ip || '' }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="getStatusBadgeClass(result.status)" class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full">
                  {{ result.status }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-on-card/500">
                {{ formatDateTime(result.started_at) || 'Pending' }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-on-card/500">
                {{ formatDateTime(result.completed_at) || '-' }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <template v-if="job && jobTypeRegistry[job.job_type] && jobTypeRegistry[job.job_type].logComponents">
                  <button v-if="jobTypeRegistry[job.job_type].logComponents.job" @click="openJobLogModal(result)" class="text-info-600 hover:text-info-900 cursor-pointer mr-2" title="View Job Log">
                    <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2a4 4 0 014-4h2a4 4 0 014 4v2" /></svg>
                    Job Log
                  </button>
                  <button v-if="jobTypeRegistry[job.job_type].logComponents.connection" @click="openConnLogModal(result)" class="text-success-600 hover:text-success-900 cursor-pointer" title="View Connection Log">
                    <svg class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V4a2 2 0 10-4 0v1.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5" /></svg>
                    Conn Log
                  </button>
                </template>
                <template v-else>
                  <a v-if="result.has_log" @click="viewDeviceLog(result)" class="text-info-600 hover:text-info-900 cursor-pointer">View Log</a>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
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
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import LiveLog from './LiveLog.vue'
dayjs.extend(relativeTime);

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
const lastChecked = ref(null);
const lastCheckedTimer = ref(null);
const lastCheckedDisplay = ref('');

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

const percentComplete = computed(() => {
  if (deviceResults.value.length === 0) return 0;
  return Math.round((completedCount.value / deviceResults.value.length) * 100);
});

const failedCount = computed(() => {
  return deviceResults.value.filter(device => device.status === 'FAILED').length;
});

const statusBadgeClass = computed(() => {
  if (!job.value) return '';
  switch (job.value.status) {
    case 'COMPLETED_SUCCESS': return 'bg-success/10 text-success';
    case 'RUNNING': return 'bg-primary/10 text-primary';
    case 'PENDING': return 'bg-warning/10 text-warning';
    case 'COMPLETED_PARTIAL_FAILURE': return 'bg-orange-100 text-orange-800';
    case 'COMPLETED_FAILURE':
    case 'FAILED_UNEXPECTED':
    case 'FAILED_DISPATCHER_ERROR':
    case 'FAILED_CREDENTIAL_RESOLUTION':
      return 'bg-error/10 text-error';
    case 'COMPLETED_NO_DEVICES':
      return 'bg-on-card/10 text-on-card/80';
    case 'COMPLETED_NO_CREDENTIALS':
      return 'bg-warning/10 text-warning';
    default:
      return 'bg-on-card/10 text-on-card/80';
  }
});

const statusIcon = computed(() => {
  if (!job.value) return '';
  switch (job.value.status) {
    case 'COMPLETED_SUCCESS':
      return 'M5 13l4 4L19 7'; // checkmark
    case 'RUNNING':
      return 'M12 8v4l3 3'; // clock
    case 'PENDING':
      return 'M8 7V3m8 4V3m-9 8h10'; // clock
    case 'COMPLETED_FAILURE':
    case 'FAILED_UNEXPECTED':
    case 'FAILED_DISPATCHER_ERROR':
    case 'FAILED_CREDENTIAL_RESOLUTION':
      return 'M6 18L18 6M6 6l12 12'; // X
    default:
      return '';
  }
});

const statusIconColor = computed(() => {
  if (!job.value) return '';
  switch (job.value.status) {
    case 'COMPLETED_SUCCESS': return 'text-success';
    case 'RUNNING': return 'text-primary';
    case 'PENDING': return 'text-warning';
    case 'COMPLETED_PARTIAL_FAILURE': return 'text-orange-800';
    case 'COMPLETED_FAILURE':
    case 'FAILED_UNEXPECTED':
    case 'FAILED_DISPATCHER_ERROR':
    case 'FAILED_CREDENTIAL_RESOLUTION':
      return 'text-error';
    case 'COMPLETED_NO_DEVICES':
      return 'text-on-card/80';
    case 'COMPLETED_NO_CREDENTIALS':
      return 'text-warning';
    default:
      return 'text-on-card/80';
  }
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

function updateLastCheckedDisplay() {
  if (lastChecked.value) {
    lastCheckedDisplay.value = `Last checked: ${dayjs(lastChecked.value).fromNow()}`;
  } else {
    lastCheckedDisplay.value = '';
  }
}

async function fetchJobStatus() {
  isLoading.value = true;
  error.value = null;
  try {
    const jobResponse = await api.get(`/jobs/${props.jobId}`);
    job.value = jobResponse.data;
    const deviceResponse = await api.get(`/jobs/${props.jobId}/devices`);
    deviceResults.value = deviceResponse.data;
    lastChecked.value = new Date();
    updateLastCheckedDisplay();
    if (job.value.status === 'COMPLETED' || job.value.status === 'FAILED') {
      if (refreshTimer.value) {
        clearInterval(refreshTimer.value);
        refreshTimer.value = null;
      }
    }
  } catch (err) {
    if (err.response && err.response.status === 401) {
      error.value = 'Session expired. Please log in again.';
    } else if (err.request && !err.response) {
      error.value = 'Network error: Unable to reach the server.';
    } else {
      error.value = err.response?.data?.detail || 'Failed to load job status';
    }
    notificationStore.error(error.value);
  } finally {
    isLoading.value = false;
  }
}

function setupAutoRefresh() {
  if (lastCheckedTimer.value) {
    clearInterval(lastCheckedTimer.value);
  }
  lastCheckedTimer.value = setInterval(() => {
    updateLastCheckedDisplay();
  }, 1000);

  if (props.autoRefresh) {
    if (refreshTimer.value) {
      clearInterval(refreshTimer.value);
    }
    refreshTimer.value = setInterval(() => {
      if (canRefresh.value) {
        fetchJobStatus();
      } else {
        clearInterval(refreshTimer.value);
        refreshTimer.value = null;
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
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value);
    refreshTimer.value = null;
  }
  if (lastCheckedTimer.value) {
    clearInterval(lastCheckedTimer.value);
    lastCheckedTimer.value = null;
  }
});

// Watch for job ID changes
watch(() => props.jobId, () => {
  fetchJobStatus();
  setupAutoRefresh();
});
</script> 