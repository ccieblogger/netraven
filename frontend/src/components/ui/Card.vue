<template>
  <div 
    class="nr-card" 
    :class="[
      padding ? `p-${padding}` : '',
      { 'shadow-md': shadow },
      { 'border-l-4 border-l-primary': accent },
      className
    ]"
  >
    <div v-if="$slots.header || title" :class="`border-b border-divider ${headerClass}`">
      <slot name="header">
        <h3 class="text-lg font-medium text-text-primary">{{ title }}</h3>
        <p v-if="subtitle" class="text-sm text-text-secondary mt-1">{{ subtitle }}</p>
      </slot>
    </div>
    
    <div :class="contentClass">
      <slot></slot>
    </div>
    
    <div v-if="$slots.footer" class="border-t border-divider p-4">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: ''
  },
  subtitle: {
    type: String,
    default: ''
  },
  padding: {
    type: [String, Number],
    default: '4'
  },
  contentClass: {
    type: String,
    default: 'p-4'
  },
  className: {
    type: String,
    default: ''
  },
  shadow: {
    type: Boolean,
    default: true
  },
  accent: {
    type: Boolean,
    default: false
  },
  headerClass: {
    type: String,
    default: 'p-0'
  }
});
</script> 