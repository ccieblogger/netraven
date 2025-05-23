<template>
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-semibold mb-4">Manage Tags</h1>

    <!-- Add Tag Button -->
    <div class="mb-4 text-right">
      <button @click="openCreateModal" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
        + Add Tag
      </button>
    </div>

    <!-- Loading Indicator -->
    <div v-if="tagStore.isLoading" class="text-center py-4">Loading...</div>

    <!-- Error Display -->
    <div v-if="tagStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
      <strong class="font-bold">Error!</strong>
      <span class="block sm:inline"> {{ tagStore.error }}</span>
    </div>

    <!-- Tags Table -->
    <div v-if="!tagStore.isLoading && tags.length > 0" class="bg-white shadow-md rounded my-6">
      <table class="min-w-max w-full table-auto">
        <thead>
          <tr class="bg-gray-200 text-gray-600 uppercase text-sm leading-normal">
            <th class="py-3 px-6 text-left">ID</th>
            <th class="py-3 px-6 text-left">Name</th>
            <th class="py-3 px-6 text-left">Type</th>
            <th class="py-3 px-6 text-center">Actions</th>
          </tr>
        </thead>
        <tbody class="text-gray-600 text-sm font-light">
          <tr v-for="tag in tags" :key="tag.id" class="border-b border-gray-200 hover:bg-gray-100">
            <td class="py-3 px-6 text-left whitespace-nowrap">
              {{ tag.id }}
            </td>
            <td class="py-3 px-6 text-left">
              {{ tag.name }}
            </td>
             <td class="py-3 px-6 text-left">
              {{ tag.type || '-' }}
            </td>
            <td class="py-3 px-6 text-center">
              <div class="flex item-center justify-center">
                <button @click="openEditModal(tag)" class="w-4 mr-2 transform hover:text-purple-500 hover:scale-110">
                  <!-- Edit Icon Placeholder -->✏️
                </button>
                <button @click="confirmDelete(tag)" class="w-4 mr-2 transform hover:text-red-500 hover:scale-110">
                  <!-- Delete Icon Placeholder -->🗑️
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

     <!-- No Tags Message -->
    <div v-if="!tagStore.isLoading && tags.length === 0" class="text-center text-gray-500 py-6">
      No tags found. Add one!
    </div>

    <!-- TODO: Add Create/Edit Modal Component -->
    <TagFormModal
      v-if="showModal"
      :is-open="showModal"
      :tag-to-edit="isEditMode ? selectedTag : null"
      :backend-error="modalBackendError"
      @close="closeModal"
      @save="handleSave"
    />

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useTagStore } from '../store/tag'
import TagFormModal from '../components/TagFormModal.vue'

const tagStore = useTagStore()

// Compute tags from store
const tags = computed(() => tagStore.tags)

// Modal state
const showModal = ref(false)
const selectedTag = ref(null) // For editing
const isEditMode = ref(false)
const modalBackendError = ref('')

// Fetch tags when component mounts
onMounted(() => {
  tagStore.fetchTags()
})

// --- CRUD Action Handlers ---
function openCreateModal() {
  selectedTag.value = { name: '', type: '' }
  isEditMode.value = false
  modalBackendError.value = ''
  showModal.value = true
}

function openEditModal(tag) {
  selectedTag.value = { ...tag }
  isEditMode.value = true
  modalBackendError.value = ''
  showModal.value = true
}

function confirmDelete(tag) {
  if (confirm(`Are you sure you want to delete the tag "${tag.name}"?`)) {
    tagStore.deleteTag(tag.id)
  }
}

function closeModal() {
  showModal.value = false
  selectedTag.value = null
  modalBackendError.value = ''
}

async function handleSave(tagData) {
  let success = false
  modalBackendError.value = ''
  if (isEditMode.value && selectedTag.value && selectedTag.value.id) {
    success = await tagStore.updateTag(selectedTag.value.id, tagData)
  } else {
    success = await tagStore.createTag(tagData)
  }
  if (success) {
    closeModal()
  } else {
    // Show backend error if present
    modalBackendError.value = tagStore.error || 'Failed to save tag.'
  }
}

</script>

<style scoped>
/* Add any page-specific styles */
</style> 