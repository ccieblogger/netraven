<template>
  <BaseModal :is-open="isOpen" :title="`Confirm Deletion`" @close="closeModal">
    <template #content>
      <p class="text-sm text-gray-500">
        Are you sure you want to delete the {{ itemType }} "<strong>{{ itemName }}</strong>"?
        This action cannot be undone.
      </p>
    </template>
    <template #actions>
      <button
        type="button"
        class="inline-flex justify-center rounded-md border border-transparent bg-red-100 px-4 py-2 text-sm font-medium text-red-900 hover:bg-red-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2"
        @click="confirmDelete"
      >
        Delete
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
import BaseModal from './BaseModal.vue';

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true,
  },
  itemType: {
    type: String,
    required: true,
    default: 'item'
  },
  itemName: {
    type: String,
    required: true,
    default: ''
  }
});

const emit = defineEmits(['close', 'confirm']);

function closeModal() {
  emit('close');
}

function confirmDelete() {
  emit('confirm');
  // Optionally close the modal after confirm, or let the parent handle it
  // closeModal();
}
</script> 