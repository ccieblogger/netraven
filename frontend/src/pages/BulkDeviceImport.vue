<template>
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-semibold mb-4">Bulk Device Import</h1>
    <div class="mb-6">
      <p class="mb-2 text-gray-700">
        Import multiple devices at once using a CSV or JSON file. Download a sample file and review the required schema below.
      </p>
      <div class="flex flex-row gap-4 mb-2">
        <a :href="sampleCsvUrl" download class="btn btn-sm btn-outline">Download CSV Sample</a>
        <a :href="sampleJsonUrl" download class="btn btn-sm btn-outline">Download JSON Sample</a>
      </div>
      <div class="mb-2">
        <label class="block font-medium mb-1">Upload CSV or JSON File</label>
        <input type="file" accept=".csv,.json" @change="onFileChange" />
      </div>
    </div>
    <div class="mb-6">
      <h2 class="text-lg font-semibold mb-2">Import Schema</h2>
      <CodeBlock :code="schemaExample" language="json" />
    </div>
    <div v-if="importResult" class="mb-6">
      <h2 class="text-lg font-semibold mb-2">Import Results</h2>
      <div class="mb-2 text-green-700" v-if="importResult.success_count > 0">
        {{ importResult.success_count }} device(s) imported successfully.
      </div>
      <div v-if="importResult.errors.length">
        <h3 class="font-semibold text-red-700">Errors</h3>
        <ul class="list-disc ml-6">
          <li v-for="err in importResult.errors" :key="'err-' + err.row">Row {{ err.row }}: {{ err.error }}</li>
        </ul>
      </div>
      <div v-if="importResult.duplicates.length">
        <h3 class="font-semibold text-yellow-700">Duplicates</h3>
        <ul class="list-disc ml-6">
          <li v-for="dup in importResult.duplicates" :key="'dup-' + dup.row">Row {{ dup.row }}: {{ dup.reason }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import CodeBlock from '../components/CodeBlock.vue'
import api from '../services/api'

const importResult = ref(null)
const sampleCsvUrl = '/public/samples/bulk_device_import_sample.csv'
const sampleJsonUrl = '/public/samples/bulk_device_import_sample.json'

const schemaExample = `[
  {
    "hostname": "core-sw-01",
    "ip_address": "10.0.0.2",
    "device_type": "cisco_ios",
    "port": 22,
    "description": "Core switch",
    "serial_number": "FTX1234A1B2",
    "model": "Catalyst 9300",
    "source": "imported",
    "notes": "Main rack"
  }
]`

function onFileChange(e) {
  const file = e.target.files[0]
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  api.post('/devices/bulk_import', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    .then(res => {
      importResult.value = res.data
    })
    .catch(err => {
      importResult.value = { success_count: 0, errors: [{ row: '-', error: err.response?.data?.detail || 'Import failed' }], duplicates: [] }
    })
}
</script>

<style scoped>
.btn {
  @apply px-3 py-1 rounded border border-gray-300 bg-white hover:bg-gray-100 text-gray-700;
}
</style>
