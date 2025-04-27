<template>
  <span class="inline-flex items-center space-x-2">
    <span :class="dotClass" class="w-3 h-3 rounded-full border border-gray-300"></span>
    <span class="text-xs font-medium" :class="labelClass">{{ label }}</span>
  </span>
</template>

<script setup>
const props = defineProps({
  status: {
    type: String,
    default: 'unknown', // 'healthy', 'unhealthy', 'unknown'
  },
  label: {
    type: String,
    default: '',
  }
})
const dotClass = {
  healthy: 'bg-green-500',
  unhealthy: 'bg-red-500',
  unknown: 'bg-yellow-400',
}[props.status] || 'bg-gray-300'
const labelClass = {
  healthy: 'text-green-600',
  unhealthy: 'text-red-600',
  unknown: 'text-yellow-600',
}[props.status] || 'text-gray-500'
</script> 