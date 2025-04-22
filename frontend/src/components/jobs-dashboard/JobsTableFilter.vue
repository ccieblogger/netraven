<template>
  <div v-if="selectedFilters.length > 0" class="mb-2 flex items-center">
    <span class="mr-2 text-gray-600">Filter:</span>
    <span v-for="filter in selectedFilters" :key="filter" class="bg-blue-100 text-blue-700 px-2 py-1 rounded-full text-xs mr-2 flex items-center">
      {{ filter }}
      <button @click="$emit('removeFilter', filter)" class="ml-1 text-blue-500 hover:text-blue-700 focus:outline-none">&times;</button>
    </span>
  </div>
</template>
<script setup>
const props = defineProps({
  activeTab: String,
  selectedFilters: Array
})
</script> 