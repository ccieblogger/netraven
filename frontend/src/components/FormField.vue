<template>
  <div>
    <label :for="id" class="block text-sm font-medium text-gray-700">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    <div class="mt-1 relative">
      <!-- Standard Text Input -->
      <input
        v-if="type !== 'textarea' && type !== 'select'"
        :id="id"
        :type="type"
        :min="min"
        :max="max"
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        :disabled="disabled"
        :placeholder="placeholder"
        :required="required"
        :pattern="pattern"
        :class="[
          'block w-full rounded-md shadow-sm sm:text-sm',
          error ? 'border-red-300 text-red-900 placeholder-red-300 focus:border-red-500 focus:ring-red-500' 
                : 'border-gray-300 focus:border-indigo-500 focus:ring-indigo-500',
          disabled ? 'bg-gray-100 cursor-not-allowed' : ''
        ]"
      />

      <!-- Textarea Input -->
      <textarea
        v-else-if="type === 'textarea'"
        :id="id"
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
        :disabled="disabled"
        :placeholder="placeholder"
        :required="required"
        :rows="rows || 3"
        :class="[
          'block w-full rounded-md shadow-sm sm:text-sm',
          error ? 'border-red-300 text-red-900 placeholder-red-300 focus:border-red-500 focus:ring-red-500' 
                : 'border-gray-300 focus:border-indigo-500 focus:ring-indigo-500',
          disabled ? 'bg-gray-100 cursor-not-allowed' : ''
        ]"
      ></textarea>

      <!-- Select Input -->
      <select
        v-else
        :id="id"
        :value="modelValue"
        @change="$emit('update:modelValue', $event.target.value)"
        :disabled="disabled"
        :required="required"
        :multiple="multiple"
        :class="[
          'block w-full rounded-md shadow-sm sm:text-sm',
          multiple ? 'h-24' : '',
          error ? 'border-red-300 text-red-900 focus:border-red-500 focus:ring-red-500' 
                : 'border-gray-300 focus:border-indigo-500 focus:ring-indigo-500',
          disabled ? 'bg-gray-100 cursor-not-allowed' : ''
        ]"
      >
        <option v-if="placeholder && !multiple" value="">{{ placeholder }}</option>
        <slot></slot>
      </select>

      <!-- Error Icon for Validation Errors -->
      <div v-if="error" class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
        <ExclamationCircleIcon class="h-5 w-5 text-red-500" aria-hidden="true" />
      </div>
    </div>
    
    <!-- Error Message Display -->
    <p v-if="error" class="mt-2 text-sm text-red-600">{{ error }}</p>
    
    <!-- Help Text -->
    <p v-if="helpText && !error" class="mt-2 text-sm text-gray-500">{{ helpText }}</p>
  </div>
</template>

<script setup>
import { ExclamationCircleIcon } from '@heroicons/vue/20/solid';

defineProps({
  id: {
    type: String,
    required: true
  },
  modelValue: {
    type: [String, Number, Boolean, Array],
    default: ''
  },
  label: {
    type: String,
    required: true
  },
  type: {
    type: String,
    default: 'text',
    validator: (value) => {
      return ['text', 'number', 'email', 'password', 'date', 'time', 'datetime-local', 
              'textarea', 'select', 'checkbox', 'radio', 'tel', 'url'].includes(value);
    }
  },
  placeholder: {
    type: String,
    default: ''
  },
  required: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  helpText: {
    type: String,
    default: ''
  },
  min: {
    type: [Number, String],
    default: null
  },
  max: {
    type: [Number, String], 
    default: null
  },
  pattern: {
    type: String,
    default: ''
  },
  multiple: {
    type: Boolean,
    default: false
  },
  rows: {
    type: Number,
    default: 3
  }
});

defineEmits(['update:modelValue']);
</script> 