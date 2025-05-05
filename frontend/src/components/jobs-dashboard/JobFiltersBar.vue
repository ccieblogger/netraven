<template>
  <div class="flex flex-wrap items-center gap-4 mb-4 px-6">
    <select v-model="localFilters.status" @change="emitUpdate" class="form-select">
      <option value="">All Statuses</option>
      <option value="Running">Running</option>
      <option value="Succeeded">Succeeded</option>
      <option value="Failed">Failed</option>
    </select>
    <select v-model="localFilters.type" @change="emitUpdate" class="form-select">
      <option value="">All Types</option>
      <option value="Backup">Backup</option>
      <option value="Audit">Audit</option>
      <option value="Config Pull">Config Pull</option>
    </select>
    <input v-model="localFilters.search" @input="emitUpdate" type="text" placeholder="Search jobs/logs..." class="form-input" />
  </div>
</template>
<script setup>
// Phase 1: mock data only
import { reactive, watch } from 'vue'
const props = defineProps({
  filters: {
    type: Object,
    required: true,
    default: () => ({ status: '', type: '', search: '' })
  }
})
const emit = defineEmits(['updateFilters'])
const localFilters = reactive({ ...props.filters })
function emitUpdate() {
  emit('updateFilters', { ...localFilters })
}
watch(() => props.filters, (newVal) => {
  Object.assign(localFilters, newVal)
})
</script> 