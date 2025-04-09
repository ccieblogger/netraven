<template>
  <div class="credential-selector">
    <label :for="id" class="block text-sm font-medium text-gray-700">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    
    <div class="mt-1 relative">
      <div
        :class="[
          'flex items-center w-full rounded-md shadow-sm border p-2',
          error ? 'border-red-300 focus-within:border-red-500 focus-within:ring-red-500' 
                : 'border-gray-300 focus-within:border-indigo-500 focus-within:ring-indigo-500',
          disabled ? 'bg-gray-100 cursor-not-allowed' : ''
        ]"
        @click="toggleDropdown"
      >
        <!-- Selected credential or placeholder -->
        <div class="flex-grow truncate text-sm">
          <div v-if="selectedCredential" class="flex items-center">
            <KeyIcon class="h-4 w-4 text-gray-500 mr-2" />
            <span class="font-medium">{{ selectedCredential.name }}</span>
            <span class="ml-2 text-gray-500">({{ selectedCredential.username }})</span>
          </div>
          <div v-else class="text-gray-500">{{ placeholder }}</div>
        </div>
        
        <!-- Dropdown arrow -->
        <div class="ml-2">
          <ChevronDownIcon 
            class="h-5 w-5 text-gray-400"
            :class="{ 'transform rotate-180': isDropdownOpen }"
          />
        </div>
      </div>

      <!-- Dropdown -->
      <div
        v-if="isDropdownOpen && !disabled"
        class="absolute z-10 mt-1 w-full bg-white shadow-lg rounded-md border border-gray-300 py-1 max-h-60 overflow-auto"
      >
        <div v-if="loading" class="px-4 py-2 text-sm text-gray-500">
          Loading credentials...
        </div>
        <div v-else-if="credentials.length === 0" class="px-4 py-2 text-sm text-gray-500">
          No credentials found
        </div>
        <ul v-else role="listbox">
          <!-- Option to unselect credential -->
          <li
            v-if="allowClear && selectedId"
            @click="selectCredential(null)"
            class="px-4 py-2 text-sm text-gray-700 hover:bg-indigo-50 cursor-pointer flex items-center"
          >
            <span class="text-gray-500">-- None --</span>
          </li>
          
          <!-- Credential options -->
          <li
            v-for="credential in credentials"
            :key="credential.id"
            @click="selectCredential(credential)"
            class="px-4 py-2 text-sm hover:bg-indigo-50 cursor-pointer"
            :class="{ 
              'bg-indigo-50': selectedId === credential.id,
              'text-gray-900': selectedId !== credential.id,
              'text-indigo-700 font-medium': selectedId === credential.id
            }"
            role="option"
          >
            <div class="flex items-center">
              <KeyIcon class="h-4 w-4 mr-2" :class="selectedId === credential.id ? 'text-indigo-500' : 'text-gray-500'" />
              <span>{{ credential.name }}</span>
              <span class="ml-2 text-xs" :class="selectedId === credential.id ? 'text-indigo-400' : 'text-gray-500'">
                ({{ credential.username }})
              </span>
            </div>
            
            <!-- Tags if available -->
            <div v-if="credential.tags && credential.tags.length > 0" class="ml-6 mt-1 flex flex-wrap gap-1">
              <span 
                v-for="tag in credential.tags" 
                :key="tag.id"
                class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
              >
                {{ tag.name }}
              </span>
            </div>
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
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { ChevronDownIcon, KeyIcon } from '@heroicons/vue/20/solid';
import { useCredentialStore } from '../store/credential';

const props = defineProps({
  id: {
    type: String,
    required: true
  },
  modelValue: {
    type: Number,
    default: null
  },
  label: {
    type: String,
    required: true
  },
  placeholder: {
    type: String,
    default: 'Select credentials...'
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
  },
  allowClear: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(['update:modelValue']);

const credentialStore = useCredentialStore();
const isDropdownOpen = ref(false);
const selectorRef = ref(null);

// Computed properties
const loading = computed(() => credentialStore.isLoading);
const credentials = computed(() => credentialStore.credentials);
const selectedId = computed(() => props.modelValue);

const selectedCredential = computed(() => {
  if (selectedId.value === null) return null;
  return credentials.value.find(c => c.id === selectedId.value) || null;
});

// Methods
function toggleDropdown() {
  if (!props.disabled) {
    isDropdownOpen.value = !isDropdownOpen.value;
  }
}

function selectCredential(credential) {
  if (props.disabled) return;
  
  emit('update:modelValue', credential ? credential.id : null);
  isDropdownOpen.value = false;
}

// Handle click outside to close dropdown
function handleClickOutside(event) {
  if (isDropdownOpen.value && selectorRef.value && !selectorRef.value.contains(event.target)) {
    isDropdownOpen.value = false;
  }
}

// Lifecycle hooks
onMounted(() => {
  // Fetch credentials if not already loaded
  if (credentials.value.length === 0 && !loading.value) {
    credentialStore.fetchCredentials();
  }
  
  selectorRef.value = document.querySelector('.credential-selector');
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style scoped>
/* Any additional styling can go here */
</style> 