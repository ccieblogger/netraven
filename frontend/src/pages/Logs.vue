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
      >
        <Column field="timestamp" header="Timestamp" :headerClass="headerClass" :bodyClass="bodyClass" />
        <Column field="log_type" header="Type" :headerClass="headerClass" :bodyClass="bodyClass" />
        <Column field="level" header="Level" :headerClass="headerClass" :bodyClass="bodyClass" />
        <Column field="job_id" header="Job ID" :headerClass="headerClass" :bodyClass="bodyClass" />
        <Column field="device_id" header="Device ID" :headerClass="headerClass" :bodyClass="bodyClass" />
        <Column field="source" header="Source" :headerClass="headerClass" :bodyClass="bodyClass" />
        <Column field="message" header="Message" :headerClass="headerClass" :bodyClass="bodyClass" />
      </DataTable>
    </div>
  </Card>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useLogStore } from '../store/log'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Card from '../components/ui/Card.vue'

const logStore = useLogStore()
const isLoading = ref(false)

const logs = computed(() => logStore.logs)

const headerClass = 'bg-card text-text-primary font-semibold'
const bodyClass = 'px-4'

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
</style>
