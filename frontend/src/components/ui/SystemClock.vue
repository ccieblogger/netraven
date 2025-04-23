<template>
  <div class="flex items-center text-sm font-mono text-text-secondary">
    <span>Local Time: {{ localTime }}</span>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '../../services/api'

const localTime = ref('')
let timer = null
let resyncTimer = null

async function fetchAndSetTime() {
  try {
    const res = await api.get('/system/status')
    if (res.data && res.data.system_time) {
      const utcDate = new Date(res.data.system_time)
      localTime.value = utcDate.toLocaleString()
    }
  } catch (e) {
    localTime.value = ''
  }
}

function tick() {
  // Just increment the time by 1s if possible, else refetch
  if (localTime.value) {
    const d = new Date(localTime.value)
    if (!isNaN(d)) {
      d.setSeconds(d.getSeconds() + 1)
      localTime.value = d.toLocaleString()
      return
    }
  }
  fetchAndSetTime()
}

onMounted(() => {
  fetchAndSetTime()
  timer = setInterval(tick, 1000)
  resyncTimer = setInterval(fetchAndSetTime, 600000) // every 10 minutes
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (resyncTimer) clearInterval(resyncTimer)
})
</script> 