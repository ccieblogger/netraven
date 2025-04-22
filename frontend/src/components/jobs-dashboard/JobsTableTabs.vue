<template>
  <div class="flex border-b mb-4">
    <button
      :class="['px-4 py-2 -mb-px font-semibold', tab === 'scheduled' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500']"
      @click="$emit('update:tab', 'scheduled')"
    >
      Scheduled Jobs
    </button>
    <button
      :class="['ml-2 px-4 py-2 -mb-px font-semibold', tab === 'recent' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500']"
      @click="$emit('update:tab', 'recent')"
    >
      Recent Jobs
    </button>
  </div>
</template>
<script setup>
const props = defineProps({
  tab: { type: String, required: true }
})
</script> 