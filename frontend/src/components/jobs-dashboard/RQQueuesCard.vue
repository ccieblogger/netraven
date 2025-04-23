<template>
  <NrCard accent className="border-l-4 border-l-yellow-500">
    <div class="p-4 flex justify-between items-start">
      <div>
        <h2 class="text-lg uppercase font-semibold text-text-secondary">RQ Queues</h2>
        <div class="mt-2 space-y-1">
          <div class="flex justify-between items-center">
            <span class="text-sm text-text-secondary">Total jobs</span>
            <span class="text-base text-text-primary font-bold">{{ totalJobs }}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-sm text-text-secondary">Low queue</span>
            <span class="text-base text-text-primary font-bold">{{ lowQueue }}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-sm text-text-secondary">High queue</span>
            <span class="text-base text-text-primary font-bold">{{ highQueue }}</span>
          </div>
        </div>
      </div>
      <div class="flex items-center justify-center h-10 w-10 rounded-md bg-yellow-500">
        <!-- List Icon -->
        <svg class="w-6 h-6 text-yellow-100" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7" />
        </svg>
      </div>
    </div>
  </NrCard>
</template>
<script setup>
import NrCard from '../ui/Card.vue'
import { computed } from 'vue'
const props = defineProps({ status: Object })
const totalJobs = computed(() => props.status && props.status.rq_queues ? props.status.rq_queues.reduce((sum, q) => sum + (q.job_count || 0), 0) : 45)
const lowQueue = computed(() => props.status && props.status.rq_queues ? (props.status.rq_queues.find(q => q.name === 'low')?.job_count || 0) : 30)
const highQueue = computed(() => props.status && props.status.rq_queues ? (props.status.rq_queues.find(q => q.name === 'high')?.job_count || 0) : 15)
</script> 