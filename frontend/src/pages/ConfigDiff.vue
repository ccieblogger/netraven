<template>
  <div class="p-4 bg-main min-h-screen">
    <h1 class="text-2xl font-semibold mb-4 text-text-primary">Configuration Diff Viewer</h1>

    <!-- Selection Controls -->
    <div class="nr-card bg-card border border-divider shadow rounded p-4 mb-6">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Device Selection -->
        <div>
          <label for="device-select" class="block text-sm font-medium text-text-secondary mb-1">Device</label>
          <select 
            id="device-select" 
            v-model="selectedDeviceId" 
            class="w-full rounded-md border border-divider bg-input text-text-primary shadow-sm focus:border-primary focus:ring-primary"
            :disabled="isLoading"
          >
            <option value="" disabled>Select a device...</option>
            <option v-for="device in devices" :key="device.id" :value="device.id">
              {{ device.hostname }} ({{ device.ip_address }})
            </option>
          </select>
        </div>
      </div>

      <div class="my-4 border-t border-divider"></div>

      <div v-if="selectedDeviceId" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Version A (Old) Selection -->
        <div>
          <label for="version-a" class="block text-sm font-medium text-text-secondary mb-1">Version A (Old)</label>
          <select 
            id="version-a" 
            v-model="selectedVersionA" 
            class="w-full rounded-md border border-divider bg-input text-text-primary shadow-sm focus:border-primary focus:ring-primary"
            :disabled="isLoading || !configVersions.length"
          >
            <option value="" disabled>Select old version...</option>
            <option v-for="version in configVersions" :key="version.id" :value="version.id">
              {{ formatDate(version) }} 
              {{ version.job_id ? `(Job #${version.job_id})` : '' }}
            </option>
          </select>
        </div>

        <!-- Version B (New) Selection -->
        <div>
          <label for="version-b" class="block text-sm font-medium text-text-secondary mb-1">Version B (New)</label>
          <select 
            id="version-b" 
            v-model="selectedVersionB" 
            class="w-full rounded-md border border-divider bg-input text-text-primary shadow-sm focus:border-primary focus:ring-primary"
            :disabled="isLoading || !configVersions.length"
          >
            <option value="" disabled>Select new version...</option>
            <option v-for="version in configVersions" :key="version.id" :value="version.id">
              {{ formatDate(version) }} 
              {{ version.job_id ? `(Job #${version.job_id})` : '' }}
            </option>
          </select>
        </div>
      </div>

      <!-- Compare Button -->
      <div class="mt-4 text-right">
        <button 
          @click="loadDiff" 
          class="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50"
          :disabled="isLoading || !canCompare"
        >
          <span v-if="isLoading">Loading...</span>
          <span v-else>Compare Versions</span>
        </button>
      </div>
    </div>

    <!-- Diff Summary -->
    <div class="bg-card border border-divider rounded p-4 mb-4 text-text-primary">
      <slot name="diff-summary">
        <div class="font-semibold text-lg mb-2">Configuration Diff</div>
        <div class="text-text-secondary">
          {{ versionADetails ? formatDate(versionADetails) : 'Unknown' }} ({{ versionADetails?.job_id || 'Unknown' }}) →
          {{ versionBDetails ? formatDate(versionBDetails) : 'Unknown' }} ({{ versionBDetails?.job_id || 'Unknown' }})
        </div>
      </slot>
    </div>

    <!-- Diff Viewer -->
    <div v-if="diffError" class="bg-error/10 border-l-4 border-error text-error p-4 mb-6 rounded-md">
      <p>{{ diffError }}</p>
    </div>

    <div class="bg-card border border-divider rounded p-4 mb-6">
      <DiffViewer
        :old-content="configA"
        :new-content="configB"
        :old-version="versionADetails"
        :new-version="versionBDetails"
        :is-loading="isLoadingDiff"
        :error="diffError"
        class="diff-viewer-panel"
      />
    </div>

    <div v-if="!selectedDeviceId" class="bg-card p-6 rounded-md text-center text-text-secondary border border-divider">
      <p>Select a device and versions to compare configurations</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import DiffViewer from '../components/DiffViewer.vue';
import { useDeviceStore } from '../store/device';
import { useNotificationStore } from '../store/notifications';
import axios from 'axios';

// Stores
const deviceStore = useDeviceStore();
const notificationStore = useNotificationStore();
const route = useRoute();
const router = useRouter();

// State
const selectedDeviceId = ref('');
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
const canCompare = computed(() => 
  selectedDeviceId.value && 
  selectedVersionA.value && 
  selectedVersionB.value
);

// Format date for display
function formatDate(version) {
  // Accepts a config version object or timestamp string
  if (!version) return 'Unknown';
  // If passed a string, treat as timestamp
  if (typeof version === 'string') {
    return new Date(version).toLocaleString();
  }
  // Try 'timestamp', then 'retrieved_at', then fallback
  const ts = version.timestamp || version.retrieved_at || null;
  if (!ts) return 'Unknown';
  return new Date(ts).toLocaleString();
}

// Fetch device configurations
async function fetchDeviceConfigurations() {
  if (!selectedDeviceId.value) return;
  isLoading.value = true;
  configVersions.value = [];
  diffError.value = '';
  try {
    // Correct API call to fetch configuration history for a device
    const response = await axios.get(`/api/configs/${selectedDeviceId.value}/history`);
    // Ensure response is an array before sorting
    const configs = Array.isArray(response.data) ? response.data : [];
    configVersions.value = configs.sort((a, b) => 
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
    const responseA = await axios.get(`/api/configs/${selectedVersionA.value}`);
    configA.value = responseA.data.config_data;
    // Fetch version B (new)
    const responseB = await axios.get(`/api/configs/${selectedVersionB.value}`);
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

// On mount: check for route query params and auto-load diff if present
onMounted(async () => {
  if (devices.value.length === 0) {
    await deviceStore.fetchDevices();
  }
  // Always allow manual selection: if a device is already selected (from query or user), fetch its configs
  const { deviceId, v1, v2 } = route.query;
  if (deviceId) {
    selectedDeviceId.value = deviceId;
    await fetchDeviceConfigurations();
  }
  // If both versions are present, auto-select and load diff
  if (deviceId && v1 && v2) {
    selectedVersionA.value = v1;
    selectedVersionB.value = v2;
    await loadDiff();
  }
});
</script>

<style scoped>
/* Theme-aligned diff panel styles for readability */
.diff-viewer-panel, .diff-viewer, .diff, pre {
  background: var(--color-bg-card, #181f2a) !important;
  color: var(--color-text-primary, #e5e7eb) !important;
  font-size: 1rem;
  border-radius: 0.5rem;
  padding: 1rem;
  overflow-x: auto;
}

/* Ensure added/removed lines in diff are readable */
.diff-viewer-panel .diff-add {
  background: #193a1a !important;
  color: #b6fcb6 !important;
}
.diff-viewer-panel .diff-remove {
  background: #3a1a1a !important;
  color: #fcb6b6 !important;
}

/* General card and border alignment */
.bg-card {
  background: var(--color-bg-card, #181f2a) !important;
}
.text-text-primary {
  color: var(--color-text-primary, #e5e7eb) !important;
}
.text-text-secondary {
  color: var(--color-text-secondary, #a0aec0) !important;
}
.border-divider {
  border-color: var(--color-border-divider, #293042) !important;
}
</style>