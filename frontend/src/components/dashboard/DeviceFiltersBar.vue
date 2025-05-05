<template>
  <div class="flex flex-wrap items-center gap-4 mb-4 justify-start">
    <input v-model="localFilters.hostname" @input="emitUpdate" type="text" placeholder="Hostname" class="form-input w-40" />
    <input v-model="localFilters.ip_address" @input="emitUpdate" type="text" placeholder="IP Address" class="form-input w-40" />
    <input v-model="localFilters.serial" @input="emitUpdate" type="text" placeholder="Serial" class="form-input w-32" />
    <input v-model="localFilters.global" @input="emitUpdate" type="text" placeholder="Search all..." class="form-input w-48" />
  </div>
</template>
<script setup>
import { reactive, watch } from 'vue';
const props = defineProps({
  filters: {
    type: Object,
    required: true,
    default: () => ({ hostname: '', ip_address: '', serial: '', global: '' })
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