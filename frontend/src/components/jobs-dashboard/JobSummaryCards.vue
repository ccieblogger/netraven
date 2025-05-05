<template>
  <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
    <div class="bg-card p-4 rounded-lg shadow flex flex-col items-center">
      <span class="text-lg font-semibold text-primary">Total</span>
      <span class="text-2xl font-bold">{{ summary.total }}</span>
    </div>
    <div class="bg-card p-4 rounded-lg shadow flex flex-col items-center">
      <span class="text-lg font-semibold text-info">Running</span>
      <span class="text-2xl font-bold">{{ summary.running }}</span>
    </div>
    <div class="bg-card p-4 rounded-lg shadow flex flex-col items-center">
      <span class="text-lg font-semibold text-success">Succeeded</span>
      <span class="text-2xl font-bold">{{ summary.succeeded }}</span>
    </div>
    <div class="bg-card p-4 rounded-lg shadow flex flex-col items-center">
      <span class="text-lg font-semibold text-danger">Failed</span>
      <span class="text-2xl font-bold">{{ summary.failed }}</span>
    </div>
  </div>
</template>
<script setup>
// Phase 1: mock data only
const props = defineProps({
  summary: {
    type: Object,
    required: true,
    default: () => ({ total: 0, running: 0, succeeded: 0, failed: 0 })
  }
})
</script> 