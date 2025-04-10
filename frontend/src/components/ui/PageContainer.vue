<template>
  <div class="page-container h-full">
    <!-- Page header with title and optional actions -->
    <div class="mb-6 flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-semibold text-text-primary">{{ title }}</h1>
        <p v-if="subtitle" class="mt-1 text-sm text-text-secondary">{{ subtitle }}</p>
        
        <!-- Breadcrumbs -->
        <div v-if="breadcrumbs && breadcrumbs.length" class="mt-2 flex items-center text-sm text-text-secondary">
          <router-link to="/" class="hover:text-primary">Home</router-link>
          <svg v-for="(crumb, index) in breadcrumbs" :key="index" class="w-4 h-4 mx-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
          <span v-if="!crumb.to">{{ crumb.text }}</span>
          <router-link v-else :to="crumb.to" class="hover:text-primary">{{ crumb.text }}</router-link>
        </div>
      </div>
      
      <!-- Actions slot for buttons, etc. -->
      <div v-if="$slots.actions" class="flex items-center space-x-3">
        <slot name="actions"></slot>
      </div>
    </div>
    
    <!-- Page content -->
    <div class="space-y-6">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  },
  breadcrumbs: {
    type: Array,
    default: () => []
    // Expected format: [{ text: 'Devices', to: '/devices' }, { text: 'Edit Device' }]
  }
});
</script> 