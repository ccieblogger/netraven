<template>
  <div class="flex w-full h-full">
    <div class="flex-1 border-r border-gray-700 min-w-0">
      <slot name="left" />
    </div>
    <div class="flex-1 min-w-0">
      <slot name="right" />
    </div>
  </div>
</template>

<script setup>
// No logic needed for basic split layout
</script>

<style scoped>
.flex {
  display: flex;
}
</style>
