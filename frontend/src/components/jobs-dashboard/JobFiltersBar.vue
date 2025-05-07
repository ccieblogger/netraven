<template>
  <div class="flex flex-wrap items-center gap-4 mb-4 justify-start">
    <input v-model="localFilters.search" @input="emitUpdate" :placeholder="placeholder" class="form-input" />
  </div>
</template>
<script setup>
import { reactive, watch, onMounted } from 'vue'
const props = defineProps({
  filters: {
    type: Object,
    required: true,
    default: () => ({ search: '' })
  },
  placeholder: {
    type: String,
    default: 'Search...'
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
  localFilters.search = ''
})
</script> 