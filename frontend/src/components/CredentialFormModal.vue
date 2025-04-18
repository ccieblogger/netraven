<template>
  <BaseModal :is-open="isOpen" :title="modalTitle" @close="closeModal">
    <template #content>
      <form @submit.prevent="submitForm" class="space-y-4">
        <!-- Error Banner -->
        <div v-if="generalError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded mb-2">
          {{ generalError }}
        </div>
        <!-- Username -->
        <FormField
          id="username"
          v-model="form.username"
          label="Username"
          type="text"
          required
          :error="validationErrors.username"
          placeholder="e.g., admin"
        />
        <!-- Password (write-only) -->
        <FormField
          v-if="!isEditMode || showPasswordField"
          id="password"
          v-model="form.password"
          label="Password"
          type="password"
          :required="!isEditMode"
          :error="validationErrors.password"
          placeholder="Enter password"
        />
        <button
          v-if="isEditMode && !showPasswordField"
          type="button"
          class="text-xs text-blue-600 underline"
          @click="showPasswordField = true"
        >
          Change password
        </button>
        <!-- Priority -->
        <FormField
          id="priority"
          v-model.number="form.priority"
          label="Priority"
          type="number"
          :min="1"
          :max="1000"
          :error="validationErrors.priority"
          help-text="Lower numbers are higher priority (default: 100)"
        />
        <!-- Description -->
        <FormField
          id="description"
          v-model="form.description"
          label="Description"
          type="text"
          :error="validationErrors.description"
          placeholder="Optional description"
        />
        <!-- Tags (multi-select) -->
        <TagSelector
          id="tags"
          v-model="form.tags"
          label="Tags"
          :error="validationErrors.tags"
          help-text="Associate tags with this credential"
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
        {{ isSaving ? 'Saving...' : (isEditMode ? 'Update' : 'Save') }}
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

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true,
  },
  credentialToEdit: {
    type: Object,
    default: null, // null indicates create mode
  },
  backendError: {
    type: String,
    default: '',
  },
});

const emit = defineEmits(['close', 'save']);

const isSaving = ref(false);
const validationErrors = ref({});
const generalError = ref("");
const showPasswordField = ref(false);

const form = ref({
  id: null,
  username: '',
  password: '',
  priority: 100,
  description: '',
  tags: [], // Array of tag IDs
});

const isEditMode = computed(() => !!props.credentialToEdit);
const modalTitle = computed(() => isEditMode.value ? 'Edit Credential' : 'Add Credential');

function setFormFromProps() {
  if (props.credentialToEdit && Object.keys(props.credentialToEdit).length > 0) {
    form.value = {
      id: props.credentialToEdit.id,
      username: props.credentialToEdit.username || '',
      password: '', // Always blank for edit
      priority: props.credentialToEdit.priority ?? 100,
      description: props.credentialToEdit.description || '',
      tags: (props.credentialToEdit.tags || []).map(t => t.id),
    };
    showPasswordField.value = false;
  } else {
    form.value = { id: null, username: '', password: '', priority: 100, description: '', tags: [] };
    showPasswordField.value = false;
  }
}

onMounted(() => {
  setFormFromProps();
});

watch(() => props.credentialToEdit, () => {
  setFormFromProps();
}, { immediate: true });

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    setFormFromProps();
    clearValidationErrors();
    generalError.value = props.backendError || "";
  }
});

function clearValidationErrors() {
  validationErrors.value = {};
  generalError.value = '';
}

function validateForm() {
  const errors = {};
  if (!form.value.username || !form.value.username.trim()) {
    errors.username = 'Username is required.';
  }
  if (!isEditMode.value || showPasswordField.value) {
    if (!form.value.password || !form.value.password.trim()) {
      errors.password = 'Password is required.';
    }
  }
  if (form.value.priority && (form.value.priority < 1 || form.value.priority > 1000)) {
    errors.priority = 'Priority must be between 1 and 1000.';
  }
  // tags is optional
  validationErrors.value = errors;
  return Object.keys(errors).length === 0;
}

function closeModal() {
  emit('close');
}

function submitForm() {
  clearValidationErrors();
  if (!validateForm()) return;
  isSaving.value = true;
  // Emit only the necessary fields
  const payload = {
    username: form.value.username,
    priority: form.value.priority,
    description: form.value.description,
    tags: form.value.tags,
  };
  if (!isEditMode.value || showPasswordField.value) {
    payload.password = form.value.password;
  }
  if (isEditMode.value) {
    payload.id = form.value.id;
  }
  emit('save', payload);
  isSaving.value = false;
}
</script>

<style scoped>
/* Add any modal-specific styles here */
</style> 