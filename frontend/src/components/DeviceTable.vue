<template>
  <!-- Device Table Card: aligns with filter/search section, uses production theme -->
  <div>
    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-2 px-2 pt-6 mb-2">
      <slot name="filters"></slot>
      <slot name="search"></slot>
    </div>

    <!-- Table Section: accessible, responsive, themed -->
    <div class="overflow-x-auto px-2">
      <DataTable
        :value="devices"
        :loading="loading"
        dataKey="id"
        :paginator="true"
        :rows="pageSize"
        :rowsPerPageOptions="[10, 20, 50]"
        class="text-text-primary min-w-full"
        tableStyle="min-width: 100%"
        responsiveLayout="scroll"
        :emptyMessage="emptyMessage"
        :sortField="sortField"
        :sortOrder="sortOrder"
        @sort="onSort"
        @rowClick="onRowClick"
        stripedRows
        :pt="{ bodyRow: 'bg-card', bodyRowEven: 'bg-card', paginator: { class: 'bg-card' } }"
      >
        <!-- Static columns with header/body color classes -->
        <Column field="hostname" header="Hostname" sortable class="px-4" :headerClass="'bg-card text-text-primary font-semibold'" :bodyClass="bodyClass('hostname')" />
        <Column field="ip_address" header="Host IP" sortable class="px-4" :headerClass="'bg-card text-text-primary font-semibold'" :bodyClass="bodyClass('ip_address')" />
        <Column field="serial" header="Serial" class="px-4" :headerClass="'bg-card text-text-primary font-semibold'" :bodyClass="bodyClass('serial')" />
        <Column header="Reachable" class="px-4" :headerClass="'bg-card text-text-primary font-semibold'">
          <template #body="{ data }">
            <ServiceDot
              :status="data.last_reachability_status === 'success' ? 'healthy' : data.last_reachability_status === 'failure' ? 'unhealthy' : 'unknown'"
              :label="''"
              :tooltip="reachabilityTooltip(data)"
            />
          </template>
        </Column>
        <Column field="job_status" header="JobStat" class="px-4" :headerClass="'bg-card text-text-primary font-semibold'" :bodyClass="bodyClass('job_status')" />
        <Column header="Tags" class="px-4" :headerClass="'bg-card text-text-primary font-semibold'">
          <template #body="{ data }">
            <span v-for="tag in data.tags" :key="tag.id" class="bg-blue-900/30 text-blue-200 py-1 px-3 rounded-full text-xs mr-1">
              {{ tag.name }}
            </span>
          </template>
        </Column>
        <Column header="Credential" class="px-4" :headerClass="'bg-card text-text-primary font-semibold'">
          <template #body="{ data }">
            <span v-if="data.matching_credentials_count > 0" class="text-blue-300 cursor-pointer hover:text-blue-100 underline">
              {{ data.matching_credentials_count }} credential(s)
            </span>
            <span v-else class="text-red-400 font-semibold">No credentials found.</span>
          </template>
        </Column>
        <Column header="Actions" class="px-4" :headerClass="'bg-card text-text-primary font-semibold'">
          <template #body="{ data }">
            <div class="flex flex-row space-x-1">
              <Button size="sm" variant="ghost" @click="$emit('edit', data)" aria-label="Edit Device" title="Edit Device" iconOnly>
                <PencilIcon class="h-4 w-4" />
              </Button>
              <Button size="sm" variant="ghost" @click="$emit('delete', data)" aria-label="Delete Device" title="Delete Device" iconOnly>
                <TrashIcon class="h-4 w-4" />
              </Button>
            </div>
          </template>
        </Column>
        <Column header="Other" class="px-4" :headerClass="'bg-card text-text-primary font-semibold'">
          <template #body="{ data }">
            <div class="flex flex-row space-x-1">
              <Button size="sm" variant="ghost" @click="$emit('check-reachability', data)" :disabled="data.status === 'offline'" aria-label="Check Reachability" title="Check Reachability" iconOnly>
                <i class="pi pi-check-circle h-4 w-4" />
              </Button>
              <Button size="sm" variant="ghost" @click="$emit('credential-check', data)" aria-label="Credential Check" title="Credential Check" iconOnly>
                <i class="pi pi-key h-4 w-4" />
              </Button>
              <Button size="sm" variant="ghost" @click="$emit('view-configs', data)" aria-label="View Configs" title="View Configs" iconOnly>
                <i class="pi pi-eye h-4 w-4" />
              </Button>
            </div>
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>

<script setup>
// DeviceTable.vue: Device inventory table with best practices for theming, accessibility, and UX
import { ref, computed } from 'vue';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from './ui/Button.vue';
import ServiceDot from './ui/ServiceDot.vue';
import { PencilIcon, TrashIcon } from '@heroicons/vue/24/outline';

/**
 * Props:
 *  - devices: Array of device objects to display
 *  - loading: Boolean, show loading state
 *  - pageSize: Number, default page size
 */
const props = defineProps({
  devices: { type: Array, required: true },
  loading: { type: Boolean, default: false },
  pageSize: { type: Number, default: 10 },
});
const emit = defineEmits(['edit', 'delete', 'check-reachability', 'credential-check', 'view-configs', 'row-click']);

const sortField = ref('hostname');
const sortOrder = ref(1); // 1 = asc, -1 = desc

function onSort(e) {
  sortField.value = e.sortField;
  sortOrder.value = e.sortOrder;
}

function onRowClick(e) {
  emit('row-click', e.data);
}

function reachabilityTooltip(device) {
  if (device.last_reachability_status === 'success') return 'Reachable';
  if (device.last_reachability_status === 'failure') return 'Unreachable';
  return 'Never Checked';
}

const emptyMessage = computed(() => props.loading ? 'Loading devices...' : 'No devices found');

// Add bodyClass to highlight sorted column
function bodyClass(field) {
  return field === sortField ? 'text-blue-400' : '';
}
</script>

<style scoped>
:deep(.p-paginator) {
  background-color: var(--nr-bg-card) !important;
}
</style> 