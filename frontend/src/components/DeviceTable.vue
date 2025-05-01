<template>
  <div>
    <!-- Filter/Search Bar (to be integrated) -->
    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-2 mb-4">
      <slot name="filters"></slot>
      <slot name="search"></slot>
    </div>

    <BaseTable
      :items="devices"
      :columns="columns"
      :loading="loading"
      :itemKey="'id'"
      @row-click="onRowClick"
    >
      <!-- Custom cell rendering for reachability -->
      <template #cell(reachability)="{ item }">
        <ServiceDot
          :status="item.last_reachability_status === 'success' ? 'healthy' : item.last_reachability_status === 'failure' ? 'unhealthy' : 'unknown'"
          :label="''"
          :tooltip="reachabilityTooltip(item)"
        />
      </template>
      <!-- Custom cell rendering for tags -->
      <template #cell(tags)="{ value }">
        <span v-for="tag in value" :key="tag.id" class="bg-blue-100 text-blue-600 py-1 px-3 rounded-full text-xs mr-1">
          {{ tag.name }}
        </span>
      </template>
      <!-- Custom cell rendering for credentials -->
      <template #cell(credentials)="{ item }">
        <span v-if="item.matching_credentials_count > 0" class="text-blue-600 cursor-pointer hover:text-blue-800 underline">
          {{ item.matching_credentials_count }} credential(s)
        </span>
        <span v-else class="text-red-500 font-semibold">No credentials found.</span>
      </template>
      <!-- Custom cell rendering for primary actions -->
      <template #cell(primary_actions)="{ item }">
        <div class="flex flex-row space-x-1">
          <Button size="sm" variant="ghost" @click="$emit('edit', item)" aria-label="Edit Device" title="Edit Device">
            <PencilIcon class="h-4 w-4" />
          </Button>
          <Button size="sm" variant="ghost" @click="$emit('delete', item)" aria-label="Delete Device" title="Delete Device">
            <TrashIcon class="h-4 w-4" />
          </Button>
        </div>
      </template>
      <!-- Custom cell rendering for secondary actions -->
      <template #cell(secondary_actions)="{ item }">
        <div class="flex flex-row space-x-1">
          <Button size="sm" variant="ghost" @click="$emit('check-reachability', item)" :disabled="item.status === 'offline'" aria-label="Check Reachability" title="Check Reachability">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2l4-4m5 2a9 9 0 11-18 0a9 9 0 0118 0z" /></svg>
          </Button>
          <Button size="sm" variant="ghost" @click="$emit('credential-check', item)" aria-label="Credential Check" title="Credential Check">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 01-8 0m8 0V5a4 4 0 00-8 0v2m8 0a4 4 0 01-8 0m8 0v2a4 4 0 01-8 0V7" /></svg>
          </Button>
          <Button size="sm" variant="ghost" @click="$emit('view-configs', item)" aria-label="View Configs" title="View Configs">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m2 0a2 2 0 01-2 2H9a2 2 0 01-2-2m2-2h6m2 0a2 2 0 00-2-2H9a2 2 0 00-2 2" /></svg>
          </Button>
        </div>
      </template>
    </BaseTable>
    <!-- Pagination slot -->
    <slot name="pagination"></slot>
  </div>
</template>

<script setup>
import BaseTable from './BaseTable.vue';
import Button from './ui/Button.vue';
import ServiceDot from './ui/ServiceDot.vue';
import { PencilIcon, TrashIcon } from '@heroicons/vue/24/outline';
import { computed } from 'vue';

const props = defineProps({
  devices: { type: Array, required: true },
  loading: { type: Boolean, default: false },
});
const emit = defineEmits(['edit', 'delete', 'check-reachability', 'credential-check', 'view-configs', 'row-click']);

const columns = [
  { key: 'hostname', label: 'Hostname', sortable: true },
  { key: 'ip_address', label: 'Host IP', sortable: true },
  { key: 'serial', label: 'Serial', sortable: false },
  { key: 'reachability', label: 'Reachable', sortable: false },
  { key: 'job_status', label: 'JobStat', sortable: false },
  { key: 'tags', label: 'Tags', sortable: false },
  { key: 'credentials', label: 'Credential', sortable: false },
  { key: 'primary_actions', label: 'Actions', sortable: false },
  { key: 'secondary_actions', label: 'Other', sortable: false },
];

function onRowClick(item) {
  emit('row-click', item);
}

function reachabilityTooltip(device) {
  if (device.last_reachability_status === 'success') return 'Reachable';
  if (device.last_reachability_status === 'failure') return 'Unreachable';
  return 'Never Checked';
}
</script> 