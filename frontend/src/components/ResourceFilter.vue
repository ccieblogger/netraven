<template>
  <div class="bg-white shadow sm:rounded-lg mb-6">
    <div class="p-4 sm:p-6">
      <h3 class="text-base font-semibold leading-6 text-gray-900">
        {{ title }}
      </h3>
      
      <!-- Filter form -->
      <div class="mt-4 flex flex-row flex-wrap items-center justify-evenly gap-12 w-full">
        <div v-for="field in filterFields" :key="field.name" class="flex flex-col flex-1 min-w-[160px] max-w-xs">
          <label :for="field.name" class="block text-sm font-medium text-text-primary">
            {{ field.label }}
          </label>
          
          <!-- Text input -->
          <input 
            v-if="field.type === 'text'"
            :id="field.name"
            v-model="filterValues[field.name]"
            type="text"
            :placeholder="field.placeholder || ''"
            class="mt-1 block w-full rounded-md border-divider bg-card text-text-primary shadow-sm focus:border-primary focus:ring-primary sm:text-sm h-10"
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
            class="mt-1 block w-full rounded-md border-divider bg-card text-text-primary shadow-sm focus:border-primary focus:ring-primary sm:text-sm h-10"
          />
          
          <!-- Select input -->
          <div v-else-if="field.type === 'select'">
            <div v-if="getLoading(field)" class="text-xs text-gray-400 py-1">Loading...</div>
            <select
              :id="field.name"
              v-model="filterValues[field.name]"
              class="mt-1 block w-full rounded-md border-divider bg-card text-text-primary shadow-sm focus:border-primary focus:ring-primary sm:text-sm h-10"
            >
              <option value="">{{ field.placeholder || 'Select an option' }}</option>
              <option 
                v-for="option in getOptions(field)" 
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
          </div>
          
          <!-- Datepicker input -->
          <Datepicker
            v-else-if="field.type === 'date'"
            v-model="filterValues[field.name]"
            :input-class="'mt-1 block w-full rounded-md border-divider bg-card text-text-primary shadow-sm focus:border-primary focus:ring-primary sm:text-sm h-10'"
            :calendar-class="'bg-card text-text-primary'"
            :day-class="'text-text-primary'"
            :wrapper-class="'w-full v3dp__input_wrapper'"
            :clearable="true"
            :format="'yyyy-MM-dd'"
            :placeholder="field.placeholder || 'Select date'"
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
            <div v-for="option in getOptions(field)" :key="option.value" class="flex items-center">
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
            <div v-if="getLoading(field)" class="text-xs text-gray-400 py-1">Loading...</div>
            <div v-for="option in getOptions(field)" :key="option.value" class="flex items-center">
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
      <div class="mt-8 flex flex-row justify-center gap-4 w-full">
        <button
          type="button"
          @click="resetFilters"
          class="rounded-md border border-gray-300 bg-white py-2 px-4 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
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
import Datepicker from 'vue3-datepicker';

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

// Helper to get options from field (supports computed, function, or array)
function getOptions(field) {
  if (typeof field.options === 'function') return field.options();
  if (field.options && typeof field.options.value !== 'undefined') return field.options.value;
  return field.options || [];
}

// Helper to get loading state from field (supports computed, function, or boolean)
function getLoading(field) {
  if (typeof field.loading === 'function') return field.loading();
  if (field.loading && typeof field.loading.value !== 'undefined') return field.loading.value;
  return !!field.loading;
}
</script>

<style>
/* Fix vue3-datepicker clear button alignment and input height */
.v3dp__input_wrapper {
  display: flex;
  align-items: center;
  height: 2.5rem; /* h-10 */
}
.v3dp__input_wrapper input {
  height: 2.5rem !important;
  min-height: 2.5rem !important;
}
.v3dp__clear_icon {
  position: absolute;
  right: 2.5rem;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
}
</style> 