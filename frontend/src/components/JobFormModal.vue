<template>
  <BaseModal :is-open="isOpen" :title="modalTitle" @close="closeModal">
    <template #content>
      <form @submit.prevent="submitForm" class="space-y-4">
        <!-- Job Name -->
        <FormField
          id="jobName"
          v-model="form.name"
          label="Job Name"
          type="text"
          required
          :error="validationErrors.name"
          placeholder="e.g., Daily Backup"
        />

        <!-- Description -->
        <FormField
          id="jobDescription"
          v-model="form.description"
          label="Description"
          type="textarea"
          :error="validationErrors.description"
          placeholder="Enter job description..."
          help-text="Describe the purpose of this job"
        />

        <!-- Tags (Multi-select) -->
        <TagSelector
          id="jobTags"
          v-model="form.tag_ids"
          label="Target Tags"
          required
          :error="validationErrors.tag_ids"
          help-text="Select tags to determine which devices this job will run against"
        />

        <!-- Is Enabled -->
        <div class="flex items-center">
          <input 
            id="is_enabled" 
            type="checkbox" 
            v-model="form.is_enabled"
            class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
          >
          <label for="is_enabled" class="ml-2 block text-sm text-gray-900">
            Enable this job
          </label>
        </div>

        <!-- Schedule Type -->
        <FormField
          id="scheduleType"
          v-model="form.schedule_type"
          label="Schedule Type"
          type="select"
          required
          :error="validationErrors.schedule_type"
        >
          <option value="interval">Interval</option>
          <option value="cron">Cron</option>
          <option value="onetime">One Time</option>
        </FormField>

        <!-- Interval Seconds (Conditional) -->
        <FormField
          v-if="form.schedule_type === 'interval'"
          id="intervalSeconds"
          v-model.number="form.interval_seconds"
          label="Interval (seconds)"
          type="number"
          required
          :min="60"
          :error="validationErrors.interval_seconds"
          help-text="Minimum interval is 60 seconds (1 minute)"
        />

        <!-- Cron String (Conditional) -->
        <FormField
          v-if="form.schedule_type === 'cron'"
          id="cronString"
          v-model="form.cron_string"
          label="Cron Expression"
          type="text"
          required
          :error="validationErrors.cron_string"
          placeholder="e.g., 0 2 * * *"
          help-text="Standard cron format (min hour day month weekday)"
        />

        <!-- One Time Date (Conditional) -->
        <FormField
          v-if="form.schedule_type === 'onetime'"
          id="runAt"
          v-model="form.run_at"
          label="Run At"
          type="datetime-local"
          required
          :error="validationErrors.run_at"
          help-text="Select date and time to run this job"
        />
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
import FormField from './FormField.vue';
import TagSelector from './TagSelector.vue';
import { useTagStore } from '../store/tag';
import { useNotificationStore } from '../store/notifications';

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
const notificationStore = useNotificationStore();
const isSaving = ref(false);
const validationErrors = ref({});

// Initialize form reactive object
const form = ref({
    id: null,
    name: '',
    description: '',
    tag_ids: [], // Array of selected tag IDs
    is_enabled: true,
    schedule_type: 'interval', // Default schedule type
    interval_seconds: 3600, // Default interval: 1 hour
    cron_string: '',
    run_at: formatDateForInput(new Date(Date.now() + 3600000)) // Default: 1 hour from now
});

const modalTitle = computed(() => props.jobToEdit ? 'Edit Job' : 'Create New Job');

// Helper function to format date for datetime-local input
function formatDateForInput(date) {
  if (!date) return '';
  
  // Convert to ISO string and remove seconds and timezone
  return new Date(date).toISOString().slice(0, 16);
}

// Watch for the modal opening or jobToEdit changing
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    resetForm();
    clearValidationErrors();
    
    // Fetch tags if they haven't been loaded
    if (tagStore.tags.length === 0 && !tagStore.isLoading) {
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
        form.value.interval_seconds = props.jobToEdit.interval_seconds || 3600;
        form.value.cron_string = props.jobToEdit.cron_string || '';
        
        // Handle run_at for onetime jobs
        if (props.jobToEdit.run_at) {
          form.value.run_at = formatDateForInput(new Date(props.jobToEdit.run_at));
        } else {
          form.value.run_at = formatDateForInput(new Date(Date.now() + 3600000));
        }
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
        form.value.run_at = formatDateForInput(new Date(Date.now() + 3600000));
    }
    isSaving.value = false; // Reset saving state
}

function clearValidationErrors() {
  validationErrors.value = {};
}

function validateForm() {
  const errors = {};
  
  // Name validation
  if (!form.value.name) {
    errors.name = 'Job name is required';
  } else if (form.value.name.length < 3) {
    errors.name = 'Job name must be at least 3 characters';
  }
  
  // Tag validation
  if (!form.value.tag_ids || form.value.tag_ids.length === 0) {
    errors.tag_ids = 'Please select at least one target tag';
  }
  
  // Schedule type specific validation
  if (form.value.schedule_type === 'interval') {
    if (!form.value.interval_seconds) {
      errors.interval_seconds = 'Interval is required';
    } else if (form.value.interval_seconds < 60) {
      errors.interval_seconds = 'Interval must be at least 60 seconds';
    }
  } else if (form.value.schedule_type === 'cron') {
    if (!form.value.cron_string) {
      errors.cron_string = 'Cron expression is required';
    } else if (!/^(\S+\s+){4}\S+$/.test(form.value.cron_string)) {
      errors.cron_string = 'Invalid cron expression format';
    }
  } else if (form.value.schedule_type === 'onetime') {
    if (!form.value.run_at) {
      errors.run_at = 'Run date/time is required';
    } else {
      const runAtDate = new Date(form.value.run_at);
      if (isNaN(runAtDate) || runAtDate <= new Date()) {
        errors.run_at = 'Run date/time must be in the future';
      }
    }
  }
  
  validationErrors.value = errors;
  return Object.keys(errors).length === 0;
}

function closeModal() {
  emit('close');
}

async function submitForm() {
  // Validate form
  if (!validateForm()) {
    notificationStore.error('Please correct the validation errors before saving.');
    return;
  }

  isSaving.value = true;
  try {
    // Prepare payload, ensuring nulls for non-applicable schedule fields
    const payload = {
      ...form.value,
      // Set irrelevant schedule fields to null based on schedule_type
      interval_seconds: form.value.schedule_type === 'interval' ? form.value.interval_seconds : null,
      cron_string: form.value.schedule_type === 'cron' ? form.value.cron_string : null,
      run_at: form.value.schedule_type === 'onetime' ? new Date(form.value.run_at).toISOString() : null,
    };
    
    // Remove id if it's null (for create operation)
    if (payload.id === null) {
      delete payload.id;
    }

    await emit('save', payload);
    notificationStore.success(`Job ${props.jobToEdit ? 'updated' : 'created'} successfully!`);
    // Parent should handle closing on success
  } catch (error) {
    console.error("Error saving job:", error);
    notificationStore.error({
      title: 'Save Failed',
      message: error.message || 'Failed to save job. Please try again.',
      duration: 0 // Make error persistent
    });
  } finally {
    isSaving.value = false;
  }
}

// Fetch initial tags if needed
onMounted(() => {
  if (props.isOpen && tagStore.tags.length === 0 && !tagStore.isLoading) {
    tagStore.fetchTags();
  }
});
</script> 