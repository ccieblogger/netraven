<template>
  <div class="bg-card rounded-lg p-4 mb-4 border border-divider">
    <div class="flex flex-wrap gap-3">
      <!-- Device Dropdown -->
      <div class="w-full sm:w-48">
        <label class="block text-xs text-text-secondary mb-1">Device</label>
        <Listbox v-model="selectedDevice" as="div" class="relative">
          <div class="relative">
            <ListboxButton
              class="w-full px-3 py-2 bg-input border border-divider rounded text-text-primary focus:outline-none focus:ring-1 focus:ring-primary flex items-center justify-between"
            >
              <span class="truncate">{{ selectedDevice ? (selectedDevice.hostname || selectedDevice.name) : 'All Devices' }}</span>
              <ChevronDownIcon class="h-4 w-4 text-text-secondary" aria-hidden="true" />
            </ListboxButton>
            <transition
              leave-active-class="transition duration-100 ease-in"
              leave-from-class="opacity-100"
              leave-to-class="opacity-0"
            >
              <ListboxOptions
                class="absolute z-10 mt-1 w-full bg-card shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm"
              >
                <!-- Always use v-slot for ListboxOption to avoid Vue warnings -->
                <ListboxOption
                  v-slot="{ active, selected }"
                  :key="'all'"
                  :value="null"
                >
                  <div
                    :class="[
                      active ? 'bg-primary-light text-text-primary' : 'text-text-secondary',
                      'cursor-pointer select-none relative py-2 pl-3 pr-9'
                    ]"
                  >
                    <span :class="['block truncate', selected && 'font-medium']">All Devices</span>
                    <span v-if="selected" class="absolute inset-y-0 right-0 flex items-center pr-4">
                      <CheckIcon class="h-5 w-5 text-primary" aria-hidden="true" />
                    </span>
                  </div>
                </ListboxOption>
                <ListboxOption
                  v-for="device in devices"
                  v-slot="{ active, selected }"
                  :key="device.id"
                  :value="device"
                >
                  <div
                    :class="[
                      active ? 'bg-primary-light text-text-primary' : 'text-text-secondary',
                      'cursor-pointer select-none relative py-2 pl-3 pr-9'
                    ]"
                  >
                    <span :class="['block truncate', selected && 'font-medium']">{{ device.hostname || device.name }}</span>
                    <span v-if="selected" class="absolute inset-y-0 right-0 flex items-center pr-4">
                      <CheckIcon class="h-5 w-5 text-primary" aria-hidden="true" />
                    </span>
                  </div>
                </ListboxOption>
              </ListboxOptions>
            </transition>
          </div>
        </Listbox>
      </div>

      <!-- Date Range Picker -->
      <div class="w-full sm:w-72">
        <label class="block text-xs text-text-secondary mb-1">Date Range</label>
        <Popover class="relative">
          <PopoverButton
            class="w-full px-3 py-2 bg-input border border-divider rounded text-text-primary focus:outline-none focus:ring-1 focus:ring-primary flex items-center justify-between"
          >
            <span>{{ dateRangeText }}</span>
            <CalendarIcon class="h-4 w-4 text-text-secondary" aria-hidden="true" />
          </PopoverButton>

          <transition
            enter-active-class="transition duration-200 ease-out"
            enter-from-class="translate-y-1 opacity-0"
            enter-to-class="translate-y-0 opacity-100"
            leave-active-class="transition duration-150 ease-in"
            leave-from-class="translate-y-0 opacity-100"
            leave-to-class="translate-y-1 opacity-0"
          >
            <PopoverPanel class="absolute z-10 mt-1 w-96 p-4 bg-card shadow-lg rounded-md ring-1 ring-black ring-opacity-5 focus:outline-none">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-xs text-text-secondary mb-1">Start Date</label>
                  <input
                    v-model="startDate"
                    type="date"
                    class="w-full px-3 py-2 bg-input border border-divider rounded text-text-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <div>
                  <label class="block text-xs text-text-secondary mb-1">End Date</label>
                  <input
                    v-model="endDate"
                    type="date"
                    class="w-full px-3 py-2 bg-input border border-divider rounded text-text-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <div class="col-span-2 flex justify-end mt-2">
                  <button
                    @click="clearDateRange"
                    class="mr-2 px-3 py-1 text-sm border border-divider text-text-secondary rounded hover:bg-card-secondary focus:outline-none"
                  >
                    Clear
                  </button>
                  <button
                    @click="applyDateRange"
                    class="px-3 py-1 text-sm bg-primary text-white rounded hover:bg-primary-dark focus:outline-none"
                  >
                    Apply
                  </button>
                </div>
              </div>
            </PopoverPanel>
          </transition>
        </Popover>
      </div>

      <!-- Search Input -->
      <div class="flex-1 min-w-[200px]">
        <label class="block text-xs text-text-secondary mb-1">Search</label>
        <div class="relative">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search configurations..."
            class="w-full px-3 py-2 pl-9 bg-input border border-divider rounded text-text-primary focus:outline-none focus:ring-1 focus:ring-primary"
          />
          <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <MagnifyingGlassIcon class="h-4 w-4 text-text-secondary" aria-hidden="true" />
          </div>
        </div>
      </div>

      <!-- Search Button -->
      <div class="w-auto self-end">
        <button
          @click="search"
          class="px-4 py-2 bg-primary text-white rounded hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-opacity-50"
        >
          Search
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import {
  Listbox,
  ListboxButton,
  ListboxOptions,
  ListboxOption,
  Popover,
  PopoverButton,
  PopoverPanel
} from '@headlessui/vue'
import { MagnifyingGlassIcon, ChevronDownIcon, CheckIcon, CalendarIcon } from '@heroicons/vue/24/solid'

// Props
const props = defineProps({
  initialSearchQuery: {
    type: String,
    default: ''
  },
  initialDeviceId: {
    type: [String, Number],
    default: null
  },
  initialStartDate: {
    type: String,
    default: null
  },
  initialEndDate: {
    type: String,
    default: null
  },
  devices: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['search', 'update:searchQuery', 'update:deviceId', 'update:startDate', 'update:endDate'])

// State
const searchQuery = ref(props.initialSearchQuery)
const selectedDevice = ref(props.initialDeviceId ? props.devices.find(d => d.id === props.initialDeviceId) : null)
const startDate = ref(props.initialStartDate)
const endDate = ref(props.initialEndDate)
const appliedStartDate = ref(props.initialStartDate)
const appliedEndDate = ref(props.initialEndDate)

// Watch for changes to devices and update selectedDevice if needed
watch(
  () => props.devices,
  (newDevices) => {
    if (props.initialDeviceId) {
      selectedDevice.value = newDevices.find(d => d.id === props.initialDeviceId) || null;
    }
  },
  { immediate: true }
)

// Computed
const dateRangeText = computed(() => {
  if (!appliedStartDate.value && !appliedEndDate.value) {
    return 'Any Time'
  }
  if (appliedStartDate.value && !appliedEndDate.value) {
    return `Since ${formatDate(appliedStartDate.value)}`
  }
  if (!appliedStartDate.value && appliedEndDate.value) {
    return `Until ${formatDate(appliedEndDate.value)}`
  }
  return `${formatDate(appliedStartDate.value)} - ${formatDate(appliedEndDate.value)}`
})

// Methods
function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(date)
}

function applyDateRange() {
  appliedStartDate.value = startDate.value
  appliedEndDate.value = endDate.value
  emit('update:startDate', startDate.value)
  emit('update:endDate', endDate.value)
}

function clearDateRange() {
  startDate.value = null
  endDate.value = null
  appliedStartDate.value = null
  appliedEndDate.value = null
  emit('update:startDate', null)
  emit('update:endDate', null)
}

function search() {
  emit('search', {
    query: searchQuery.value,
    deviceId: selectedDevice.value?.id || null,
    startDate: appliedStartDate.value,
    endDate: appliedEndDate.value
  })
}

// Watch for changes to emit them up
watch(searchQuery, (newValue) => {
  emit('update:searchQuery', newValue)
})

watch(selectedDevice, (newValue) => {
  emit('update:deviceId', newValue?.id || null)
})
</script>
