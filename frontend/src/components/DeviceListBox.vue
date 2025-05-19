<script setup>
import { ref } from 'vue'
import { Listbox } from '@headlessui/vue'

const selected = ref('dark')
const themes = ['dark', 'light', 'blue']
</script>

<template>
  <div class="p-4">
    <Listbox v-model="selected">
      <Listbox.Button class="w-full h-8 rounded bg-card text-white text-sm px-3 border border-divider">
        {{ selected }}
      </Listbox.Button>
      <Listbox.Options class="mt-1 w-full rounded bg-card border border-divider shadow-lg">
        <Listbox.Option
          v-for="theme in themes"
          :key="theme"
          :value="theme"
          v-slot="{ selected, active }"
          class="cursor-pointer select-none py-1 px-3 text-sm text-white hover:bg-primary/20"
        >
          <span :class="{ 'font-bold': selected }">{{ theme }}</span>
          <span v-if="selected">✔︎</span>
        </Listbox.Option>
      </Listbox.Options>
    </Listbox>
  </div>
</template>
