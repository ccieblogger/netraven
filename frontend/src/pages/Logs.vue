<template>
  <PageContainer title="Dashboard" subtitle="System overview and device inventory">
  <Card title="Logs" subtitle="System and job event history">
    <template #header>
      <div class="flex justify-end px-2 pt-2 text-xs">
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
        class="text-text-primary min-w-full text-xs"
        tableStyle="min-width: 100%"
        :emptyMessage="logs.length === 0 ? 'No logs found.' : ''"
        filterDisplay="row"
        v-model:filters="filters"
        :globalFilterFields="['timestamp', 'log_type', 'level', 'job_id', 'device_id', 'source', 'message']"
      >
        <Column field="timestamp" header="Timestamp" style="min-width: 12rem" filter :headerClass="'text-text-primary font-semibold'" :bodyClass="'px-4'">
          <template #body="{ data }">
            {{ data.timestamp }}
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <InputText v-model="filterModel.value" type="text" @input="filterCallback()" placeholder="Search timestamp" class="w-full" />
          </template>
        </Column>
        <Column field="log_type" header="Type" style="min-width: 8rem" filter :headerClass="'text-text-primary font-semibold'" :bodyClass="'px-4'">
          <template #body="{ data }">
            {{ data.log_type }}
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <InputText v-model="filterModel.value" type="text" @input="filterCallback()" placeholder="Search type" class="w-full" />
          </template>
        </Column>
        <Column field="level" header="Level" style="min-width: 8rem" filter :headerClass="'text-text-primary font-semibold'" :bodyClass="'px-4'">
          <template #body="{ data }">
            {{ data.level }}
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <InputText v-model="filterModel.value" type="text" @input="filterCallback()" placeholder="Search level" class="w-full" />
          </template>
        </Column>
        <Column field="job_id" header="Job ID" style="min-width: 8rem" filter :headerClass="'text-text-primary font-semibold'" :bodyClass="'px-4'">
          <template #body="{ data }">
            {{ data.job_id }}
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <InputText v-model="filterModel.value" type="text" @input="filterCallback()" placeholder="Search job ID" class="w-full" />
          </template>
        </Column>
        <Column field="device_id" header="Device ID" style="min-width: 8rem" filter :headerClass="'text-text-primary font-semibold'" :bodyClass="'px-4'">
          <template #body="{ data }">
            {{ data.device_id }}
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <InputText v-model="filterModel.value" type="text" @input="filterCallback()" placeholder="Search device ID" class="w-full" />
          </template>
        </Column>
        <Column field="source" header="Source" style="min-width: 10rem" filter :headerClass="'text-text-primary font-semibold'" :bodyClass="'px-4'">
          <template #body="{ data }">
            {{ data.source }}
          </template>
          <template #filter="{ filterModel, filterCallback }">
            <InputText v-model="filterModel.value" type="text" @input="filterCallback()" placeholder="Search source" class="w-full" />
          </template>
        </Column>
        <Column field="message" header="Message" style="min-width: 16rem" filter :headerClass="'text-text-primary font-semibold'" :bodyClass="'px-4'">
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
  </PageContainer>
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
