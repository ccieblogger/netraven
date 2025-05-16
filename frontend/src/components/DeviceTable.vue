<template>
  <div class="nr-card overflow-x-auto">
    <table class="min-w-full table-auto">
      <thead>
        <tr class="bg-card text-text-secondary text-sm">
          <th class="py-2 px-4 text-left cursor-pointer select-none" @click="changeSort('hostname')">
            Hostname
            <span v-if="sortField === 'hostname'">{{ sortOrder === 1 ? '▲' : '▼' }}</span>
          </th>
          <th class="py-2 px-4 text-left cursor-pointer select-none" @click="changeSort('ip_address')">
            Host IP
            <span v-if="sortField === 'ip_address'">{{ sortOrder === 1 ? '▲' : '▼' }}</span>
          </th>
          <th class="py-2 px-4 text-left">Serial</th>
          <th class="py-2 px-4 text-left">Reachable</th>
          <th class="py-2 px-4 text-left">Tags</th>
          <th class="py-2 px-4 text-left">Credential</th>
          <th class="py-2 px-4 text-left">Actions</th>
          <th class="py-2 px-4 text-left">Other</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="device in sortedDevices" :key="device.id" class="border-b text-text-primary">
          <td class="py-2 px-4">{{ device.hostname }}</td>
          <td class="py-2 px-4">{{ device.ip_address }}</td>
          <td class="py-2 px-4">{{ device.serial }}</td>
          <td class="py-2 px-4">
            <StatusIcon :status="mapReachabilityStatus(device.last_reachability_status)" :tooltip="reachabilityTooltip(device)" />
          </td>
          <td class="py-2 px-4">
            <span v-for="tag in device.tags" :key="tag.id" class="bg-blue-900/30 text-blue-200 py-1 px-3 rounded-full text-xs mr-1">
              {{ tag.name }}
            </span>
          </td>
          <td class="py-2 px-4">
            <span v-if="device.matching_credentials_count > 0" class="text-blue-300 cursor-pointer hover:text-blue-100 underline">
              {{ device.matching_credentials_count }} credential(s)
            </span>
            <span v-else class="text-red-400 font-semibold">No credentials found.</span>
          </td>
          <td class="py-2 px-4">
            <div class="flex flex-row space-x-1">
              <button class="btn btn-xs btn-ghost" @click="$emit('edit', device)" title="Edit Device">
                <i class="pi pi-pencil"></i>
              </button>
              <button class="btn btn-xs btn-ghost text-red-500" @click="$emit('delete', device)" title="Delete Device">
                <i class="pi pi-trash"></i>
              </button>
            </div>
          </td>
          <td class="py-2 px-4">
            <div class="flex flex-row space-x-1">
              <button class="btn btn-xs btn-ghost" @click="$emit('check-reachability', device)" :disabled="device.status === 'offline'" title="Check Reachability">
                <i class="pi pi-check-circle"></i>
              </button>
              <button class="btn btn-xs btn-ghost" @click="$emit('credential-check', device)" title="Credential Check">
                <i class="pi pi-key"></i>
              </button>
              <button class="btn btn-xs btn-ghost" @click="$emit('view-configs', device)" title="View Configs">
                <i class="pi pi-eye"></i>
              </button>
              <button class="btn btn-xs btn-ghost" @click="$emit('timeline', device)" title="Timeline">
                <i class="pi pi-clock"></i>
              </button>
            </div>
          </td>
        </tr>
        <tr v-if="!loading && devices.length === 0">
          <td colspan="8" class="text-center text-text-secondary py-4">No devices found.</td>
        </tr>
        <tr v-if="loading">
          <td colspan="8" class="text-center text-text-secondary py-4">Loading devices...</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import StatusIcon from './ui/StatusIcon.vue';

const props = defineProps({
  devices: { type: Array, required: true },
  loading: { type: Boolean, default: false }
});
const sortField = ref('hostname');
const sortOrder = ref(1); // 1 = asc, -1 = desc
function changeSort(field) {
  if (sortField.value === field) {
    sortOrder.value = -sortOrder.value;
  } else {
    sortField.value = field;
    sortOrder.value = 1;
  }
}
const sortedDevices = computed(() => {
  const arr = [...props.devices];
  if (!sortField.value) return arr;
  return arr.sort((a, b) => {
    const aVal = a[sortField.value] || '';
    const bVal = b[sortField.value] || '';
    if (aVal < bVal) return -1 * sortOrder.value;
    if (aVal > bVal) return 1 * sortOrder.value;
    return 0;
  });
});
function reachabilityTooltip(device) {
  if (device.last_reachability_status === 'success') return 'Reachable';
  if (device.last_reachability_status === 'failure') return 'Unreachable';
  return 'Never Checked';
}
function mapReachabilityStatus(status) {
  if (!status) return 'unknown';
  const normalized = String(status).toLowerCase();
  if ([ 'success', 'reachable', 'ok', 'online' ].includes(normalized)) return 'healthy';
  if ([ 'failure', 'unreachable', 'offline', 'error' ].includes(normalized)) return 'unhealthy';
  if ([ 'warning', 'partial' ].includes(normalized)) return 'warning';
  return 'unknown';
}
</script>

<style scoped>
/* Add any table-specific styles here */
</style>