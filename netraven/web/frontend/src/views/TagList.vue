<template>
  <MainLayout>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Device Tags</h1>
      <button 
        @click="showCreateModal = true" 
        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
      >
        Add New Tag
      </button>
    </div>
    
    <div v-if="loading" class="text-center py-8">
      <p>Loading tags...</p>
    </div>
    
    <div v-else-if="tags.length === 0" class="bg-white rounded-lg shadow p-6 text-center">
      <p class="text-gray-600 mb-4">No tags have been created yet.</p>
      <button 
        @click="showCreateModal = true" 
        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
      >
        Create Your First Tag
      </button>
    </div>
    
    <div v-else class="bg-white rounded-lg shadow overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Tag
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Description
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Devices
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Created
            </th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="tag in tags" :key="tag.id">
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="flex items-center">
                <TagBadge :tag="tag" />
              </div>
            </td>
            <td class="px-6 py-4">
              <div class="text-sm text-gray-900">
                {{ tag.description || 'No description' }}
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm text-gray-900">
                {{ tag.device_count || 0 }} devices
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm text-gray-500">
                {{ formatDate(tag.created_at) }}
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
              <button
                @click="editTag(tag)"
                class="text-blue-600 hover:text-blue-900 mr-4"
              >
                Edit
              </button>
              <button
                @click="confirmDelete(tag)"
                class="text-red-600 hover:text-red-900"
              >
                Delete
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- Create Tag Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
        <h2 class="text-xl font-bold mb-4">Add New Tag</h2>
        
        <div class="mb-4">
          <label class="block text-gray-700 text-sm font-bold mb-2" for="name">
            Tag Name
          </label>
          <input
            id="name"
            v-model="newTag.name"
            type="text"
            class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            placeholder="Enter tag name"
          />
        </div>
        
        <div class="mb-4">
          <label class="block text-gray-700 text-sm font-bold mb-2" for="color">
            Color
          </label>
          <input
            id="color"
            v-model="newTag.color"
            type="color"
            class="shadow border rounded h-10 w-full cursor-pointer"
          />
        </div>
        
        <div class="mb-4">
          <label class="block text-gray-700 text-sm font-bold mb-2" for="description">
            Description
          </label>
          <textarea
            id="description"
            v-model="newTag.description"
            class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            placeholder="Enter tag description"
            rows="3"
          ></textarea>
        </div>
        
        <div class="flex justify-end">
          <button
            @click="showCreateModal = false"
            class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded mr-2"
          >
            Cancel
          </button>
          <button
            @click="createTag"
            class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            :disabled="!newTag.name"
          >
            Create
          </button>
        </div>
      </div>
    </div>
    
    <!-- Edit Tag Modal -->
    <div v-if="showEditModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
        <h2 class="text-xl font-bold mb-4">Edit Tag</h2>
        
        <div class="mb-4">
          <label class="block text-gray-700 text-sm font-bold mb-2" for="edit-name">
            Tag Name
          </label>
          <input
            id="edit-name"
            v-model="editingTag.name"
            type="text"
            class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            placeholder="Enter tag name"
          />
        </div>
        
        <div class="mb-4">
          <label class="block text-gray-700 text-sm font-bold mb-2" for="edit-color">
            Color
          </label>
          <input
            id="edit-color"
            v-model="editingTag.color"
            type="color"
            class="shadow border rounded h-10 w-full cursor-pointer"
          />
        </div>
        
        <div class="mb-4">
          <label class="block text-gray-700 text-sm font-bold mb-2" for="edit-description">
            Description
          </label>
          <textarea
            id="edit-description"
            v-model="editingTag.description"
            class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            placeholder="Enter tag description"
            rows="3"
          ></textarea>
        </div>
        
        <div class="flex justify-end">
          <button
            @click="showEditModal = false"
            class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded mr-2"
          >
            Cancel
          </button>
          <button
            @click="updateTag"
            class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            :disabled="!editingTag.name"
          >
            Update
          </button>
        </div>
      </div>
    </div>
    
    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
        <h2 class="text-xl font-bold mb-4">Delete Tag</h2>
        
        <p class="mb-6">
          Are you sure you want to delete the tag "<span class="font-semibold">{{ deleteTagName }}</span>"? 
          This action cannot be undone.
        </p>
        
        <div class="flex justify-end">
          <button
            @click="showDeleteModal = false"
            class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded mr-2"
          >
            Cancel
          </button>
          <button
            @click="deleteTag"
            class="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script>
import { ref, reactive, onMounted, computed, onActivated } from 'vue'
import MainLayout from '@/components/MainLayout.vue'
import TagBadge from '@/components/TagBadge.vue'
import { useTagStore } from '@/store/tags'

export default {
  name: 'TagList',
  components: {
    MainLayout,
    TagBadge
  },
  
  setup() {
    const tagStore = useTagStore()
    
    const tags = computed(() => tagStore.tags)
    const loading = computed(() => tagStore.loading)
    const error = computed(() => tagStore.error)
    
    const showCreateModal = ref(false)
    const showEditModal = ref(false)
    const showDeleteModal = ref(false)
    
    const newTag = reactive({
      name: '',
      description: '',
      color: '#4F46E5' // Default color (Indigo-600)
    })
    
    const editingTag = reactive({
      id: null,
      name: '',
      description: '',
      color: ''
    })
    
    const deleteTagId = ref(null)
    const deleteTagName = ref('')
    
    const fetchTags = async () => {
      loading.value = true
      try {
        console.log('TagList: Fetching tags from API')
        await tagStore.fetchTags()
      } catch (error) {
        console.error('Error fetching tags:', error)
      } finally {
        loading.value = false
      }
    }
    
    const createTag = async () => {
      try {
        console.log('TagList: Creating new tag:', newTag.name)
        const result = await tagStore.createTag({
          name: newTag.name,
          description: newTag.description || null,
          color: newTag.color
        })
        
        // Reset form
        newTag.name = ''
        newTag.description = ''
        newTag.color = '#4F46E5'
        
        // Close modal
        showCreateModal.value = false
        
        if (!result) {
          alert('Failed to create tag. Please try again.')
          return
        }
        
        // Refresh tags from API to ensure we have the latest data
        await fetchTags()
      } catch (error) {
        console.error('Error creating tag:', error)
        alert(`Failed to create tag: ${error.response?.data?.detail || error.message}`)
      }
    }
    
    const editTag = (tag) => {
      editingTag.id = tag.id
      editingTag.name = tag.name
      editingTag.description = tag.description || ''
      editingTag.color = tag.color || '#4F46E5'
      
      showEditModal.value = true
    }
    
    const updateTag = async () => {
      try {
        await tagStore.updateTag(editingTag.id, {
          name: editingTag.name,
          description: editingTag.description || null,
          color: editingTag.color
        })
        
        // Close modal
        showEditModal.value = false
        
        // Refresh tags
        await fetchTags()
      } catch (error) {
        console.error('Error updating tag:', error)
        alert(`Failed to update tag: ${error.response?.data?.detail || error.message}`)
      }
    }
    
    const confirmDelete = (tag) => {
      deleteTagId.value = tag.id
      deleteTagName.value = tag.name
      showDeleteModal.value = true
    }
    
    const deleteTag = async () => {
      try {
        await tagStore.deleteTag(deleteTagId.value)
        
        // Close modal
        showDeleteModal.value = false
        
        // Refresh tags
        await fetchTags()
      } catch (error) {
        console.error('Error deleting tag:', error)
        alert(`Failed to delete tag: ${error.response?.data?.detail || error.message}`)
      }
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      
      const date = new Date(dateString)
      return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      }).format(date)
    }
    
    // Ensure we fetch tags when the component is first mounted
    onMounted(() => {
      console.log('TagList: Component mounted, fetching tags')
      fetchTags()
    })
    
    // Also fetch tags when navigating back to this page
    onActivated(() => {
      console.log('TagList: Component activated, fetching fresh tag data')
      fetchTags()
    })
    
    return {
      tags,
      loading,
      showCreateModal,
      showEditModal,
      showDeleteModal,
      newTag,
      editingTag,
      deleteTagName,
      fetchTags,
      createTag,
      editTag,
      updateTag,
      confirmDelete,
      deleteTag,
      formatDate
    }
  }
}
</script> 