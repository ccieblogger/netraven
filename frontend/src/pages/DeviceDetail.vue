<template>
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-semibold mb-4">Device Detail</h1>
    <div class="bg-white shadow-md rounded p-6">
      <p class="text-lg">Device ID: {{ deviceId }}</p>
      <p class="text-gray-500 mt-2">(This is a placeholder page. Implement device details here.)</p>
    </div>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
const route = useRoute()
const deviceId = route.params.id
</script> 