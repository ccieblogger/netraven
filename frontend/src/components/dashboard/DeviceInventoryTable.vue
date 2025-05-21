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
          <th class="py-2 px-4 text-left">Model</th>
          <th class="py-2 px-4 text-left">Type</th>
          <th class="py-2 px-4 text-left">Source</th>
          <th class="py-2 px-4 text-left">Reachable</th>
          <th class="py-2 px-4 text-left cursor-pointer select-none" @click="changeSort('last_backup')">
            Last Backup
            <span v-if="sortField === 'last_backup'">{{ sortOrder === 1 ? '▲' : '▼' }}</span>
          </th>
          <th class="py-2 px-4 text-left">Tags</th>
          <th class="py-2 px-4 text-left">Credential</th>
          <th class="py-2 px-4 text-left">Notes</th>
          <th class="py-2 px-4 text-left">Last Updated</th>
          <th class="py-2 px-4 text-left">Updated By</th>
          <th class="py-2 px-4 text-left">Actions</th>
          <th class="py-2 px-4 text-left">Other</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="device in devices" :key="device.id" class="border-b text-text-primary">
          <td class="py-2 px-4">
            <router-link :to="`/devices/${device.id}`" class="text-blue-600 hover:underline">
              {{ device.hostname }}
            </router-link>
          </td>
          <td class="py-2 px-4">{{ device.ip_address }}</td>
          <td class="py-2 px-4">{{ device.serial_number }}</td>
          <td class="py-2 px-4">{{ device.model }}</td>
          <td class="py-2 px-4">{{ device.device_type }}</td>
          <td class="py-2 px-4">{{ device.source }}</td>
          <td class="py-2 px-4">
            <StatusIcon :status="mapReachabilityStatus(device.last_reachability_status)" :tooltip="reachabilityTooltip(device)" />
          </td>
          <td class="py-2 px-4">{{ formatDate(device.last_backup) }}</td>
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
          <td class="py-2 px-4 max-w-xs">
            <span v-if="device.notes" class="block truncate cursor-pointer" @mouseenter="showNotes = device.id" @mouseleave="showNotes = null">
              {{ notesSnippet(device.notes) }}
              <div v-if="showNotes === device.id" class="absolute z-50 bg-white border border-gray-300 rounded shadow-lg p-3 max-w-md max-h-60 overflow-auto mt-2" style="min-width: 250px;">
                <MarkdownRenderer :content="device.notes" />
              </div>
            </span>
            <span v-else class="text-text-secondary">-</span>
          </td>
          <td class="py-2 px-4">{{ formatDate(device.last_updated) }}</td>
          <td class="py-2 px-4">{{ device.updated_by || '-' }}</td>
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
            </div>
          </td>
        </tr>
        <tr v-if="!loading && devices.length === 0">
          <td :colspan="15" class="text-center text-text-secondary py-4">No devices found.</td>
        </tr>
        <tr v-if="loading">
          <td :colspan="15" class="text-center text-text-secondary py-4">Loading devices...</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import StatusIcon from '../ui/StatusIcon.vue';
import { ref } from 'vue';
import MarkdownRenderer from '../ui/MarkdownRenderer.vue';
const props = defineProps({
  devices: { type: Array, required: true },
  loading: { type: Boolean, default: false },
  sortField: { type: String, default: '' },
  sortOrder: { type: Number, default: 1 }
});
const emit = defineEmits(['edit', 'delete', 'check-reachability', 'credential-check', 'view-configs', 'sort']);
const showNotes = ref(null);
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
function changeSort(field) {
  let order = 1;
  if (props.sortField === field) {
    order = -props.sortOrder;
  }
  emit('sort', { field, order });
}
function formatDate(dateStr) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  if (isNaN(d)) return '-';
  return d.toLocaleString();
}
function notesSnippet(notes) {
  if (!notes) return '';
  if (notes.length < 40) return notes;
  return notes.slice(0, 40) + '...';
}
</script>