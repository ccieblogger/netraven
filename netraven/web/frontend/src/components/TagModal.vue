<template>
  <teleport to="body">
    <div 
      v-if="show" 
      class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      @click="$emit('close')"
    >
      <div 
        class="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md p-6 mx-4 overflow-hidden"
        @click.stop
      >
        <button 
          class="absolute top-4 right-4 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200" 
          @click="$emit('close')"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
        
        <h2 class="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
          {{ title || 'Manage Tags' }}
        </h2>
        
        <!-- Loading state -->
        <div v-if="loading" class="flex justify-center py-6">
          <div class="loader"></div>
        </div>
        
        <div v-else>
          <!-- Current tags -->
          <div class="mb-6">
            <h3 class="text-lg font-medium mb-2 text-gray-700 dark:text-gray-300">Current Tags</h3>
            
            <div v-if="currentTags && currentTags.length > 0" class="space-y-2">
              <div 
                v-for="tag in currentTags" 
                :key="tag.id" 
                class="flex items-center justify-between bg-gray-100 dark:bg-gray-700 px-3 py-2 rounded-md"
              >
                <div class="flex items-center">
                  <div 
                    class="w-4 h-4 rounded-full mr-2" 
                    :style="{ backgroundColor: tag.color || '#6366F1' }"
                  ></div>
                  <span class="text-gray-800 dark:text-gray-200">{{ formatTagName(tag.name) }}</span>
                </div>
                
                <button 
                  @click="removeTag(tag.id)"
                  class="text-red-500 hover:text-red-700 transition-colors"
                  :disabled="isRemovingTag === tag.id"
                >
                  <svg v-if="isRemovingTag === tag.id" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                </button>
              </div>
            </div>
            
            <div v-else class="text-gray-500 dark:text-gray-400 italic py-2">
              No tags assigned yet.
            </div>
          </div>
          
          <!-- Add new tag -->
          <div>
            <h3 class="text-lg font-medium mb-2 text-gray-700 dark:text-gray-300">Add Tags</h3>
            
            <div v-if="availableTags && availableTags.length > 0">
              <div class="flex space-x-2">
                <select 
                  v-model="selectedTagId"
                  class="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-gray-900 dark:text-gray-100"
                  @change="onTagSelected"
                >
                  <option value="" disabled>Select a tag</option>
                  <option 
                    v-for="tag in availableTags" 
                    :key="tag.id" 
                    :value="tag.id"
                  >
                    {{ formatTagName(tag.name) }}
                  </option>
                </select>
                
                <button 
                  @click="addTag"
                  :disabled="!selectedTagId || isAddingTag"
                  class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  <svg v-if="isAddingTag" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Add</span>
                </button>
              </div>
              
              <div class="mt-4">
                <button 
                  @click="openCreateTagModal"
                  class="inline-flex items-center text-indigo-600 hover:text-indigo-800"
                >
                  <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                  </svg>
                  Create new tag
                </button>
              </div>
            </div>
            
            <div v-else class="text-gray-500 dark:text-gray-400 italic py-2">
              No additional tags available. 
              <button 
                @click="openCreateTagModal"
                class="text-indigo-600 hover:text-indigo-800 hover:underline"
              >
                Create a new tag
              </button>
            </div>
          </div>
          
          <!-- Error message -->
          <div 
            v-if="error" 
            class="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-md"
          >
            {{ error }}
          </div>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useTagStore } from '@/store/tags'

export default {
  name: 'TagModal',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    deviceId: {
      type: String,
      default: null
    },
    title: {
      type: String,
      default: 'Manage Tags'
    }
  },
  emits: ['close', 'update:tags', 'open-create-tag'],
  setup(props, { emit }) {
    const tagsStore = useTagStore()
    
    const loading = ref(false)
    const error = ref(null)
    const selectedTagId = ref('')
    const isAddingTag = ref(false)
    const isRemovingTag = ref(null)
    
    // Computed properties
    const currentTags = computed(() => {
      const deviceTags = props.deviceId ? tagsStore.deviceTags[props.deviceId] || [] : []
      return deviceTags
    })
    
    const allTags = computed(() => {
      return tagsStore.tags || []
    })
    
    const availableTags = computed(() => {
      // Filter out tags that are already assigned to the device
      const filtered = allTags.value.filter(tag => 
        !currentTags.value.some(dt => dt.id === tag.id)
      )
      return filtered
    })
    
    // Methods
    const fetchTags = async () => {
      if (!props.deviceId) return
      
      loading.value = true
      error.value = null
      
      try {
        // First load all available tags
        await tagsStore.fetchTags()
        
        // Then load device-specific tags
        await tagsStore.fetchTagsForDevice(props.deviceId)
        
        // Clear selected tag after fetching
        selectedTagId.value = ''
      } catch (err) {
        error.value = 'Failed to load tags. Please try again.'
        console.error('Error loading tags:', err)
      } finally {
        loading.value = false
      }
    }
    
    // Handle tag selection change
    const onTagSelected = (event) => {
      // Clear any previous error message when a new tag is selected
      if (selectedTagId.value) {
        error.value = null;
      }
    }
    
    // Format tag name by removing "tag-" prefix if present
    const formatTagName = (name) => {
      if (!name) return ''
      return name.startsWith('tag-') ? name.substring(4) : name
    }
    
    const addTag = async () => {
      // Force convert selectedTagId to string if it exists
      const tagId = selectedTagId.value ? String(selectedTagId.value) : '';
      
      if (!tagId || !props.deviceId) {
        error.value = 'Please select a tag to add';
        return;
      }
      
      isAddingTag.value = true;
      error.value = null;
      
      try {
        await tagsStore.assignTagToDevice(props.deviceId, tagId);
        await tagsStore.fetchTagsForDevice(props.deviceId); // Refresh tags
        
        selectedTagId.value = '';
        emit('update:tags', tagsStore.deviceTags[props.deviceId]);
      } catch (err) {
        console.error('=== ERROR DETAILS ===');
        console.error('Error object:', err);
        console.error('Error name:', err.name);
        console.error('Error message:', err.message);
        console.error('Error stack:', err.stack);
        console.error('Response status:', err.response?.status);
        console.error('Response data:', err.response?.data);
        console.error('=== END ERROR DETAILS ===');
        
        // Provide more specific error messages based on the error
        if (err.response) {
          if (err.response.status === 404) {
            error.value = 'The tag or device could not be found. Please refresh and try again.';
          } else if (err.response.status === 409) {
            error.value = 'This tag is already assigned to the device.';
          } else if (err.response.data && err.response.data.detail) {
            error.value = `Failed to add tag: ${err.response.data.detail}`;
          } else {
            error.value = `Failed to add tag (${err.response.status}). Please try again.`;
          }
        } else if (err.message) {
          error.value = `Failed to add tag: ${err.message}`;
        } else {
          error.value = 'Failed to add tag. Please try again.';
        }
        
        console.error('Error adding tag:', err);
      } finally {
        isAddingTag.value = false;
      }
    }
    
    const removeTag = async (tagId) => {
      if (!tagId || !props.deviceId) {
        error.value = 'Cannot remove tag';
        return;
      }
      
      isRemovingTag.value = tagId;
      error.value = null;
      
      try {
        await tagsStore.removeTagFromDevice(props.deviceId, tagId);
        await tagsStore.fetchTagsForDevice(props.deviceId); // Refresh tags
        
        emit('update:tags', tagsStore.deviceTags[props.deviceId]);
      } catch (err) {
        console.error('Detailed error removing tag:', err)
        
        // Provide more specific error messages based on the error
        if (err.response) {
          if (err.response.status === 404) {
            error.value = 'The tag or device could not be found. Please refresh and try again.'
          } else if (err.response.data && err.response.data.detail) {
            error.value = `Failed to remove tag: ${err.response.data.detail}`
          } else {
            error.value = `Failed to remove tag (${err.response.status}). Please try again.`
          }
        } else if (err.message) {
          error.value = `Failed to remove tag: ${err.message}`
        } else {
          error.value = 'Failed to remove tag. Please try again.'
        }
        
        console.error('Error removing tag:', err)
      } finally {
        isRemovingTag.value = null
      }
    }
    
    const openCreateTagModal = () => {
      emit('open-create-tag')
    }
    
    // Lifecycle hooks
    onMounted(() => {
      if (props.show) {
        fetchTags()
      }
    })
    
    watch(() => props.show, (newVal) => {
      if (newVal) {
        fetchTags()
      }
    })
    
    return {
      loading,
      error,
      currentTags,
      availableTags,
      selectedTagId,
      isAddingTag,
      isRemovingTag,
      addTag,
      removeTag,
      openCreateTagModal,
      formatTagName,
      onTagSelected
    }
  }
}
</script>

<style scoped>
.loader {
  border: 3px solid #f3f3f3;
  border-radius: 50%;
  border-top: 3px solid #6366F1;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style> 