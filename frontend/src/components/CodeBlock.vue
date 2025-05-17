<template>
  <div class="relative bg-gray-900 rounded p-3 overflow-x-auto h-full">
    <div v-if="label" class="absolute top-2 left-3 text-xs text-gray-400">{{ label }}</div>
    <pre class="text-xs font-mono text-white whitespace-pre-wrap break-all mt-5">
      <code>{{ code }}</code>
    </pre>
    <button v-if="showCopy" @click="copy" class="absolute top-2 right-3 btn btn-xs btn-primary">Copy</button>
  </div>
</template>

<script setup>
import { ref } from 'vue';
const props = defineProps({
  code: { type: String, required: true },
  label: { type: String, default: '' },
  showCopy: { type: Boolean, default: false }
});
function copy() {
  navigator.clipboard.writeText(props.code);
}
</script>

<style scoped>
.btn-xs {
  @apply px-2 py-0.5 text-xs rounded;
}
</style>
