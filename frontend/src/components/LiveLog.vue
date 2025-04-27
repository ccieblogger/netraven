<template>
  <div class="bg-black text-green-200 rounded-lg shadow p-4 relative h-80 overflow-y-auto font-mono text-xs" ref="logContainer">
    <div class="absolute top-2 right-4 flex gap-2 z-10">
      <button @click="togglePause" :class="['px-2 py-1 rounded', paused ? 'bg-yellow-600 text-black' : 'bg-gray-700 text-white']">
        <span v-if="paused">▶ Resume</span>
        <span v-else>⏸ Pause</span>
      </button>
      <button @click="toggleAutoScroll" :class="['px-2 py-1 rounded', autoScroll ? 'bg-blue-600 text-white' : 'bg-gray-700 text-white']">
        ▣ Auto-scroll
      </button>
      <button @click="clearLogs" class="px-2 py-1 rounded bg-red-700 text-white">Clear</button>
    </div>
    <div class="whitespace-pre-wrap break-words pr-2">
      <div v-for="(line, idx) in logs" :key="idx" :class="lineClass(line)">
        {{ line.text }}
      </div>
      <div v-if="logs.length === 0" class="text-gray-400 italic">No logs yet.</div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { fetchEventSource } from '@microsoft/fetch-event-source'
import { useAuthStore } from '../store/auth'
const props = defineProps({
  jobId: { type: [String, Number], required: true }
})

const logs = ref([])
const paused = ref(false)
const autoScroll = ref(true)
const controller = ref(null)
const logContainer = ref(null)
const authStore = useAuthStore()

function connectSSE() {
  if (controller.value) {
    controller.value.abort()
  }
  logs.value = []
  controller.value = new AbortController()
  const token = authStore.token
  fetchEventSource(`/api/logs/stream?job_id=${props.jobId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    signal: controller.value.signal,
    onmessage(ev) {
      if (paused.value) return
      try {
        const data = JSON.parse(ev.data)
        logs.value.push({ text: formatLog(data), level: data.level })
        if (autoScroll.value) scrollToBottom()
      } catch (e) {
        logs.value.push({ text: ev.data, level: 'info' })
      }
    },
    onerror(err) {
      logs.value.push({ text: '[connection lost, retrying...]', level: 'error' })
      setTimeout(connectSSE, 2000)
    },
    openWhenHidden: true,
  })
}

function formatLog(data) {
  // Example: [16:40:01] INFO backup ok edge-sw-01
  const ts = data.timestamp ? new Date(data.timestamp).toLocaleTimeString() : ''
  return `[${ts}] ${data.level?.toUpperCase() || ''} ${data.message || ''}`
}

function scrollToBottom() {
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}

function togglePause() {
  paused.value = !paused.value
}
function toggleAutoScroll() {
  autoScroll.value = !autoScroll.value
  if (autoScroll.value) scrollToBottom()
}
function clearLogs() {
  logs.value = []
}
function lineClass(line) {
  if (line.level === 'error') return 'text-red-400'
  if (line.level === 'warning') return 'text-yellow-300'
  if (line.level === 'debug') return 'text-blue-300'
  return ''
}

watch(() => props.jobId, () => {
  connectSSE()
})

onMounted(() => {
  connectSSE()
})
onBeforeUnmount(() => {
  if (controller.value) controller.value.abort()
})
</script>

<style scoped>
.bg-black {
  background: #18181b;
}
</style> 