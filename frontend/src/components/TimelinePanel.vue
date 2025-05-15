<template>
  <transition name="slide-over">
    <div v-if="isOpen" class="fixed inset-0 z-50 flex">
      <!-- Overlay -->
      <div class="fixed inset-0 bg-black bg-opacity-30" @click="closePanel" />
      <!-- Panel -->
      <div class="relative ml-auto w-full max-w-md bg-card shadow-xl h-full flex flex-col transition-all duration-300 sm:max-w-full sm:w-full">
        <div class="flex items-center justify-between p-4 border-b border-divider">
          <h2 class="text-lg font-semibold text-text-primary">Timeline for {{ device?.hostname || 'Device' }}</h2>
          <button @click="closePanel" class="text-text-secondary hover:text-text-primary focus:outline-none">
            <span class="sr-only">Close</span>
            &times;
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-4">
          <div v-if="loading" class="text-center py-8 text-text-secondary">Loading...</div>
          <div v-else-if="snapshots.length === 0" class="text-center py-8 text-text-secondary">No snapshots found.</div>
          <ul v-else class="space-y-4">
            <li v-for="snap in snapshots" :key="snap.id" class="bg-card-secondary rounded p-3 flex flex-col sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div class="font-mono text-sm text-text-primary">{{ formatDate(snap.retrieved_at) }}</div>
                <div class="text-xs text-text-secondary">ID: {{ snap.id }}</div>
              </div>
              <div class="flex space-x-2 mt-2 sm:mt-0">
                <button @click="$emit('view', snap)" class="px-2 py-1 text-xs bg-primary text-white rounded hover:bg-primary-dark">View</button>
                <button @click="$emit('diff', snap)" class="px-2 py-1 text-xs bg-secondary text-white rounded hover:bg-secondary-dark">Diff</button>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import { fetchDeviceSnapshots } from '../services/configSnapshots';

const props = defineProps({
  isOpen: Boolean,
  device: Object,
});
const emit = defineEmits(['close', 'view', 'diff']);

const loading = ref(false);
const snapshots = ref([]);

function closePanel() {
  emit('close');
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleString();
}

async function loadSnapshots() {
  if (!props.device) return;
  loading.value = true;
  try {
    // Replace with real API call
    const result = await fetchDeviceSnapshots(props.device.id);
    snapshots.value = result || [];
  } catch (e) {
    snapshots.value = [];
  } finally {
    loading.value = false;
  }
}

watch(() => props.isOpen, (open) => {
  if (open) loadSnapshots();
});
watch(() => props.device, (dev) => {
  if (props.isOpen && dev) loadSnapshots();
});
</script>

<style scoped>
.slide-over-enter-active,
.slide-over-leave-active {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.slide-over-enter-from,
.slide-over-leave-to {
  transform: translateX(100%);
}
.slide-over-enter-to,
.slide-over-leave-from {
  transform: translateX(0);
}
</style>
