<template>
  <Button
    :icon="icon"
    :class="[
      'inline-flex items-center justify-center rounded font-medium transition focus:outline-none',
      sizeClasses,
      variantClasses,
      iconOnlyClasses,
      { 'opacity-50 cursor-not-allowed': disabled }
    ]"
    :type="type"
    :disabled="disabled"
    @click="$emit('click', $event)"
    :aria-label="ariaLabel"
    :title="title"
  >
    <span v-if="!iconOnly && $slots.default" :class="{ 'ml-2': icon }">
      <slot></slot>
    </span>
  </Button>
</template>

<script setup>
import { computed } from 'vue';
import Button from 'primevue/button';

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'secondary', 'danger', 'success', 'warning', 'info', 'link'].includes(value)
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  },
  type: {
    type: String,
    default: 'button'
  },
  disabled: {
    type: Boolean,
    default: false
  },
  iconOnly: {
    type: Boolean,
    default: false
  },
  icon: {
    type: String,
    default: ''
  },
  ariaLabel: {
    type: String,
    default: ''
  },
  title: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['click']);

// Dynamic classes based on variant
const variantClasses = computed(() => {
  switch (props.variant) {
    case 'primary':
      return 'bg-primary text-white hover:bg-primary-dark';
    case 'secondary':
      return 'bg-transparent border border-divider text-text-secondary hover:bg-opacity-10 hover:bg-white';
    case 'danger':
      return 'bg-red-600 text-white hover:bg-red-700';
    case 'success':
      return 'bg-green-600 text-white hover:bg-green-700';
    case 'warning':
      return 'bg-amber-500 text-white hover:bg-amber-600';
    case 'info':
      return 'bg-blue-500 text-white hover:bg-blue-600';
    case 'link':
      return 'bg-transparent text-primary hover:underline p-0';
    default:
      return 'bg-primary text-white hover:bg-primary-dark';
  }
});

// Dynamic classes based on size
const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'text-xs px-2 py-1';
    case 'md':
      return 'text-sm px-3 py-2';
    case 'lg':
      return 'text-base px-4 py-2';
    default:
      return 'text-sm px-3 py-2';
  }
});

// Classes for icon-only buttons (making them square)
const iconOnlyClasses = computed(() => {
  if (!props.iconOnly) return '';
  
  switch (props.size) {
    case 'sm':
      return 'p-1 w-6 h-6';
    case 'md':
      return 'p-2 w-8 h-8';
    case 'lg':
      return 'p-2 w-10 h-10';
    default:
      return 'p-2 w-8 h-8';
  }
});
</script> 