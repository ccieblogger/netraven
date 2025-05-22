<template>
  <div class="job-form-grid grid grid-cols-2 gap-6">
    <div>
      <h2 class="text-xl font-semibold mb-2">Job Parameters</h2>
      <p class="text-gray-700 italic">No dynamic form available. Please see the job description for details.</p>
    </div>
    <div>
      <div class="mt-4 flex gap-2">
        <button class="btn btn-primary" @click="runNow">Run Now</button>
        <button class="btn btn-secondary" @click="scheduleJob">Schedule</button>
      </div>
      <div class="mt-6 p-4 bg-gray-50 rounded">
        <h3 class="font-semibold">Description</h3>
        <p class="text-gray-700">{{ metadata.description }}</p>
        <!-- If you want markdown support, replace the above line with a markdown renderer later -->
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  metadata: { type: Object, required: true }
});
const emit = defineEmits(['run-now', 'schedule-job']);

function runNow() {
  emit('run-now', {});
}
function scheduleJob() {
  emit('schedule-job', {});
}
</script>

<style scoped>
.job-form-grid {
  min-height: 400px;
}
.btn {
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 500;
}
.btn-primary {
  background-color: #2563eb;
  color: #fff;
  transition: background 0.2s;
}
.btn-primary:hover {
  background-color: #1d4ed8;
}
.btn-secondary {
  background-color: #e5e7eb;
  color: #1f2937;
  transition: background 0.2s;
}
.btn-secondary:hover {
  background-color: #d1d5db;
}
</style>
