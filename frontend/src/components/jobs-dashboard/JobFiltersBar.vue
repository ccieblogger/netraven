<template>
  <div class="flex flex-wrap items-center gap-4 mb-4 justify-start">
    <select v-model="localFilters.job" @change="emitUpdate" class="form-select w-48">
      <option value="">All Jobs</option>
      <option v-for="name in jobNames" :key="name" :value="name">{{ name }}</option>
    </select>
    <select v-model="localFilters.type" @change="emitUpdate" class="form-select w-48">
      <option value="">All Job Types</option>
      <option v-for="type in jobTypes" :key="type" :value="type">{{ type }}</option>
    </select>
    <input v-model="localFilters.search" @input="emitUpdate" type="text" placeholder="Search jobs/logs..." class="form-input" />
  </div>
</template>
<script setup>
// Phase 1: mock data only
import { reactive, watch, onMounted } from 'vue'
const props = defineProps({
  filters: {
    type: Object,
    required: true,
    default: () => ({ job: '', type: '', search: '' })
  },
  jobNames: {
    type: Array,
    required: true,
    default: () => []
  },
  jobTypes: {
    type: Array,
    required: true,
    default: () => []
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
onMounted(() => {
  localFilters.job = ''
})
watch(() => props.jobNames, (newNames) => {
  if (!newNames.includes(localFilters.job)) {
    localFilters.job = ''
  }
})
</script> 