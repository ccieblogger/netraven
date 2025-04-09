<template>
  <BaseModal :is-open="isOpen" :title="modalTitle" @close="closeModal">
    <template #content>
      <form @submit.prevent="submitForm">
        <div class="space-y-4">
          <!-- Hostname -->
          <div>
            <label for="hostname" class="block text-sm font-medium text-gray-700">Hostname</label>
            <input type="text" id="hostname" v-model="form.hostname" required
                   class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
            <!-- Add validation error display if needed -->
          </div>

          <!-- IP Address -->
          <div>
            <label for="ip_address" class="block text-sm font-medium text-gray-700">IP Address</label>
            <input type="text" id="ip_address" v-model="form.ip_address" required
                   pattern="^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
                   title="Enter a valid IPv4 address"
                   class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
          </div>

          <!-- Device Type (Example - adapt based on actual types) -->
           <div>
            <label for="device_type" class="block text-sm font-medium text-gray-700">Device Type</label>
            <input type="text" id="device_type" v-model="form.device_type" required placeholder="e.g., cisco_ios, junos"
                   class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
          </div>

          <!-- Port -->
          <div>
            <label for="port" class="block text-sm font-medium text-gray-700">Port</label>
            <input type="number" id="port" v-model.number="form.port" min="1" max="65535"
                   class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
          </div>

          <!-- Tags (Multi-select example using basic select) -->
          <div>
            <label for="tags" class="block text-sm font-medium text-gray-700">Tags</label>
            <select id="tags" v-model="form.tag_ids" multiple
                    class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm h-24">
              <option v-if="tagStore.isLoading">Loading tags...</option>
              <option v-for="tag in tagStore.tags" :key="tag.id" :value="tag.id">
                {{ tag.name }}
              </option>
            </select>
             <p v-if="tagStore.error" class="text-xs text-red-600 mt-1">{{ tagStore.error }}</p>
          </div>

          <!-- Credentials (Dropdown) -->
          <div>
            <label for="credential" class="block text-sm font-medium text-gray-700">Credentials</label>
            <select id="credential" v-model="form.credential_id" required
                    class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
              <option v-if="credentialStore.isLoading">Loading credentials...</option>
              <option :value="null">-- Select Credentials --</option> <!-- Allow unsetting -->
              <option v-for="cred in credentialStore.credentials" :key="cred.id" :value="cred.id">
                {{ cred.name }} ({{ cred.username }})
              </option>
            </select>
            <p v-if="credentialStore.error" class="text-xs text-red-600 mt-1">{{ credentialStore.error }}</p>
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
import { useTagStore } from '../store/tag';
import { useCredentialStore } from '../store/credential';

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

const isSaving = ref(false);

// Initialize form reactive object
const form = ref({
    id: null,
    hostname: '',
    ip_address: '',
    device_type: '',
    port: 22, // Default SSH port
    tag_ids: [], // Store array of selected tag IDs
    credential_id: null,
});

const modalTitle = computed(() => props.deviceToEdit ? 'Edit Device' : 'Create New Device');

// Watch for the modal opening or deviceToEdit changing
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    resetForm();
    // Fetch tags and credentials if they haven't been loaded
    if (tagStore.tags.length === 0) {
        tagStore.fetchTags();
    }
    if (credentialStore.credentials.length === 0) {
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
    }
    isSaving.value = false; // Reset saving state
}


function closeModal() {
  emit('close');
}

async function submitForm() {
  // Basic validation example (can be expanded)
  if (!form.value.hostname || !form.value.ip_address || !form.value.device_type || !form.value.credential_id) {
    alert('Please fill in all required fields.'); // Replace with better validation feedback
    return;
  }

  isSaving.value = true;
  try {
    // Prepare payload - ensure credential_id is null if not selected, not undefined
    const payload = {
        ...form.value,
        credential_id: form.value.credential_id || null
    };
    // Remove id if it's null (for create operation)
    if (payload.id === null) {
        delete payload.id;
    }

    await emit('save', payload);
    // Parent component should close modal on successful save
    // closeModal();
  } catch (error) {
    console.error("Error saving device:", error);
    alert('Failed to save device. Check console for details.'); // User feedback
  } finally {
    isSaving.value = false;
  }
}

// Fetch initial data if stores are empty (e.g., on component mount if modal could be initially open)
// Although fetching in the watch(isOpen) is generally preferred for modals
onMounted(() => {
    if (tagStore.tags.length === 0) {
        // tagStore.fetchTags(); // Can optionally pre-fetch
    }
     if (credentialStore.credentials.length === 0) {
        // credentialStore.fetchCredentials(); // Can optionally pre-fetch
    }
})

</script> 