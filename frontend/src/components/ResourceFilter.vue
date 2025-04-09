<template>
  <div class="bg-white shadow sm:rounded-lg mb-6">
    <div class="p-4 sm:p-6">
      <h3 class="text-base font-semibold leading-6 text-gray-900">
        {{ title }}
      </h3>
      
      <!-- Filter form -->
      <div class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="field in filterFields" :key="field.name" class="col-span-1">
          <label :for="field.name" class="block text-sm font-medium text-gray-700">
            {{ field.label }}
          </label>
          
          <!-- Text input -->
          <input 
            v-if="field.type === 'text'"
            :id="field.name"
            v-model="filterValues[field.name]"
            type="text"
            :placeholder="field.placeholder || ''"
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
          
          <!-- Number input -->
          <input 
            v-else-if="field.type === 'number'"
            :id="field.name"
            v-model.number="filterValues[field.name]"
            type="number"
            :min="field.min"
            :max="field.max"
            :step="field.step || 1"
            :placeholder="field.placeholder || ''"
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
          
          <!-- Select input -->
          <select
            v-else-if="field.type === 'select'"
            :id="field.name"
            v-model="filterValues[field.name]"
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            <option value="">{{ field.placeholder || 'Select an option' }}</option>
            <option 
              v-for="option in field.options" 
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
          
          <!-- Date input -->
          <input 
            v-else-if="field.type === 'date'"
            :id="field.name"
            v-model="filterValues[field.name]"
            type="date"
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
          
          <!-- Checkbox input -->
          <div v-else-if="field.type === 'checkbox'" class="mt-2">
            <div class="flex items-center">
              <input 
                :id="field.name"
                v-model="filterValues[field.name]"
                type="checkbox"
                class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <label :for="field.name" class="ml-2 block text-sm text-gray-900">
                {{ field.checkboxLabel || field.label }}
              </label>
            </div>
          </div>
          
          <!-- Radio group -->
          <div v-else-if="field.type === 'radio'" class="mt-2">
            <div v-for="option in field.options" :key="option.value" class="flex items-center">
              <input 
                :id="`${field.name}-${option.value}`"
                v-model="filterValues[field.name]"
                type="radio"
                :value="option.value"
                class="h-4 w-4 border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <label :for="`${field.name}-${option.value}`" class="ml-2 block text-sm text-gray-900">
                {{ option.label }}
              </label>
            </div>
          </div>
          
          <!-- Multi-select (checkboxes) -->
          <div v-else-if="field.type === 'multiselect'" class="mt-2">
            <div v-for="option in field.options" :key="option.value" class="flex items-center">
              <input 
                :id="`${field.name}-${option.value}`"
                v-model="multiSelectValues[field.name]"
                type="checkbox"
                :value="option.value"
                class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                @change="updateMultiSelectFilter(field.name)"
              />
              <label :for="`${field.name}-${option.value}`" class="ml-2 block text-sm text-gray-900">
                {{ option.label }}
              </label>
            </div>
          </div>
          
          <!-- Help text if provided -->
          <p v-if="field.helpText" class="mt-1 text-sm text-gray-500">
            {{ field.helpText }}
          </p>
        </div>
      </div>
      
      <!-- Action buttons -->
      <div class="mt-5 flex justify-end">
        <button
          type="button"
          @click="resetFilters"
          class="rounded-md border border-gray-300 bg-white py-2 px-4 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 mr-3"
        >
          Reset
        </button>
        <button
          type="button"
          @click="applyFilters"
          class="inline-flex justify-center rounded-md border border-transparent bg-indigo-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          Apply Filters
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue';

const props = defineProps({
  title: {
    type: String,
    default: 'Filter',
  },
  filterFields: {
    type: Array,
    required: true,
    // Each field should have: name, label, type, and other type-specific properties
    // e.g. { name: 'status', label: 'Status', type: 'select', options: [...], placeholder: '...' }
  },
  initialFilters: {
    type: Object,
    default: () => ({}),
  },
  applyOnMount: {
    type: Boolean,
    default: false,
  },
  applyOnChange: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['filter', 'reset']);

// Initialize filter values
const filterValues = reactive({});
const multiSelectValues = reactive({});

// Initialize the filter values on component creation
onMounted(() => {
  initializeFilters();
  
  if (props.applyOnMount) {
    applyFilters();
  }
});

// Watch for changes in initialFilters
watch(() => props.initialFilters, (newFilters) => {
  initializeFilters();
}, { deep: true });

// Watch for changes in filter values if applyOnChange is true
watch(filterValues, () => {
  if (props.applyOnChange) {
    applyFilters();
  }
}, { deep: true });

// Initialize filter values from props or with defaults based on field type
function initializeFilters() {
  // Initialize filter values
  props.filterFields.forEach(field => {
    // Handle initial value from props if available
    if (props.initialFilters && props.initialFilters[field.name] !== undefined) {
      filterValues[field.name] = props.initialFilters[field.name];
    } else {
      // Set default values based on field type
      switch (field.type) {
        case 'checkbox':
          filterValues[field.name] = false;
          break;
        case 'multiselect':
          filterValues[field.name] = [];
          // Initialize the multiSelectValues object with an empty array
          multiSelectValues[field.name] = props.initialFilters[field.name] || [];
          break;
        case 'number':
          filterValues[field.name] = null;
          break;
        default:
          filterValues[field.name] = '';
      }
    }
  });
}

// Update multi-select filter values
function updateMultiSelectFilter(fieldName) {
  filterValues[fieldName] = [...multiSelectValues[fieldName]];
}

// Apply filters
function applyFilters() {
  // Create a filtered object with only non-empty values
  const filters = {};
  
  for (const [key, value] of Object.entries(filterValues)) {
    // Skip empty values, empty arrays, and falsy values (except boolean false)
    if (value === null || value === undefined || value === '') continue;
    if (Array.isArray(value) && value.length === 0) continue;
    
    filters[key] = value;
  }
  
  emit('filter', filters);
}

// Reset all filters
function resetFilters() {
  props.filterFields.forEach(field => {
    switch (field.type) {
      case 'checkbox':
        filterValues[field.name] = false;
        break;
      case 'multiselect':
        filterValues[field.name] = [];
        multiSelectValues[field.name] = [];
        break;
      case 'number':
        filterValues[field.name] = null;
        break;
      default:
        filterValues[field.name] = '';
    }
  });
  
  emit('reset');
  
  // Also apply the reset filters if applyOnChange is true
  if (props.applyOnChange) {
    applyFilters();
  }
}
</script> 