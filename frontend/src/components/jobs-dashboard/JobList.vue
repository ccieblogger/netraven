<template>
  <div>
    <!-- Filters -->
    <div class="mb-4 flex gap-2">
      <input v-model="localFilters.name" @input="emitFilters" placeholder="Search by name" class="form-input w-48" />
      <select v-model="localFilters.type" @change="emitFilters" class="form-select w-40">
        <option value="">All Types</option>
        <option v-for="type in jobTypes" :key="type.job_type" :value="type.job_type">
          {{ type.label }}
        </option>
      </select>
      <select v-model="localFilters.status" @change="emitFilters" class="form-select w-32">
        <option value="">All Statuses</option>
        <option value="pending">Pending</option>
        <option value="running">Running</option>
        <option value="completed">Completed</option>
        <option value="failed">Failed</option>
      </select>
    </div>
    <!-- Job Table -->
    <div class="nr-card overflow-x-auto">
      <table class="min-w-full table-auto">
        <thead>
          <tr class="bg-card text-text-secondary text-sm">
            <th class="py-2 px-4 text-left">Name</th>
            <th class="py-2 px-4 text-left">Type</th>
            <th class="py-2 px-4 text-left">Status</th>
            <th class="py-2 px-4 text-left">Schedule</th>
            <th class="py-2 px-4 text-left">Last Run</th>
            <th class="py-2 px-4 text-left">Next Run</th>
            <th class="py-2 px-4 text-left">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="job in jobs" :key="job.id" class="border-b text-text-primary">
            <td class="py-2 px-4 text-xs">{{ job.name }}</td>
            <td class="py-2 px-4 flex items-center gap-2 text-xs">
              <component :is="iconForType(job.job_type)" class="w-4 h-4" />
              {{ labelForType(job.job_type) }}
            </td>
            <td class="py-2 px-4 text-xs">{{ job.status }}</td>
            <td class="py-2 px-4 text-xs">
              <span v-if="job.schedule_type === 'interval'">Every {{ job.interval_seconds }}s</span>
              <span v-else-if="job.schedule_type === 'cron'">{{ job.cron_string }}</span>
              <span v-else-if="job.schedule_type === 'onetime'">{{ formatDate(job.scheduled_for) }}</span>
              <span v-else>-</span>
            </td>
            <td class="py-2 px-4 text-xs">{{ formatDate(job.completed_at || job.started_at) }}</td>
            <td class="py-2 px-4 text-xs">{{ formatDate(job.next_run) }}</td>
            <td class="py-2 px-4 flex gap-1 text-xs">
              <button class="btn btn-xs btn-ghost" @click="$emit('run', job)">Run</button>
              <button class="btn btn-xs btn-ghost" @click="$emit('edit', job)">Edit</button>
              <button class="btn btn-xs btn-ghost text-red-500" @click="$emit('delete', job)">Delete</button>
              <button class="btn btn-xs btn-ghost" @click="$emit('details', job)">Details</button>
            </td>
          </tr>
          <tr v-if="!isLoading && jobs.length === 0">
            <td colspan="6" class="text-center text-text-secondary py-4">No jobs found.</td>
          </tr>
          <tr v-if="isLoading">
            <td colspan="6" class="text-center text-text-secondary py-4">Loading jobs...</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { CloudArrowDownIcon, SignalIcon, QuestionMarkCircleIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  jobs: { type: Array, required: true },
  jobTypes: { type: Array, required: true },
  isLoading: { type: Boolean, default: false },
  filters: { type: Object, required: true }
})

const emit = defineEmits(['run', 'edit', 'delete', 'details', 'update:filters'])

const localFilters = ref({ ...props.filters })

watch(() => props.filters, (newVal) => {
  localFilters.value = { ...newVal }
})

function emitFilters() {
  emit('update:filters', { ...localFilters.value })
}

function labelForType(jobType) {
  const type = props.jobTypes.find(t => t.job_type === jobType)
  return type ? type.label : jobType
}
function iconForType(jobType) {
  const type = props.jobTypes.find(t => t.job_type === jobType)
  if (!type) return QuestionMarkCircleIcon
  if (type.icon === 'BackupIcon') return CloudArrowDownIcon
  if (type.icon === 'NetworkCheckIcon') return SignalIcon
  return QuestionMarkCircleIcon
}
function formatDate(dt) {
  if (!dt) return '-'
  try {
    return new Date(dt).toLocaleString()
  } catch {
    return dt
  }
}
</script> 