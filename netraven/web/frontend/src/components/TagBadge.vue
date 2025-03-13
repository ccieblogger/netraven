<template>
  <div 
    class="inline-flex items-center text-xs px-2 py-1 rounded-full font-medium"
    :style="{ 
      backgroundColor: backgroundColor, 
      color: textColor 
    }"
  >
    <span>{{ tag.name }}</span>
    <button 
      v-if="removable" 
      class="ml-1 focus:outline-none" 
      @click.stop="$emit('remove', tag)"
      type="button"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
      </svg>
    </button>
  </div>
</template>

<script>
export default {
  name: 'TagBadge',
  props: {
    tag: {
      type: Object,
      required: true
    },
    removable: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    backgroundColor() {
      return this.tag.color || '#4F46E5'; // Default to Indigo-600 if no color
    },
    textColor() {
      // Determine if text should be white or black based on background brightness
      const color = this.tag.color || '#4F46E5';
      const r = parseInt(color.slice(1, 3), 16);
      const g = parseInt(color.slice(3, 5), 16);
      const b = parseInt(color.slice(5, 7), 16);
      const brightness = (r * 299 + g * 587 + b * 114) / 1000;
      return brightness > 128 ? '#000000' : '#FFFFFF';
    }
  },
  emits: ['remove']
}
</script> 