<template>
  <BaseModal :is-open="isOpen" :title="modalTitle" @close="closeModal">
    <template #content>
      <form @submit.prevent="submitForm" class="space-y-6">
        <!-- Error Banner -->
        <div v-if="generalError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded mb-2">
          {{ generalError }}
        </div>
        <div class="bg-card-secondary rounded-lg p-4 shadow-sm">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
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
            <!-- Serial Number -->
            <FormField
              id="serial_number"
              v-model="form.serial_number"
              label="Serial Number"
              type="text"
              :error="validationErrors.serial_number"
              placeholder="e.g., SN-123456789"
              help-text="Device serial number (optional)"
            />
            <!-- Model -->
            <FormField
              id="model"
              v-model="form.model"
              label="Model"
              type="text"
              :error="validationErrors.model"
              placeholder="e.g., Catalyst 9500"
              help-text="Device model (optional)"
            />
            <!-- Source -->
            <FormField
              id="source"
              v-model="form.source"
              label="Source"
              type="select"
              :error="validationErrors.source"
              help-text="How this device was added"
            >
              <option value="local">Local</option>
              <option value="imported">Imported</option>
            </FormField>
            <!-- Tags (multi-select) -->
            <TagSelector
              id="tags"
              v-model="form.tag_ids"
              label="Tags"
              :error="validationErrors.tag_ids"
              help-text="Associate tags with this device"
            />
          </div>
          <!-- Description and Notes in full width -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            <div>
              <FormField
                id="description"
                v-model="form.description"
                label="Description"
                type="text"
                :error="validationErrors.description"
                placeholder="e.g., Core Switch in Data Center 1"
                help-text="Optional description of this device"
              />
            </div>
            <div>
              <FormField
                id="notes"
                v-model="form.notes"
                label="Notes"
                type="textarea"
                :error="validationErrors.notes"
                placeholder="Add notes or comments (markdown supported)"
                help-text="Supports markdown formatting."
                :rows="4"
              />
              <div class="text-xs text-gray-500 mb-2">You can use <a href='https://www.markdownguide.org/cheat-sheet/' target='_blank' class='underline'>Markdown</a> for formatting.</div>
              <div v-if="form.notes" class="mb-2">
                <span class="text-xs text-text-secondary">Preview:</span>
                <div class="border rounded bg-white p-2 mt-1 max-h-32 overflow-auto">
                  <MarkdownRenderer :content="form.notes" />
                </div>
              </div>
            </div>
          </div>
          <!-- Credentials Info -->
          <div class="mt-4 bg-blue-50 p-3 rounded text-sm text-blue-800">
            <h4 class="font-medium">About Credentials</h4>
            <p>Device credentials are assigned automatically through tags. Select appropriate tags above to associate credentials with this device.</p>
          </div>
          <!-- Read-only last_updated and updated_by -->
          <div v-if="form.last_updated || form.updated_by" class="flex flex-row gap-4 mt-4 text-xs text-gray-500">
            <div v-if="form.last_updated">Last Updated: {{ formatDate(form.last_updated) }}</div>
            <div v-if="form.updated_by">Updated By: {{ form.updated_by }}</div>
          </div>
        </div>
      </form>
    </template>
    <template #actions>
      <div class="flex flex-row gap-4 justify-end mt-4">
        <button
          type="button"
          :disabled="isSaving"
          class="inline-flex justify-center rounded-md border border-transparent bg-primary-600 px-6 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition"
          @click="submitForm"
        >
          {{ isSaving ? 'Saving...' : 'Save' }}
        </button>
        <button
          type="button"
          class="inline-flex justify-center rounded-md border border-gray-300 bg-white px-6 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 transition"
          @click="closeModal"
        >
          Cancel
        </button>
      </div>
    </template>
  </BaseModal>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue';
import BaseModal from './BaseModal.vue';
import FormField from './FormField.vue';
import TagSelector from './TagSelector.vue';
import CredentialSelector from './CredentialSelector.vue';
import MarkdownRenderer from './ui/MarkdownRenderer.vue';
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
  },
  backendError: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['close', 'save']);

const tagStore = useTagStore();
const credentialStore = useCredentialStore();
const notificationStore = useNotificationStore();

const isSaving = ref(false);
const validationErrors = ref({});
const generalError = ref("");

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
    serial_number: '',
    model: '',
    source: 'local',
    notes: '',
    last_updated: '',
    updated_by: '',
});

const modalTitle = computed(() => props.deviceToEdit ? 'Edit Device' : 'Create New Device');

// Watch for the modal opening or deviceToEdit changing
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    resetForm();
    clearValidationErrors();
    generalError.value = props.backendError || "";
    
    // Fetch tags and credentials if they haven't been loaded
    if (tagStore.tags.length === 0 && !tagStore.isLoading) {
        tagStore.fetchTags();
    }
    if (credentialStore.credentials.length === 0 && !credentialStore.isLoading) {
        credentialStore.fetchCredentials();
    }
  }
});

// Watch for backendError changes
watch(() => props.backendError, (newVal) => {
  if (props.isOpen) {
    generalError.value = newVal || "";
  }
});

// Helper to get the default tag ID from tagStore
function getDefaultTagId() {
  const defaultTag = tagStore.tags.find(tag => tag.name === 'default');
  return defaultTag ? defaultTag.id : null;
}

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
        form.value.serial_number = props.deviceToEdit.serial_number || '';
        form.value.model = props.deviceToEdit.model || '';
        form.value.source = props.deviceToEdit.source || 'local';
        form.value.notes = props.deviceToEdit.notes || '';
        form.value.last_updated = props.deviceToEdit.last_updated || '';
        form.value.updated_by = props.deviceToEdit.updated_by || '';
        // API likely returns full tag objects, we need just the IDs for the form model
        form.value.tag_ids = props.deviceToEdit.tags ? props.deviceToEdit.tags.map(tag => tag.id) : [];
        // Ensure default tag is always present
        const defaultTagId = getDefaultTagId();
        if (defaultTagId && !form.value.tag_ids.includes(defaultTagId)) {
          form.value.tag_ids.push(defaultTagId);
        }
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
        form.value.serial_number = '';
        form.value.model = '';
        form.value.source = 'local';
        form.value.notes = '';
        form.value.last_updated = '';
        form.value.updated_by = '';
        // Ensure default tag is always present
        const defaultTagId = getDefaultTagId();
        if (defaultTagId) {
          form.value.tag_ids.push(defaultTagId);
        }
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
  
  // Tag validation (must select at least one tag)
  if (!form.value.tag_ids || form.value.tag_ids.length === 0) {
    errors.tag_ids = 'At least one tag is required to associate credentials.';
  }
  
  validationErrors.value = errors;
  return Object.keys(errors).length === 0;
}

function closeModal() {
  emit('close');
}

async function submitForm() {
  isSaving.value = true;
  clearValidationErrors();
  generalError.value = "";
  try {
    // Validate required fields (add more as needed)
    if (!form.value.hostname) validationErrors.value.hostname = "Hostname is required.";
    if (!form.value.ip_address) validationErrors.value.ip_address = "IP address is required.";
    if (!form.value.device_type) validationErrors.value.device_type = "Device type is required.";
    if (Object.keys(validationErrors.value).length > 0) throw new Error("Validation failed");
    // Emit save event to parent (Devices.vue handles API call and error)
    emit('save', { ...form.value });
  } catch (err) {
    if (err.response && err.response.data && err.response.data.detail) {
      generalError.value = err.response.data.detail;
    } else if (typeof err === 'string') {
      generalError.value = err;
    } else {
      generalError.value = 'Failed to save device.';
    }
  } finally {
    isSaving.value = false;
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  if (isNaN(d)) return '-';
  return d.toLocaleString();
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

<style scoped>
.bg-card-secondary {
  background: var(--nr-bg-card-secondary, #f7fafc);
}
@media (max-width: 768px) {
  .grid-cols-2 {
    grid-template-columns: 1fr !important;
  }
}
</style>