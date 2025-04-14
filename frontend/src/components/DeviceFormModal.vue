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
          type="select"
          required
          :error="validationErrors.device_type"
          help-text="Netmiko device type"
        >
          <option value="">Select a device type</option>
          <option value="cisco_ios">cisco_ios</option>
          <option value="cisco_xe">cisco_xe</option>
          <option value="cisco_nxos">cisco_nxos</option>
          <option value="cisco_asa">cisco_asa</option>
          <option value="cisco_xr">cisco_xr</option>
          <option value="juniper_junos">juniper_junos</option>
          <option value="arista_eos">arista_eos</option>
          <option value="hp_comware">hp_comware</option>
          <option value="hp_procurve">hp_procurve</option>
          <option value="huawei">huawei</option>
          <option value="fortinet">fortinet</option>
          <option value="paloalto_panos">paloalto_panos</option>
          <option value="f5_tmsh">f5_tmsh</option>
          <option value="linux">linux</option>
          <option value="dell_os10">dell_os10</option>
          <option value="dell_os6">dell_os6</option>
          <option value="dell_os9">dell_os9</option>
        </FormField>

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
        <!--
        <CredentialSelector
          id="credential"
          v-model="form.credential_id"
          label="Credential"
          required
          :error="validationErrors.credential_id"
          help-text="Credentials used to access this device"
        />
        -->

        <!-- Add this explanation instead -->
        <div class="mt-4 bg-blue-50 p-3 rounded text-sm text-blue-800">
          <h4 class="font-medium">About Credentials</h4>
          <p>Device credentials are assigned automatically through tags. Select appropriate tags above to associate credentials with this device.</p>
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
  
  // Remove credential validation since we're using tag-based credential matching
  // No longer need to validate credential_id
  
  validationErrors.value = errors;
  return Object.keys(errors).length === 0;
}

function closeModal() {
  emit('close');
}

function submitForm() {
  clearValidationErrors();
  
  if (!validateForm()) {
    return;
  }
  
  isSaving.value = true;
  
  // Remove credential_id from the form data
  const formData = { ...form.value };
  delete formData.credential_id; // Remove direct credential selection
  
  emit('save', formData);
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