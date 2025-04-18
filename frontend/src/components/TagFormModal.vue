<template>
  <BaseModal :is-open="isOpen" :title="modalTitle" @close="closeModal">
    <template #content>
      <form @submit.prevent="submitForm" class="space-y-4">
        <!-- Error Banner -->
        <div v-if="generalError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded mb-2">
          {{ generalError }}
        </div>
        <!-- Tag Name -->
        <FormField
          id="tag_name"
          v-model="form.name"
          label="Tag Name"
          type="text"
          required
          :error="validationErrors.name"
          placeholder="e.g., production"
        />
        <!-- Tag Type (optional) -->
        <FormField
          id="tag_type"
          v-model="form.type"
          label="Tag Type"
          type="text"
          :error="validationErrors.type"
          placeholder="e.g., environment"
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
// TagFormModal.vue
// Props:
//   isOpen (Boolean, required): Whether the modal is open
//   tagToEdit (Object|null, default null): Tag object for edit mode, or null for create
// Emits:
//   'close' - when modal is closed
//   'save' (tagData) - when form is submitted
import { ref, watch, computed, onMounted } from 'vue';
import BaseModal from './BaseModal.vue';
import FormField from './FormField.vue';

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true,
  },
  tagToEdit: {
    type: Object,
    default: null,
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

const form = ref({
  id: null,
  name: '',
  type: '',
});

const isEditMode = computed(() => !!props.tagToEdit);
const modalTitle = computed(() => isEditMode.value ? 'Edit Tag' : 'Add Tag');

function setFormFromProps() {
  if (props.tagToEdit && Object.keys(props.tagToEdit).length > 0) {
    form.value = { ...props.tagToEdit };
  } else {
    form.value = { id: null, name: '', type: '' };
  }
}

onMounted(() => {
  setFormFromProps();
});

watch(() => props.tagToEdit, () => {
  setFormFromProps();
}, { immediate: true });

function clearValidationErrors() {
  validationErrors.value = {};
  generalError.value = '';
}

function validateForm() {
  const errors = {};
  if (!form.value.name || !form.value.name.trim()) {
    errors.name = 'Tag name is required.';
  }
  // Add more validation as needed
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
  // Simulate async save (integration with store will be added in next phase)
  setTimeout(() => {
    isSaving.value = false;
    emit('save', { ...form.value });
  }, 300);
}
</script>

<style scoped>
/* Add any modal-specific styles here */
</style> 