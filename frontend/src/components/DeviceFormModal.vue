<template>
  <BaseModal :is-open="isOpen" :title="modalTitle" @close="closeModal">
    <template #content>
      <form @submit.prevent="submitForm" class="space-y-4">
        <!-- Hostname -->
        <FormField
          id="hostname"
          v-model="form.hostname"
          label="Hostname"
          type="text"
          required
          :error="validationErrors.hostname"
          placeholder="e.g., core-switch-01"
        />

        <!-- IP Address -->
        <FormField
          id="ip_address"
          v-model="form.ip_address"
          label="IP Address"
          type="text"
          required
          :error="validationErrors.ip_address"
          placeholder="e.g., 192.168.1.1"
          pattern="^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
          help-text="IPv4 address of the device"
        />

        <!-- Device Type -->
        <FormField
          id="device_type"
          v-model="form.device_type"
          label="Device Type"
          type="text"
          required
          :error="validationErrors.device_type"
          placeholder="e.g., cisco_ios, junos"
          help-text="Netmiko device type"
        />

        <!-- Port -->
        <FormField
          id="port"
          v-model.number="form.port"
          label="Port"
          type="number"
          :min="1"
          :max="65535"
          :error="validationErrors.port"
          help-text="SSH port (default: 22)"
        />

        <!-- Description -->
        <FormField
          id="description"
          v-model="form.description"
          label="Description"
          type="text"
          :error="validationErrors.description"
          placeholder="e.g., Core Switch in Data Center 1"
          help-text="Optional description of this device"
        />

        <!-- Tags (multi-select) -->
        <TagSelector
          id="tags"
          v-model="form.tag_ids"
          label="Tags"
          :error="validationErrors.tag_ids"
          help-text="Associate tags with this device"
        />

        <!-- Credentials -->
        <!-- TEMPORARY: Direct credential selection until proper tag-based credential matching is implemented -->
        <!-- TODO: Replace with tag-based credential matching in future implementation -->
        <CredentialSelector
          id="credential"
          v-model="form.credential_id"
          label="Credential"
          required
          :error="validationErrors.credential_id"
          help-text="Credentials used to access this device"
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
        {{ isSaving ? 'Saving...' : 'Save' }}
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
import CredentialSelector from './CredentialSelector.vue';
import { useTagStore } from '../store/tag';
import { useCredentialStore } from '../store/credential';
import { useNotificationStore } from '../store/notifications';

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true,
  },
  deviceToEdit: {
    type: Object,
    default: null // null indicates create mode
  }
});

const emit = defineEmits(['close', 'save']);

const tagStore = useTagStore();
const credentialStore = useCredentialStore();
const notificationStore = useNotificationStore();

const isSaving = ref(false);
const validationErrors = ref({});

// Initialize form reactive object
const form = ref({
    id: null,
    hostname: '',
    ip_address: '',
    device_type: '',
    port: 22, // Default SSH port
    tag_ids: [], // Store array of selected tag IDs
    credential_id: null,
    description: '',
});

const modalTitle = computed(() => props.deviceToEdit ? 'Edit Device' : 'Create New Device');

// Watch for the modal opening or deviceToEdit changing
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    resetForm();
    clearValidationErrors();
    
    // Fetch tags and credentials if they haven't been loaded
    if (tagStore.tags.length === 0 && !tagStore.isLoading) {
        tagStore.fetchTags();
    }
    if (credentialStore.credentials.length === 0 && !credentialStore.isLoading) {
        credentialStore.fetchCredentials();
    }
  }
});

// Function to reset form state
function resetForm() {
    if (props.deviceToEdit) {
        // Edit mode: Populate form from deviceToEdit
        form.value.id = props.deviceToEdit.id;
        form.value.hostname = props.deviceToEdit.hostname;
        form.value.ip_address = props.deviceToEdit.ip_address;
        form.value.device_type = props.deviceToEdit.device_type;
        form.value.port = props.deviceToEdit.port || 22;
        form.value.description = props.deviceToEdit.description || '';
        // API likely returns full tag objects, we need just the IDs for the form model
        form.value.tag_ids = props.deviceToEdit.tags ? props.deviceToEdit.tags.map(tag => tag.id) : [];
        form.value.credential_id = props.deviceToEdit.credential ? props.deviceToEdit.credential.id : null;
    } else {
        // Create mode: Reset to defaults
        form.value.id = null;
        form.value.hostname = '';
        form.value.ip_address = '';
        form.value.device_type = '';
        form.value.port = 22;
        form.value.tag_ids = [];
        form.value.credential_id = null;
        form.value.description = '';
    }
    isSaving.value = false; // Reset saving state
}

function clearValidationErrors() {
  validationErrors.value = {};
}

function validateForm() {
  const errors = {};
  
  // Hostname validation
  if (!form.value.hostname) {
    errors.hostname = 'Hostname is required';
  } else if (form.value.hostname.length < 2) {
    errors.hostname = 'Hostname must be at least 2 characters';
  }
  
  // IP Address validation
  if (!form.value.ip_address) {
    errors.ip_address = 'IP address is required';
  } else if (!/^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/.test(form.value.ip_address)) {
    errors.ip_address = 'Please enter a valid IPv4 address';
  }
  
  // Device type validation
  if (!form.value.device_type) {
    errors.device_type = 'Device type is required';
  }
  
  // Port validation (optional)
  if (form.value.port !== null && (form.value.port < 1 || form.value.port > 65535)) {
    errors.port = 'Port must be between 1 and 65535';
  }
  
  // Credential validation
  if (!form.value.credential_id) {
    errors.credential_id = 'Please select credentials for this device';
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
    // Prepare payload
    const payload = {
        ...form.value,
        credential_id: form.value.credential_id || null
    };
    
    // Remove id if it's null (for create operation)
    if (payload.id === null) {
        delete payload.id;
    }

    await emit('save', payload);
    notificationStore.success(`Device ${props.deviceToEdit ? 'updated' : 'created'} successfully!`);
    // Parent component should close modal on successful save
  } catch (error) {
    console.error("Error saving device:", error);
    notificationStore.error({
      title: 'Save Failed',
      message: error.message || 'Failed to save device. Please try again.',
      duration: 0 // Make error persistent
    });
  } finally {
    isSaving.value = false;
  }
}

// Fetch initial data if needed (e.g., when modal is initially open)
onMounted(() => {
  if (props.isOpen) {
    if (tagStore.tags.length === 0 && !tagStore.isLoading) {
      tagStore.fetchTags();
    }
    if (credentialStore.credentials.length === 0 && !credentialStore.isLoading) {
      credentialStore.fetchCredentials();
    }
  }
});
</script> 