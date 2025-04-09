<template>
  <div class="bg-white shadow-md rounded-lg overflow-hidden">
    <!-- Loading Indicator -->
    <div v-if="loading" class="flex justify-center items-center py-10">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
      <span class="ml-2 text-gray-600">Loading...</span>
    </div>

    <!-- No Data Message -->
    <div v-else-if="!items || items.length === 0" class="flex flex-col items-center justify-center py-10 text-gray-500">
      <slot name="empty">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
        </svg>
        <p class="mt-2">No items found</p>
      </slot>
    </div>

    <!-- Table -->
    <div v-else class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th
              v-for="column in columns"
              :key="column.key"
              scope="col"
              :class="[
                'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider',
                column.sortable ? 'cursor-pointer hover:bg-gray-100' : '',
                column.width ? column.width : '',
                column.align ? `text-${column.align}` : 'text-left'
              ]"
              @click="column.sortable ? handleSort(column.key) : null"
            >
              <div class="flex items-center space-x-1">
                <span>{{ column.label }}</span>
                <span v-if="column.sortable" class="ml-1">
                  <svg 
                    v-if="sortKey === column.key && sortOrder === 'asc'"
                    xmlns="http://www.w3.org/2000/svg" 
                    class="h-4 w-4 text-indigo-500" 
                    fill="none" 
                    viewBox="0 0 24 24" 
                    stroke="currentColor"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
                  </svg>
                  <svg 
                    v-else-if="sortKey === column.key && sortOrder === 'desc'"
                    xmlns="http://www.w3.org/2000/svg" 
                    class="h-4 w-4 text-indigo-500" 
                    fill="none" 
                    viewBox="0 0 24 24" 
                    stroke="currentColor"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                  </svg>
                  <svg 
                    v-else
                    xmlns="http://www.w3.org/2000/svg" 
                    class="h-4 w-4 text-gray-300" 
                    fill="none" 
                    viewBox="0 0 24 24" 
                    stroke="currentColor"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                  </svg>
                </span>
              </div>
            </th>
            <!-- Actions column if slot is provided -->
            <th v-if="$slots.actions" scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr 
            v-for="(item, index) in sortedItems" 
            :key="getItemKey(item, index)"
            class="hover:bg-gray-50"
            :class="{ 'bg-indigo-50': isSelected(item) }"
          >
            <td 
              v-for="column in columns" 
              :key="`${getItemKey(item, index)}-${column.key}`"
              :class="[
                'px-6 py-4 whitespace-nowrap text-sm text-gray-900',
                column.align ? `text-${column.align}` : 'text-left'
              ]"
            >
              <!-- Use custom rendering via slot if provided -->
              <slot :name="`cell(${column.key})`" :item="item" :value="getColumnValue(item, column.key)">
                {{ getColumnValue(item, column.key) }}
              </slot>
            </td>
            <!-- Actions slot -->
            <td v-if="$slots.actions" class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
              <slot name="actions" :item="item" :index="index"></slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination slot -->
    <div v-if="$slots.pagination" class="bg-white px-4 py-3 border-t border-gray-200">
      <slot name="pagination"></slot>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';

const props = defineProps({
  /**
   * Items to display in the table
   */
  items: {
    type: Array,
    required: true
  },
  /**
   * Column definitions
   * [{ key: 'id', label: 'ID', sortable: true, width: 'w-20', align: 'center' }, ...]
   */
  columns: {
    type: Array,
    required: true
  },
  /**
   * Loading state
   */
  loading: {
    type: Boolean,
    default: false
  },
  /**
   * Key to use for item identification
   */
  itemKey: {
    type: String,
    default: 'id'
  },
  /**
   * Default sort key
   */
  defaultSortKey: {
    type: String,
    default: ''
  },
  /**
   * Default sort order (asc or desc)
   */
  defaultSortOrder: {
    type: String,
    default: 'asc',
    validator: (value) => ['asc', 'desc'].includes(value)
  },
  /**
   * Array of selected item IDs
   */
  selected: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['sort', 'row-click']);

// Internal sort state
const sortKey = ref(props.defaultSortKey);
const sortOrder = ref(props.defaultSortOrder);

// Initialize sort with default values
watch(() => props.defaultSortKey, (newVal) => {
  sortKey.value = newVal;
}, { immediate: true });

watch(() => props.defaultSortOrder, (newVal) => {
  sortOrder.value = newVal;
}, { immediate: true });

/**
 * Get a unique key for each item
 */
function getItemKey(item, index) {
  return props.itemKey && item[props.itemKey] ? item[props.itemKey] : index;
}

/**
 * Get the value for a column from an item, handling nested properties
 */
function getColumnValue(item, key) {
  // Handle nested properties (e.g., 'user.name')
  if (key.includes('.')) {
    return key.split('.').reduce((obj, property) => {
      return obj && obj[property] !== undefined ? obj[property] : null;
    }, item);
  }
  return item[key];
}

/**
 * Check if an item is selected
 */
function isSelected(item) {
  if (!props.selected || !props.selected.length) return false;
  const itemId = getItemKey(item, -1);
  return props.selected.includes(itemId);
}

/**
 * Handle sorting
 */
function handleSort(key) {
  if (sortKey.value === key) {
    // Toggle order if already sorting by this key
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    // Set new sort key and default to ascending
    sortKey.value = key;
    sortOrder.value = 'asc';
  }
  
  emit('sort', { key: sortKey.value, order: sortOrder.value });
}

/**
 * Sort items based on current sort key and order
 */
const sortedItems = computed(() => {
  if (!sortKey.value || !props.items || props.items.length === 0) {
    return props.items;
  }
  
  return [...props.items].sort((a, b) => {
    const aVal = getColumnValue(a, sortKey.value);
    const bVal = getColumnValue(b, sortKey.value);
    
    // Handle undefined or null values
    if (aVal === undefined || aVal === null) return sortOrder.value === 'asc' ? -1 : 1;
    if (bVal === undefined || bVal === null) return sortOrder.value === 'asc' ? 1 : -1;
    
    // Sort by type
    if (typeof aVal === 'string' && typeof bVal === 'string') {
      return sortOrder.value === 'asc' 
        ? aVal.localeCompare(bVal) 
        : bVal.localeCompare(aVal);
    }
    
    // Default numeric sort
    return sortOrder.value === 'asc' 
      ? aVal - bVal 
      : bVal - aVal;
  });
});
</script> 