<template>
  <div class="p-4">
    <h2 class="text-xl font-semibold">{{ metadata.description }}</h2>
    <div v-if="metadata.has_parameters" class="mt-4">
      <label class="block mb-1 font-medium">Parameters (JSON or Markdown)</label>
      <textarea v-model="rawParams" class="w-full h-32 p-2 border rounded" placeholder="Enter parameters..."></textarea>
    </div>
    <div class="mt-4">
      <label class="block mb-1 font-medium">Schedule</label>
      <input v-model="schedule" class="w-full p-2 border rounded" placeholder="e.g. @daily or cron expression" />
    </div>
    <div class="mt-4 flex space-x-2">
      <button class="btn btn-primary" @click="runNow">Run Now</button>
      <button class="btn btn-secondary" @click="scheduleJob">Schedule</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  metadata: { type: Object, required: true }
});
const emit = defineEmits(['run-now', 'schedule-job']);

const rawParams = ref('');
const schedule = ref('');

function runNow() {
  emit('run-now', { rawParams: rawParams.value, schedule: schedule.value });
}
function scheduleJob() {
  emit('schedule-job', { rawParams: rawParams.value, schedule: schedule.value });
}
</script>

<style scoped>
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
