<template>
  <NrCard accent className="border-l-4 border-l-red-500">
    <div class="p-4 flex justify-between items-start">
      <div>
        <h2 class="text-lg uppercase font-semibold text-text-secondary">Redis Status</h2>
        <div class="mt-2">
          <div class="text-base text-text-primary font-bold">{{ upText }}</div>
          <div class="text-base text-text-primary font-semibold">{{ uptimeText }}</div>
          <div class="text-base text-text-primary font-semibold">{{ memoryText }}</div>
          <div class="text-base text-text-primary font-semibold">{{ heartbeatText }}</div>
        </div>
      </div>
      <div class="flex items-center justify-center h-10 w-10 rounded-md bg-red-600">
        <!-- Database Icon -->
        <svg class="w-6 h-6 text-red-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <ellipse cx="12" cy="5" rx="9" ry="3" />
          <path d="M3 5v14c0 1.657 4.03 3 9 3s9-1.343 9-3V5" />
        </svg>
      </div>
    </div>
  </NrCard>
</template>
<script setup>
import NrCard from '../ui/Card.vue'
import { computed } from 'vue'
const props = defineProps({ status: Object })
const upText = computed(() => props.status ? 'UP' : 'DOWN')
const uptimeText = computed(() => props.status && props.status.redis_uptime ? `${Math.floor(props.status.redis_uptime/86400)} days, ${Math.floor((props.status.redis_uptime%86400)/3600)} hours` : '8 days, 4 hours')
const memoryText = computed(() => props.status && props.status.redis_memory ? `${(props.status.redis_memory/1024/1024).toFixed(0)} MB` : '123 MB')
const heartbeatText = computed(() => props.status && props.status.redis_last_heartbeat ? `${props.status.redis_last_heartbeat} ago` : '10 seconds ago')
</script> 