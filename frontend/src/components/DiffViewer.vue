<template>
  <div class="diff-viewer">
    <!-- Header with commit information -->
    <div class="bg-gray-100 p-4 mb-4 rounded-md">
      <div class="flex justify-between items-center">
        <div>
          <h3 class="text-lg font-semibold">Configuration Diff</h3>
          <div v-if="isLoading" class="text-sm text-gray-500">Loading...</div>
          <div v-else-if="error" class="text-sm text-red-500">{{ error }}</div>
          <div v-else class="text-sm text-gray-500">
            <span v-if="oldVersion">{{ formatDate(oldVersion.timestamp) }} ({{ oldVersion.job_id ? `Job #${oldVersion.job_id}` : 'Unknown' }})</span>
            <span v-if="oldVersion && newVersion"> → </span>
            <span v-if="newVersion">{{ formatDate(newVersion.timestamp) }} ({{ newVersion.job_id ? `Job #${newVersion.job_id}` : 'Unknown' }})</span>
          </div>
        </div>
        <div class="flex space-x-2">
          <!-- View type toggle -->
          <button 
            @click="toggleViewType" 
            class="px-3 py-1 border border-gray-300 rounded-md text-sm hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {{ viewType === 'side-by-side' ? 'Unified View' : 'Side-by-Side View' }}
          </button>
          <!-- Copy to clipboard button -->
          <button 
            @click="copyToClipboard" 
            class="px-3 py-1 border border-gray-300 rounded-md text-sm hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <span v-if="copied">Copied!</span>
            <span v-else>Copy</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Diff content container -->
    <div class="bg-white border border-gray-200 rounded-md overflow-auto">
      <div id="diff-container" ref="diffContainer"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import * as Diff2Html from 'diff2html';
import 'diff2html/bundles/css/diff2html.min.css';

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
  },
  initialViewType: {
    type: String,
    default: 'side-by-side',
    validator: (value) => ['side-by-side', 'line-by-line'].includes(value)
  }
});

// Reactive state
const diffContainer = ref(null);
const viewType = ref(props.initialViewType);
const copied = ref(false);

// Generate unified diff from old and new content
const diffText = computed(() => {
  if (!props.oldContent && !props.newContent) return '';
  
  const oldLines = (props.oldContent || '').split('\n');
  const newLines = (props.newContent || '').split('\n');
  
  // Create a unified diff format
  let diffLines = [];
  diffLines.push('diff --git a/old_config.txt b/new_config.txt');
  diffLines.push('--- a/old_config.txt');
  diffLines.push('+++ b/new_config.txt');
  
  // Simple diff algorithm (for more complex diffs, consider using a library like jsdiff)
  const oldLineCount = oldLines.length;
  const newLineCount = newLines.length;
  
  // Add unified diff header (showing line numbers)
  diffLines.push(`@@ -1,${oldLineCount} +1,${newLineCount} @@`);
  
  // Add old lines (with minus prefix)
  for (const line of oldLines) {
    diffLines.push(`-${line}`);
  }
  
  // Add new lines (with plus prefix)
  for (const line of newLines) {
    diffLines.push(`+${line}`);
  }
  
  return diffLines.join('\n');
});

// Watch changes to render diff
watch([() => props.oldContent, () => props.newContent, viewType], renderDiff, { immediate: true });

// Format date for display
function formatDate(timestamp) {
  if (!timestamp) return 'Unknown';
  return new Date(timestamp).toLocaleString();
}

// Render the diff using diff2html
function renderDiff() {
  if (!diffContainer.value) return;
  
  // Clear previous content
  diffContainer.value.innerHTML = '';
  
  // If no content, show message
  if (!props.oldContent && !props.newContent) {
    diffContainer.value.innerHTML = '<div class="p-4 text-gray-500 text-center">No configuration data available</div>';
    return;
  }
  
  // Configure diff2html options
  const configuration = {
    drawFileList: false,
    matching: 'lines',
    outputFormat: viewType.value,
    renderNothingWhenEmpty: true,
    matchWordsThreshold: 0.25,
    matchingMaxComparisons: 2500
  };
  
  // Render diff to container
  try {
    const diffHtml = Diff2Html.html(diffText.value, configuration);
    diffContainer.value.innerHTML = diffHtml;
  } catch (e) {
    console.error('Error rendering diff:', e);
    diffContainer.value.innerHTML = '<div class="p-4 text-red-500 text-center">Error rendering diff</div>';
  }
}

// Toggle between side-by-side and line-by-line (unified) views
function toggleViewType() {
  viewType.value = viewType.value === 'side-by-side' ? 'line-by-line' : 'side-by-side';
}

// Copy diff to clipboard
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

// Initialize component
onMounted(() => {
  renderDiff();
});
</script>

<style scoped>
.diff-viewer {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* Override diff2html styles for better integration with our UI */
:deep(.d2h-file-header) {
  background-color: #f3f4f6;
  border-bottom: 1px solid #e5e7eb;
  padding: 8px 10px;
}

:deep(.d2h-file-name) {
  font-weight: 600;
  color: #374151;
}

:deep(.d2h-code-line) {
  padding: 0 8px;
}

:deep(.d2h-code-side-line) {
  padding: 0 8px;
}

:deep(.d2h-code-line-ctn) {
  white-space: pre-wrap;
}

:deep(.d2h-info) {
  background-color: #f9fafb;
  color: #6b7280;
}

:deep(.d2h-file-list-wrapper) {
  display: none;
}

:deep(.d2h-tag) {
  display: none;
}

:deep(.d2h-del) {
  background-color: #fee2e2;
}

:deep(.d2h-ins) {
  background-color: #d1fae5;
}
</style> 