<template>
  <BaseModal :is-open="isOpen" :title="modalTitle" @close="closeModal">
    <template #content>
      <form @submit.prevent="submitForm">
        <div class="space-y-4">
          <!-- Job Name -->
          <div>
            <label for="jobName" class="block text-sm font-medium text-gray-700">Job Name</label>
            <input type="text" id="jobName" v-model="form.name" required
                   class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
          </div>

          <!-- Description -->
          <div>
            <label for="jobDescription" class="block text-sm font-medium text-gray-700">Description</label>
            <textarea id="jobDescription" v-model="form.description" rows="3"
                      class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"></textarea>
          </div>

           <!-- Tags (Multi-select) -->
          <div>
            <label for="jobTags" class="block text-sm font-medium text-gray-700">Target Tags</label>
            <select id="jobTags" v-model="form.tag_ids" multiple required
                    class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm h-24">
              <option v-if="tagStore.isLoading">Loading tags...</option>
              <option v-for="tag in tagStore.tags" :key="tag.id" :value="tag.id">
                {{ tag.name }}
              </option>
            </select>
             <p v-if="tagStore.error" class="text-xs text-red-600 mt-1">{{ tagStore.error }}</p>
          </div>

          <!-- Is Enabled -->
          <div class="flex items-center">
            <input id="is_enabled" type="checkbox" v-model="form.is_enabled"
                   class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500">
            <label for="is_enabled" class="ml-2 block text-sm text-gray-900">Enabled</label>
          </div>

          <!-- Schedule Type -->
          <div>
            <label for="scheduleType" class="block text-sm font-medium text-gray-700">Schedule Type</label>
            <select id="scheduleType" v-model="form.schedule_type" required
                    class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
              <option value="interval">Interval</option>
              <option value="cron">Cron</option>
              <!-- <option value="onetime">One Time</option> -->
              <!-- Add other types if supported -->
            </select>
          </div>

          <!-- Interval Seconds (Conditional) -->
          <div v-if="form.schedule_type === 'interval'">
            <label for="intervalSeconds" class="block text-sm font-medium text-gray-700">Interval (seconds)</label>
            <input type="number" id="intervalSeconds" v-model.number="form.interval_seconds" min="1" required
                   class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
          </div>

          <!-- Cron String (Conditional) -->
          <div v-if="form.schedule_type === 'cron'">
            <label for="cronString" class="block text-sm font-medium text-gray-700">Cron String</label>
            <input type="text" id="cronString" v-model="form.cron_string" placeholder="e.g., 0 2 * * *" required
                   class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
             <p class="text-xs text-gray-500 mt-1">Standard cron format (min hour day month weekday)</p>
          </div>

        </div>
      </form>
    </template>
    <template #actions>
       <button
        type="button"
        :disabled="isSaving"
        class="inline-flex justify-center rounded-md border border-transparent bg-blue-100 px-4 py-2 text-sm font-medium text-blue-900 hover:bg-blue-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
        @click="submitForm"
      >
        {{ isSaving ? 'Saving...' : 'Save Job' }}
      </button>
      <button
        type="button"
        class="inline-flex justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
        @click="closeModal"
      >
        Cancel
      </button>
    </template>
  </BaseModal>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue';
import BaseModal from './BaseModal.vue';
import { useTagStore } from '../store/tag';

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true,
  },
  jobToEdit: {
    type: Object,
    default: null // null indicates create mode
  }
});

const emit = defineEmits(['close', 'save']);

const tagStore = useTagStore();
const isSaving = ref(false);

// Initialize form reactive object
const form = ref({
    id: null,
    name: '',
    description: '',
    tag_ids: [], // Array of selected tag IDs
    is_enabled: true,
    schedule_type: 'interval', // Default schedule type
    interval_seconds: 3600, // Default interval
    cron_string: ''
});

const modalTitle = computed(() => props.jobToEdit ? 'Edit Job' : 'Create New Job');

// Watch for the modal opening or jobToEdit changing
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    resetForm();
    // Fetch tags if they haven't been loaded
    if (tagStore.tags.length === 0) {
        tagStore.fetchTags();
    }
  }
});

// Function to reset form state
function resetForm() {
    if (props.jobToEdit) {
        // Edit mode: Populate form from jobToEdit
        form.value.id = props.jobToEdit.id;
        form.value.name = props.jobToEdit.name;
        form.value.description = props.jobToEdit.description || '';
        form.value.tag_ids = props.jobToEdit.tags ? props.jobToEdit.tags.map(tag => tag.id) : [];
        form.value.is_enabled = props.jobToEdit.is_enabled;
        form.value.schedule_type = props.jobToEdit.schedule_type || 'interval';
        form.value.interval_seconds = props.jobToEdit.interval_seconds || null;
        form.value.cron_string = props.jobToEdit.cron_string || '';
    } else {
        // Create mode: Reset to defaults
        form.value.id = null;
        form.value.name = '';
        form.value.description = '';
        form.value.tag_ids = [];
        form.value.is_enabled = true;
        form.value.schedule_type = 'interval';
        form.value.interval_seconds = 3600;
        form.value.cron_string = '';
    }
     isSaving.value = false; // Reset saving state
}


function closeModal() {
  emit('close');
}

async function submitForm() {
  // Basic validation
  if (!form.value.name || form.value.tag_ids.length === 0) {
    alert('Please provide a Job Name and select at least one Target Tag.');
    return;
  }
  if (form.value.schedule_type === 'interval' && (!form.value.interval_seconds || form.value.interval_seconds < 1)) {
    alert('Please provide a valid Interval (positive number of seconds).');
    return;
  }
   if (form.value.schedule_type === 'cron' && !form.value.cron_string) {
    alert('Please provide a valid Cron String.');
    return;
  }

  isSaving.value = true;
  try {
    // Prepare payload, ensuring nulls for non-applicable schedule fields
    const payload = {
        ...form.value,
        interval_seconds: form.value.schedule_type === 'interval' ? form.value.interval_seconds : null,
        cron_string: form.value.schedule_type === 'cron' ? form.value.cron_string : null,
    };
    // Remove id if it's null (for create operation)
    if (payload.id === null) {
        delete payload.id;
    }

    await emit('save', payload);
    // Parent should handle closing on success
  } catch (error) {
    console.error("Error saving job:", error);
    alert('Failed to save job. Check console for details.'); // User feedback
  } finally {
    isSaving.value = false;
  }
}

// Fetch initial tags if needed
onMounted(() => {
    if (tagStore.tags.length === 0) {
        // tagStore.fetchTags(); // Optional pre-fetch
    }
})

</script> 