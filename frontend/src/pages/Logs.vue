<template>
  <Card title="Logs" subtitle="System and job event history" className="mb-8">
    <template #header>
      <div class="flex justify-end px-2 pt-2">
        <IconField>
          <InputIcon>
            <i class="pi pi-search" />
          </InputIcon>
          <InputText v-model="filters.global.value" placeholder="Keyword Search" class="w-64" />
        </IconField>
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
        :globalFilterFields="['timestamp', 'log_type', 'level', 'job_id', 'device_id', 'source', 'message']"
        :pt="{
          bodyRow: 'bg-card',
          bodyRowEven: 'bg-card',
          paginator: { class: 'bg-card' },
          headerCell: 'bg-card text-text-primary font-semibold',
          filterCell: 'bg-card text-text-primary font-semibold'
        }"
      >
        <Column field="timestamp" header="Timestamp" style="min-width: 12rem" filter :headerClass="'bg-card text-text-primary font-semibold'" :bodyClass="'px-4'">
          <template #body="{ data }">
            {{ data.timestamp }}
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <InputText v-model="filterModel.value" type="text" @input="filterCallback()" placeholder="Search timestamp" class="w-full" />
          </template>
        </Column>
        <Column field="log_type" header="Type" style="min-width: 8rem" filter :headerClass="'bg-card text-text-primary font-semibold'" :bodyClass="'px-4'">
          <template #body="{ data }">
            {{ data.log_type }}
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <InputText v-model="filterModel.value" type="text" @input="filterCallback()" placeholder="Search type" class="w-full" />
          </template>
        </Column>
        <Column field="level" header="Level" style="min-width: 8rem" filter :headerClass="'bg-card text-text-primary font-semibold'" :bodyClass="'px-4'">
          <template #body="{ data }">
            {{ data.level }}
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <InputText v-model="filterModel.value" type="text" @input="filterCallback()" placeholder="Search level" class="w-full" />
          </template>
        </Column>
        <Column field="job_id" header="Job ID" style="min-width: 8rem" filter :headerClass="'bg-card text-text-primary font-semibold'" :bodyClass="'px-4'">
          <template #body="{ data }">
            {{ data.job_id }}
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <InputText v-model="filterModel.value" type="text" @input="filterCallback()" placeholder="Search job ID" class="w-full" />
          </template>
        </Column>
        <Column field="device_id" header="Device ID" style="min-width: 8rem" filter :headerClass="'bg-card text-text-primary font-semibold'" :bodyClass="'px-4'">
          <template #body="{ data }">
            {{ data.device_id }}
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <InputText v-model="filterModel.value" type="text" @input="filterCallback()" placeholder="Search device ID" class="w-full" />
          </template>
        </Column>
        <Column field="source" header="Source" style="min-width: 10rem" filter :headerClass="'bg-card text-text-primary font-semibold'" :bodyClass="'px-4'">
          <template #body="{ data }">
            {{ data.source }}
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <InputText v-model="filterModel.value" type="text" @input="filterCallback()" placeholder="Search source" class="w-full" />
          </template>
        </Column>
        <Column field="message" header="Message" style="min-width: 16rem" filter :headerClass="'bg-card text-text-primary font-semibold'" :bodyClass="'px-4'">
          <template #body="{ data }">
            {{ data.message }}
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <InputText v-model="filterModel.value" type="text" @input="filterCallback()" placeholder="Search message" class="w-full" />
          </template>
        </Column>
        <template #empty>
          <div class="text-center py-8 text-gray-500">No logs found.</div>
        </template>
        <template #loading>
          <div class="text-center py-8 text-gray-500">Loading logs data. Please wait.</div>
        </template>
      </DataTable>
    </div>
  </Card>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useLogStore } from '../store/log'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputText from 'primevue/inputtext'
import Card from '../components/ui/Card.vue'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'

const logStore = useLogStore()
const isLoading = ref(false)

const logs = computed(() => logStore.logs)

const filters = ref({
  global: { value: null, matchMode: 'contains' },
  timestamp: { value: null, matchMode: 'contains' },
  log_type: { value: null, matchMode: 'contains' },
  level: { value: null, matchMode: 'contains' },
  job_id: { value: null, matchMode: 'contains' },
  device_id: { value: null, matchMode: 'contains' },
  source: { value: null, matchMode: 'contains' },
  message: { value: null, matchMode: 'contains' },
})

onMounted(async () => {
  isLoading.value = true
  await logStore.fetchLogs()
  isLoading.value = false
})
</script>

<!--
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
  border: none !important;
  box-shadow: none !important;
  background: inherit !important;
  color: #fff !important;
  width: 100%;
  min-width: 120px;
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  font-size: 0.95rem;
}
:deep(.p-inputtext) {
  background: inherit !important;
  color: #fff !important;
  border: 1px solid var(--nr-border) !important;
  border-radius: 6px;
}
:deep(.p-icon-field) {
  background: #181a20 !important;
  border-radius: 6px;
  border: 1px solid var(--nr-border) !important;
  color: #fff !important;
}
:deep(.p-input-icon) {
  color: var(--nr-text-secondary) !important;
}
</style>
-->
