<template>
  <div v-html="compiledMarkdown" class="prose prose-sm max-w-none" />
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
const props = defineProps({
  content: { type: String, default: '' }
})
const compiledMarkdown = computed(() => props.content ? marked.parse(props.content) : '')
</script>

<style scoped>
.prose {
  /* Add minimal styling for markdown content */
  font-size: 0.95em;
  color: var(--nr-text-primary, #222);
}
</style>
