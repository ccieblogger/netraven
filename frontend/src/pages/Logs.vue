<template>
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-semibold mb-4">Logs</h1>
    <div v-if="isLoading" class="text-center py-8 text-gray-500">Loading logs...</div>
    <div v-else>
      <DataTable :value="logs" dataKey="id" class="shadow-md rounded bg-white w-full">
        <Column field="timestamp" header="Timestamp" />
        <Column field="log_type" header="Type" />
        <Column field="level" header="Level" />
        <Column field="job_id" header="Job ID" />
        <Column field="device_id" header="Device ID" />
        <Column field="source" header="Source" />
        <Column field="message" header="Message" />
      </DataTable>
      <div v-if="logs.length === 0" class="text-center text-gray-400 py-8">No logs found.</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useLogStore } from '../store/log'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'

const logStore = useLogStore()
const isLoading = ref(false)

const logs = computed(() => logStore.logs)

onMounted(async () => {
  isLoading.value = true
  await logStore.fetchLogs()
  isLoading.value = false
})
</script>

<style scoped>
.container {
  max-width: 1200px;
}
</style>
