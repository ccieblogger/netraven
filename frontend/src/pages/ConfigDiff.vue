<template>
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-semibold mb-4">Configuration Diff Viewer</h1>

    <!-- Selection Controls -->
    <div class="bg-white p-4 mb-6 rounded-md shadow">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Device Selection -->
        <div>
          <label for="device-select" class="block text-sm font-medium text-gray-700 mb-1">Device</label>
          <select 
            id="device-select" 
            v-model="selectedDeviceId" 
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            :disabled="isLoading"
          >
            <option value="" disabled>Select a device...</option>
            <option v-for="device in devices" :key="device.id" :value="device.id">
              {{ device.hostname }} ({{ device.ip_address }})
            </option>
          </select>
        </div>

        <!-- Job Filter (Optional) -->
        <div>
          <label for="job-filter" class="block text-sm font-medium text-gray-700 mb-1">Filter by Job (Optional)</label>
          <select 
            id="job-filter" 
            v-model="jobFilter" 
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            :disabled="isLoading"
          >
            <option value="">All Jobs</option>
            <option v-for="job in jobs" :key="job.id" :value="job.id">
              Job #{{ job.id }} - {{ job.name }}
            </option>
          </select>
        </div>
      </div>

      <div class="my-4 border-t border-gray-200"></div>

      <div v-if="selectedDeviceId" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Version A (Old) Selection -->
        <div>
          <label for="version-a" class="block text-sm font-medium text-gray-700 mb-1">Version A (Old)</label>
          <select 
            id="version-a" 
            v-model="selectedVersionA" 
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            :disabled="isLoading || !configVersions.length"
          >
            <option value="" disabled>Select old version...</option>
            <option v-for="version in configVersions" :key="version.id" :value="version.id">
              {{ formatDate(version.timestamp) }} 
              {{ version.job_id ? `(Job #${version.job_id})` : '' }}
            </option>
          </select>
        </div>

        <!-- Version B (New) Selection -->
        <div>
          <label for="version-b" class="block text-sm font-medium text-gray-700 mb-1">Version B (New)</label>
          <select 
            id="version-b" 
            v-model="selectedVersionB" 
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            :disabled="isLoading || !configVersions.length"
          >
            <option value="" disabled>Select new version...</option>
            <option v-for="version in configVersions" :key="version.id" :value="version.id">
              {{ formatDate(version.timestamp) }} 
              {{ version.job_id ? `(Job #${version.job_id})` : '' }}
            </option>
          </select>
        </div>
      </div>

      <!-- Compare Button -->
      <div class="mt-4 text-right">
        <button 
          @click="loadDiff" 
          class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
          :disabled="isLoading || !canCompare"
        >
          <span v-if="isLoading">Loading...</span>
          <span v-else>Compare Versions</span>
        </button>
      </div>
    </div>

    <!-- Diff Viewer -->
    <div v-if="diffError" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded-md">
      <p>{{ diffError }}</p>
    </div>

    <DiffViewer
      :old-content="configA"
      :new-content="configB"
      :old-version="versionADetails"
      :new-version="versionBDetails"
      :is-loading="isLoadingDiff"
      :error="diffError"
    />

    <div v-if="!selectedDeviceId" class="bg-gray-100 p-6 rounded-md text-center text-gray-600">
      <p>Select a device and versions to compare configurations</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import DiffViewer from '../components/DiffViewer.vue';
import { useDeviceStore } from '../store/device';
import { useJobStore } from '../store/job';
import { useNotificationStore } from '../store/notifications';
import axios from 'axios';

// Stores
const deviceStore = useDeviceStore();
const jobStore = useJobStore();
const notificationStore = useNotificationStore();

// State
const selectedDeviceId = ref('');
const jobFilter = ref('');
const selectedVersionA = ref('');
const selectedVersionB = ref('');
const configVersions = ref([]);
const isLoading = ref(false);
const isLoadingDiff = ref(false);
const diffError = ref('');
const configA = ref('');
const configB = ref('');
const versionADetails = ref(null);
const versionBDetails = ref(null);

// Computed
const devices = computed(() => deviceStore.devices);
const jobs = computed(() => jobStore.jobs);
const canCompare = computed(() => 
  selectedDeviceId.value && 
  selectedVersionA.value && 
  selectedVersionB.value
);

// Format date for display
function formatDate(timestamp) {
  if (!timestamp) return 'Unknown';
  return new Date(timestamp).toLocaleString();
}

// Fetch device configurations
async function fetchDeviceConfigurations() {
  if (!selectedDeviceId.value) return;
  
  isLoading.value = true;
  configVersions.value = [];
  diffError.value = '';
  
  try {
    // API call to fetch configurations
    const response = await axios.get(`/api/devices/${selectedDeviceId.value}/configurations`, {
      params: { job_id: jobFilter.value || undefined }
    });
    
    // Sort by timestamp (newest first)
    configVersions.value = response.data.sort((a, b) => 
      new Date(b.timestamp) - new Date(a.timestamp)
    );
    
    // Auto-select newest and second newest if available
    if (configVersions.value.length >= 2) {
      selectedVersionB.value = configVersions.value[0].id; // Newest
      selectedVersionA.value = configVersions.value[1].id; // Second newest
    } else if (configVersions.value.length === 1) {
      selectedVersionB.value = configVersions.value[0].id;
      selectedVersionA.value = '';
    } else {
      selectedVersionA.value = '';
      selectedVersionB.value = '';
    }
  } catch (error) {
    console.error('Error fetching device configurations:', error);
    notificationStore.error('Failed to load device configurations.');
    diffError.value = 'Failed to load configuration versions.';
  } finally {
    isLoading.value = false;
  }
}

// Load diff between two versions
async function loadDiff() {
  if (!canCompare.value) return;
  
  isLoadingDiff.value = true;
  configA.value = '';
  configB.value = '';
  diffError.value = '';
  
  try {
    // Get the selected version objects
    versionADetails.value = configVersions.value.find(v => v.id === selectedVersionA.value);
    versionBDetails.value = configVersions.value.find(v => v.id === selectedVersionB.value);
    
    // Fetch version A (old)
    const responseA = await axios.get(`/api/devices/${selectedDeviceId.value}/configurations/${selectedVersionA.value}`);
    configA.value = responseA.data.config_data;
    
    // Fetch version B (new)
    const responseB = await axios.get(`/api/devices/${selectedDeviceId.value}/configurations/${selectedVersionB.value}`);
    configB.value = responseB.data.config_data;
  } catch (error) {
    console.error('Error loading configuration diff:', error);
    notificationStore.error('Failed to load configuration data.');
    diffError.value = 'Failed to load configuration content.';
  } finally {
    isLoadingDiff.value = false;
  }
}

// Watch for device selection changes
watch(selectedDeviceId, () => {
  fetchDeviceConfigurations();
});

// Watch for job filter changes
watch(jobFilter, () => {
  fetchDeviceConfigurations();
});

// Load devices on component mount
onMounted(async () => {
  if (devices.value.length === 0) {
    await deviceStore.fetchDevices();
  }
  
  if (jobs.value.length === 0) {
    await jobStore.fetchJobs();
  }
});
</script> 