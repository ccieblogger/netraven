<template>
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-semibold mb-4">Device Details</h1>
    <div v-if="device" class="space-y-6">
      <!-- Device Info Card -->
      <div class="bg-white shadow-md rounded p-6 flex flex-col md:flex-row md:justify-between md:items-center gap-4">
        <div>
          <div class="flex items-center gap-3 mb-2">
            <span class="text-xl font-bold">{{ device.hostname }}</span>
            <StatusIcon :status="mapReachabilityStatus(device.last_reachability_status)" :tooltip="reachabilityTooltip(device)" />
          </div>
          <div class="text-gray-600">Model: <span class="font-medium">{{ device.model || '-' }}</span></div>
          <div class="text-gray-600">Serial #: <span class="font-medium">{{ device.serial_number || '-' }}</span></div>
          <div class="text-gray-600">Source: <span class="font-medium">{{ device.source || '-' }}</span></div>
          <div class="text-gray-600">Last Updated: <span class="font-medium">{{ formatDate(device.last_updated) }}</span></div>
          <div class="text-gray-600">Updated By: <span class="font-medium">{{ device.updated_by || '-' }}</span></div>
        </div>
      </div>
      <!-- Notes Card -->
      <div class="bg-white shadow-md rounded p-6">
        <div class="font-semibold mb-2">Notes</div>
        <div class="max-h-60 overflow-auto border rounded p-3 bg-gray-50">
          <MarkdownRenderer :content="device.notes || 'No notes.'" />
        </div>
      </div>
      <!-- Job Metrics Card (placeholder) -->
      <div class="bg-white shadow-md rounded p-6">
        <div class="font-semibold mb-2">Background Job Metrics</div>
        <div class="flex gap-6">
          <div class="text-center">
            <div class="text-2xl font-bold">{{ jobSummary.total }}</div>
            <div class="text-xs text-gray-500">Total Jobs</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-green-600">{{ jobSummary.succeeded }}</div>
            <div class="text-xs text-gray-500">Succeeded</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-red-600">{{ jobSummary.failed }}</div>
            <div class="text-xs text-gray-500">Failed</div>
          </div>
        </div>
      </div>
      <!-- Job Results Table -->
      <div class="bg-white shadow-md rounded p-6">
        <div class="font-semibold mb-2">Job Results</div>
        <div class="overflow-x-auto">
          <table class="min-w-full table-auto text-sm">
            <thead>
              <tr class="bg-gray-100">
                <th class="py-2 px-4 text-left">Job ID</th>
                <th class="py-2 px-4 text-left">Status</th>
                <th class="py-2 px-4 text-left">Start Time</th>
                <th class="py-2 px-4 text-left">End Time</th>
                <th class="py-2 px-4 text-left">Type</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="job in deviceJobs" :key="job.id">
                <td class="py-2 px-4">{{ job.id }}</td>
                <td class="py-2 px-4">{{ job.status }}</td>
                <td class="py-2 px-4">{{ formatDate(job.start_time) }}</td>
                <td class="py-2 px-4">{{ formatDate(job.end_time) }}</td>
                <td class="py-2 px-4">{{ job.job_type }}</td>
              </tr>
              <tr v-if="deviceJobs.length === 0">
                <td colspan="5" class="text-center text-gray-400 py-4">No job results found for this device.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div class="mt-6">
        <router-link to="/devices" class="text-blue-600 hover:underline">&larr; Back to Devices List</router-link>
      </div>
    </div>
    <div v-else class="text-center py-12 text-gray-500">Loading device details...</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useDeviceStore } from '../store/device';
import { useJobResultsStore } from '../store/job_results';
import StatusIcon from '../components/ui/StatusIcon.vue';
import MarkdownRenderer from '../components/ui/MarkdownRenderer.vue';

const route = useRoute();
const router = useRouter();
const deviceStore = useDeviceStore();
const jobResultsStore = useJobResultsStore();

const deviceId = route.params.id;
const device = ref(null);

const deviceJobs = computed(() => {
  return jobResultsStore.results.filter(j => String(j.device_id) === String(deviceId));
});
const jobSummary = computed(() => {
  const jobs = deviceJobs.value;
  return {
    total: jobs.length,
    succeeded: jobs.filter(j => j.status === 'completed' || j.status === 'success').length,
    failed: jobs.filter(j => j.status === 'failed' || j.status === 'error').length
  };
});

onMounted(async () => {
  if (!deviceStore.devices.length) {
    await deviceStore.fetchDevices();
  }
  device.value = deviceStore.devices.find(d => String(d.id) === String(deviceId));
  if (!jobResultsStore.results.length) {
    await jobResultsStore.fetchResults(1, { device_id: deviceId });
  }
});

function formatDate(dateStr) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  if (isNaN(d)) return '-';
  return d.toLocaleString();
}
function mapReachabilityStatus(status) {
  if (!status) return 'unknown';
  const normalized = String(status).toLowerCase();
  if ([ 'success', 'reachable', 'ok', 'online' ].includes(normalized)) return 'healthy';
  if ([ 'failure', 'unreachable', 'offline', 'error' ].includes(normalized)) return 'unhealthy';
  if ([ 'warning', 'partial' ].includes(normalized)) return 'warning';
  return 'unknown';
}
function reachabilityTooltip(device) {
  if (device.last_reachability_status === 'success') return 'Reachable';
  if (device.last_reachability_status === 'failure') return 'Unreachable';
  return 'Never Checked';
}
</script>