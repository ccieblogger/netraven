<template>
  <div class="diff-viewer" role="region" aria-label="Configuration Diff Viewer">
    <!-- Header with commit information -->
    <div class="bg-gray-100 p-4 mb-4 rounded-md">
      <div class="flex justify-between items-center">
        <div>
          <h3 class="text-lg font-semibold">Configuration Diff</h3>
          <div v-if="isLoading" class="text-sm text-gray-500" aria-live="polite">Loading...</div>
          <div v-else-if="error" class="text-sm text-red-500" aria-live="assertive">{{ error }}</div>
          <div v-else class="text-sm text-gray-500">
            <span v-if="oldVersion">{{ formatDate(oldVersion.timestamp) }} ({{ oldVersion.job_id ? `Job #${oldVersion.job_id}` : 'Unknown' }})</span>
            <span v-if="oldVersion && newVersion"> → </span>
            <span v-if="newVersion">{{ formatDate(newVersion.timestamp) }} ({{ newVersion.job_id ? `Job #${newVersion.job_id}` : 'Unknown' }})</span>
          </div>
        </div>
        <div class="flex space-x-2">
          <!-- Copy to clipboard button only -->
          <button 
            @click="copyToClipboard" 
            class="px-3 py-1 border border-gray-300 rounded-md text-sm hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Copy diff to clipboard"
            tabindex="0"
          >
            <span v-if="copied">Copied!</span>
            <span v-else>Copy</span>
          </button>
        </div>
      </div>
    </div>
    <!-- Monaco Diff Editor -->
    <div class="bg-white border border-gray-200 rounded-md overflow-auto max-h-[70vh]" role="region" aria-label="Diff content">
      <template v-if="!isLoading && !error">
        <div v-if="!oldContent?.trim() && !newContent?.trim()" class="p-4 text-gray-500 text-center">No configuration data available</div>
        <div v-else-if="oldContent === newContent" class="p-4 text-gray-500 text-center">No differences found between selected versions.</div>
        <vue-monaco-diff-editor
          v-else
          :original="sanitizeContent(oldContent)"
          :modified="sanitizeContent(newContent)"
          :key="diffKey"
          language="plaintext"
          :options="monacoOptions"
          theme="netraven-dark"
          style="height: 70vh; width: 100%;"
        />
      </template>
      <div v-else-if="isLoading" class="p-4 text-gray-500 text-center">Loading diff...</div>
      <div v-else-if="error" class="p-4 text-red-500 text-center">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import { VueMonacoDiffEditor } from '@guolao/vue-monaco-editor';

// Props
const props = defineProps({
  oldContent: {
    type: String,
    default: ''
  },
  newContent: {
    type: String,
    default: ''
  },
  oldVersion: {
    type: Object,
    default: () => null
  },
  newVersion: {
    type: Object,
    default: () => null
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  }
});

const copied = ref(false);

// Monaco options
const monacoOptions = computed(() => ({
  renderSideBySide: true,
  readOnly: true,
  lineNumbers: 'on',
  minimap: { enabled: false },
  scrollBeyondLastLine: false
}));

const sanitizeContent = (content) => {
  if (typeof content !== 'string' || !content.trim()) return ' ';
  return content;
};

const diffKey = computed(() => `${Date.now()}-${(props.oldContent || '').slice(0, 32)}-${(props.newContent || '').slice(0, 32)}`);

function formatDate(timestamp) {
  if (!timestamp) return 'Unknown';
  return new Date(timestamp).toLocaleString();
}

function copyToClipboard() {
  const textToCopy = props.oldContent && props.newContent 
    ? `Old Configuration:\n${props.oldContent}\n\nNew Configuration:\n${props.newContent}`
    : props.oldContent || props.newContent || '';
  navigator.clipboard.writeText(textToCopy)
    .then(() => {
      copied.value = true;
      setTimeout(() => { copied.value = false; }, 2000);
    })
    .catch(err => {
      console.error('Failed to copy text: ', err);
    });
}

import * as monaco from 'monaco-editor';
onMounted(() => {
  monaco.editor.defineTheme('netraven-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: '', background: '181F2A', foreground: 'E5E7EB' },
      { token: 'deleted', background: 'fee2e2' },
      { token: 'inserted', background: 'd1fae5' }
    ],
    colors: {
      'editor.background': '#181F2A',
      'editor.foreground': '#E5E7EB',
      'editor.lineHighlightBackground': '#232B3A'
    }
  });
});
</script>

<style scoped>
.diff-viewer {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
</style>