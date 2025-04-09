<template>
  <div class="container mx-auto p-4">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-semibold">Job Monitor</h1>
      <div>
        <router-link 
          to="/jobs" 
          class="text-blue-500 hover:text-blue-700 flex items-center"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
          </svg>
          Back to Jobs
        </router-link>
      </div>
    </div>

    <div v-if="!jobId" class="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-6">
      <p>No job ID specified. Please select a job to monitor.</p>
      <router-link 
        to="/jobs" 
        class="mt-2 inline-block text-blue-500 hover:text-blue-700"
      >
        View all jobs
      </router-link>
    </div>

    <JobMonitor v-else :job-id="jobId" />
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router';
import { computed } from 'vue';
import JobMonitor from '../components/JobMonitor.vue';

const route = useRoute();

// Get job ID from route params
const jobId = computed(() => {
  return route.params.id || null;
});
</script> 