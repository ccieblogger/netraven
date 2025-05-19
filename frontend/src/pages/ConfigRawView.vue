<template>
  <div class="h-full flex flex-col bg-card text-text-primary p-4">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-xl font-semibold">Raw Configuration</h2>
      <div class="flex gap-2">
        <button @click="copyConfig" class="btn btn-primary" :disabled="loading">Copy</button>
        <button @click="downloadConfig" class="btn btn-secondary" :disabled="loading">Download</button>
      </div>
    </div>
    <div v-if="error" class="text-red-500 mb-2">{{ error }}</div>
    <div v-if="loading" class="text-gray-400">Loading...</div>
    <Split v-if="showDiff" :minSize="100" :maxSize="-100" class="flex-1">
      <template #left>
        <CodeBlock :code="config" label="Current" />
      </template>
      <template #right>
        <CodeBlock :code="diffConfig" label="Diff With" />
      </template>
    </Split>
    <CodeBlock v-else :code="config" class="flex-1" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import CodeBlock from '../components/CodeBlock.vue';
import Split from '../components/Split.vue';

const route = useRoute();
const config = ref('');
const diffConfig = ref('');
const loading = ref(true);
const error = ref('');
const showDiff = ref(false);

const device = route.params.device;
const snapshotId = route.params.snapshotId;
const diffWith = route.query.diffWith;

async function fetchConfig(device, snapshotId, targetRef) {
  try {
    const res = await fetch(`/configs/${device}/${snapshotId}`);
    if (!res.ok) throw new Error('Failed to fetch config');
    const text = await res.text();
    targetRef.value = text;
  } catch (e) {
    error.value = e.message;
  }
}

async function fetchDiffConfig(device, diffId) {
  try {
    const res = await fetch(`/configs/${device}/${diffId}`);
    if (!res.ok) throw new Error('Failed to fetch diff config');
    diffConfig.value = await res.text();
  } catch (e) {
    error.value = e.message;
  }
}

onMounted(async () => {
  loading.value = true;
  await fetchConfig(device, snapshotId, config);
  if (diffWith) {
    showDiff.value = true;
    await fetchDiffConfig(device, diffWith);
  }
  loading.value = false;
});

function copyConfig() {
  navigator.clipboard.writeText(config.value);
}

async function downloadConfig() {
  try {
    const res = await fetch(`/configs/${device}/${snapshotId}`);
    if (!res.ok) throw new Error('Failed to download config');
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${device}_${snapshotId}.txt`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch (e) {
    error.value = e.message;
  }
}
</script>

<style scoped>
.btn {
  @apply px-3 py-1 rounded font-medium transition-colors;
}
.btn-primary {
  @apply bg-primary text-white hover:bg-primary-dark;
}
.btn-secondary {
  @apply bg-secondary text-white hover:bg-secondary-dark;
}
</style>
