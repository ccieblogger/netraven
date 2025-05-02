<template>
  <Card title="Logs" subtitle="System and job event history" className="mb-8">
    <template #header>
      <div class="px-2 pt-2">
        <h2 class="text-lg font-semibold text-text-primary">Logs</h2>
        <p class="text-xs text-text-secondary">System and job event history</p>
      </div>
    </template>
    <div v-if="isLoading" class="text-center py-8 text-gray-500">Loading logs...</div>
    <div v-else>
      <DataTable
        :value="logs"
        dataKey="id"
        stripedRows
        responsiveLayout="scroll"
        class="text-text-primary min-w-full"
        tableStyle="min-width: 100%"
        :emptyMessage="logs.length === 0 ? 'No logs found.' : ''"
        filterDisplay="row"
        v-model:filters="filters"
      >
        <Column field="timestamp" header="Timestamp" :headerClass="headerClass" :bodyClass="bodyClass" filter filterMatchMode="contains" />
        <Column field="log_type" header="Type" :headerClass="headerClass" :bodyClass="bodyClass" filter filterMatchMode="equals">
          <template #filter="{ filterModel }">
            <Dropdown v-model="filterModel.value" :options="logTypeOptions" placeholder="All Types" showClear class="w-full" />
          </template>
        </Column>
        <Column field="level" header="Level" :headerClass="headerClass" :bodyClass="bodyClass" filter filterMatchMode="equals">
          <template #filter="{ filterModel }">
            <Dropdown v-model="filterModel.value" :options="logLevelOptions" placeholder="All Levels" showClear class="w-full" />
          </template>
        </Column>
        <Column field="job_id" header="Job ID" :headerClass="headerClass" :bodyClass="bodyClass" filter filterMatchMode="contains" />
        <Column field="device_id" header="Device ID" :headerClass="headerClass" :bodyClass="bodyClass" filter filterMatchMode="contains" />
        <Column field="source" header="Source" :headerClass="headerClass" :bodyClass="bodyClass" filter filterMatchMode="contains" />
        <Column field="message" header="Message" :headerClass="headerClass" :bodyClass="bodyClass" filter filterMatchMode="contains" />
      </DataTable>
    </div>
  </Card>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useLogStore } from '../store/log'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dropdown from 'primevue/dropdown'
import Card from '../components/ui/Card.vue'

const logStore = useLogStore()
const isLoading = ref(false)

const logs = computed(() => logStore.logs)

const headerClass = 'bg-card text-text-primary font-semibold'
const bodyClass = 'px-4'

// PrimeVue filter state
const filters = ref({
  timestamp: { value: null, matchMode: 'contains' },
  log_type: { value: null, matchMode: 'equals' },
  level: { value: null, matchMode: 'equals' },
  job_id: { value: null, matchMode: 'contains' },
  device_id: { value: null, matchMode: 'contains' },
  source: { value: null, matchMode: 'contains' },
  message: { value: null, matchMode: 'contains' },
})

// Dropdown options for log_type and level
const logTypeOptions = ref([
  { label: 'Job', value: 'job' },
  { label: 'Connection', value: 'connection' },
  { label: 'Session', value: 'session' },
  { label: 'System', value: 'system' },
])
const logLevelOptions = ref([
  { label: 'Info', value: 'info' },
  { label: 'Warning', value: 'warning' },
  { label: 'Error', value: 'error' },
  { label: 'Debug', value: 'debug' },
])

onMounted(async () => {
  isLoading.value = true
  await logStore.fetchLogs()
  isLoading.value = false
})
</script>

<style scoped>
:deep(.p-datatable-thead > tr) {
  border-bottom: 2px solid var(--nr-text-primary);
}
:deep(.p-datatable-tbody > tr) {
  border-bottom: 1px solid var(--nr-border);
}
:deep(.p-paginator) {
  background-color: var(--nr-bg-card) !important;
}
:deep(.p-column-filter) {
  width: 100%;
  min-width: 120px;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  padding: 0.5rem 0.75rem;
  font-size: 0.95rem;
}
</style>
