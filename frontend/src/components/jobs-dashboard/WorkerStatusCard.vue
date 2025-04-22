<template>
  <NrCard accent className="border-l-4 border-l-green-600">
    <div class="p-4 flex justify-between items-start">
      <div>
        <h2 class="text-lg uppercase font-semibold text-text-secondary">Worker Status</h2>
        <div class="mt-2">
          <div class="text-text-primary font-bold">{{ workerStatus }}</div>
          <div class="text-xs text-text-secondary">Jobs in proc <span class="font-bold text-text-primary">{{ jobsInProc }}</span></div>
        </div>
      </div>
      <div class="flex items-center justify-center h-10 w-10 rounded-md bg-green-600">
        <!-- User Group Icon -->
        <svg class="w-6 h-6 text-green-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87m9-4a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      </div>
    </div>
  </NrCard>
</template>
<script setup>
import NrCard from '../ui/Card.vue'
import { computed } from 'vue'
const props = defineProps({ status: Object })
const workerStatus = computed(() => props.status && props.status.workers && props.status.workers.length > 0 ? (props.status.workers[0].status || 'ACTIVE') : 'ACTIVE')
const jobsInProc = computed(() => props.status && props.status.workers && props.status.workers.length > 0 ? (props.status.workers[0].jobs_in_progress || 0) : 12)
</script> 