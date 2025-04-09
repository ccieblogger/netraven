<template>
  <div class="tag-selector">
    <label :for="id" class="block text-sm font-medium text-gray-700">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    
    <div class="mt-1 relative">
      <div
        :class="[
          'w-full flex flex-wrap gap-2 p-2 min-h-[40px] rounded-md shadow-sm border',
          error ? 'border-red-300 focus-within:border-red-500 focus-within:ring-red-500' 
                : 'border-gray-300 focus-within:border-indigo-500 focus-within:ring-indigo-500',
          disabled ? 'bg-gray-100 cursor-not-allowed' : '',
        ]"
        @click="focusInput"
      >
        <!-- Selected Tags Pills -->
        <span 
          v-for="tag in selectedTags" 
          :key="tag.id"
          class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
        >
          {{ tag.name }}
          <button
            type="button"
            @click.stop="removeTag(tag)"
            :disabled="disabled"
            class="ml-1 text-blue-400 hover:text-blue-600 focus:outline-none"
          >
            <XMarkIcon class="h-3 w-3" />
          </button>
        </span>

        <!-- Search Input -->
        <input
          :id="id"
          ref="inputRef"
          type="text"
          v-model="searchTerm"
          @focus="isDropdownOpen = true"
          @input="handleInput"
          :placeholder="selectedTags.length ? '' : placeholder"
          :disabled="disabled"
          class="focus:outline-none flex-grow min-w-[60px] bg-transparent border-0 p-0.5"
        />
      </div>

      <!-- Dropdown with filterable options -->
      <div
        v-if="isDropdownOpen && !disabled"
        class="absolute z-10 mt-1 w-full bg-white shadow-lg rounded-md border border-gray-300 py-1 max-h-60 overflow-auto"
      >
        <div v-if="loading" class="px-4 py-2 text-sm text-gray-500">
          Loading tags...
        </div>
        <div v-else-if="availableTags.length === 0" class="px-4 py-2 text-sm text-gray-500">
          No tags found
        </div>
        <ul v-else role="listbox">
          <li
            v-for="tag in availableTags"
            :key="tag.id"
            @click="selectTag(tag)"
            class="px-4 py-2 text-sm text-gray-900 hover:bg-indigo-50 cursor-pointer"
            :class="{ 'bg-indigo-50': isSelected(tag.id) }"
            role="option"
          >
            {{ tag.name }}
            <span v-if="tag.type" class="ml-2 text-xs text-gray-500">({{ tag.type }})</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- Error Message Display -->
    <p v-if="error" class="mt-2 text-sm text-red-600">{{ error }}</p>
    
    <!-- Help Text -->
    <p v-if="helpText && !error" class="mt-2 text-sm text-gray-500">{{ helpText }}</p>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { XMarkIcon } from '@heroicons/vue/20/solid';
import { useTagStore } from '../store/tag';

const props = defineProps({
  id: {
    type: String,
    required: true
  },
  modelValue: {
    type: Array,
    default: () => []
  },
  label: {
    type: String,
    required: true
  },
  placeholder: {
    type: String,
    default: 'Select or search tags...'
  },
  required: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  helpText: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['update:modelValue']);

const tagStore = useTagStore();
const searchTerm = ref('');
const isDropdownOpen = ref(false);
const inputRef = ref(null);

// Computed properties
const loading = computed(() => tagStore.isLoading);
const tags = computed(() => tagStore.tags);

const selectedTags = computed(() => {
  return props.modelValue.map(id => 
    tags.value.find(tag => tag.id === id)
  ).filter(tag => tag); // Filter out any undefined (tag not found)
});

const availableTags = computed(() => {
  // Filter tags based on search term and exclude already selected tags
  return tags.value.filter(tag => {
    const matchesSearch = !searchTerm.value || 
      tag.name.toLowerCase().includes(searchTerm.value.toLowerCase());
    return matchesSearch && !isSelected(tag.id);
  });
});

// Methods
function handleInput() {
  if (!isDropdownOpen.value) {
    isDropdownOpen.value = true;
  }
}

function focusInput() {
  if (!props.disabled && inputRef.value) {
    inputRef.value.focus();
  }
}

function isSelected(tagId) {
  return props.modelValue.includes(tagId);
}

function selectTag(tag) {
  if (props.disabled) return;
  
  const newValue = [...props.modelValue];
  if (!newValue.includes(tag.id)) {
    newValue.push(tag.id);
    emit('update:modelValue', newValue);
  }
  
  // Clear search and keep dropdown open
  searchTerm.value = '';
  inputRef.value?.focus();
}

function removeTag(tag) {
  if (props.disabled) return;
  
  const newValue = props.modelValue.filter(id => id !== tag.id);
  emit('update:modelValue', newValue);
}

// Handle click outside to close dropdown
function handleClickOutside(event) {
  if (isDropdownOpen.value && inputRef.value && !inputRef.value.contains(event.target)) {
    isDropdownOpen.value = false;
  }
}

// Lifecycle hooks
onMounted(() => {
  // Fetch tags if not already loaded
  if (tags.value.length === 0) {
    tagStore.fetchTags();
  }
  
  // Add event listener for click outside
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style scoped>
/* Any additional styling can go here */
</style> 