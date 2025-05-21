<template>
  <div class="flex flex-wrap items-center gap-4 mb-4 justify-start">
    <input v-model="localFilters.hostname" @input="emitUpdate" type="text" placeholder="Hostname" class="form-input w-40" />
    <input v-model="localFilters.ip_address" @input="emitUpdate" type="text" placeholder="IP Address" class="form-input w-40" />
    <input v-model="localFilters.serial" @input="emitUpdate" type="text" placeholder="Serial" class="form-input w-32" />
    <input v-model="localFilters.model" @input="emitUpdate" type="text" placeholder="Model" class="form-input w-32" />
    <select v-model="localFilters.source" @change="emitUpdate" class="form-input w-32">
      <option value="">Source</option>
      <option value="local">Local</option>
      <option value="imported">Imported</option>
    </select>
    <input v-model="localFilters.notes" @input="emitUpdate" type="text" placeholder="Notes" class="form-input w-40" />
    <input v-model="localFilters.last_updated" @input="emitUpdate" type="text" placeholder="Last Updated" class="form-input w-36" />
    <input v-model="localFilters.updated_by" @input="emitUpdate" type="text" placeholder="Updated By" class="form-input w-32" />
    <input v-model="localFilters.global" @input="emitUpdate" type="text" placeholder="Search all..." class="form-input w-48" />
  </div>
</template>
<script setup>
import { reactive, watch } from 'vue';
const props = defineProps({
  filters: {
    type: Object,
    required: true,
    default: () => ({ hostname: '', ip_address: '', serial: '', model: '', source: '', notes: '', last_updated: '', updated_by: '', global: '' })
  }
});
const emit = defineEmits(['updateFilters']);
const localFilters = reactive({ ...props.filters });
function emitUpdate() {
  emit('updateFilters', { ...localFilters });
}
watch(() => props.filters, (newVal) => {
  Object.assign(localFilters, newVal);
});
</script>