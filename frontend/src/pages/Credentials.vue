<template>
  <div class="container mx-auto p-4">
    <h1 class="text-2xl font-semibold mb-4">Manage Credentials</h1>

    <!-- Add Credential Button -->
    <div class="mb-4 text-right">
      <button @click="openCreateModal" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
        + Add Credential
      </button>
    </div>

    <!-- Loading/Error Indicators -->
    <div v-if="credentialStore.isLoading" class="text-center py-4">Loading...</div>
    <div v-if="credentialStore.error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
       Error: {{ credentialStore.error }}
    </div>

    <!-- Credentials Table -->
    <div v-if="!credentialStore.isLoading && credentials.length > 0" class="bg-white shadow-md rounded my-6">
      <table class="min-w-max w-full table-auto">
        <thead>
          <tr class="bg-gray-200 text-gray-600 uppercase text-sm leading-normal">
            <th class="py-3 px-6 text-left">ID</th>
            <th class="py-3 px-6 text-left">Username</th>
            <th class="py-3 px-6 text-left">Description</th>
            <th class="py-3 px-6 text-left">Priority</th>
            <th class="py-3 px-6 text-left">Tags</th>
            <th class="py-3 px-6 text-center">Actions</th>
          </tr>
        </thead>
        <tbody class="text-gray-600 text-sm font-light">
          <tr v-for="cred in credentials" :key="cred.id" class="border-b border-gray-200 hover:bg-gray-100">
            <td class="py-3 px-6 text-left whitespace-nowrap">{{ cred.id }}</td>
            <td class="py-3 px-6 text-left">{{ cred.username }}</td>
            <td class="py-3 px-6 text-left">{{ cred.description || '-' }}</td>
            <td class="py-3 px-6 text-left">{{ cred.priority }}</td>
            <td class="py-3 px-6 text-left">
              <span v-for="tag in cred.tags" :key="tag.id" class="bg-blue-100 text-blue-600 py-1 px-3 rounded-full text-xs mr-1">
                {{ tag.name }}
              </span>
              <span v-if="!cred.tags || cred.tags.length === 0">-</span>
            </td>
            <td class="py-3 px-6 text-center">
              <div class="flex item-center justify-center">
                 <button @click="openEditModal(cred)" class="w-4 mr-2 transform hover:text-purple-500 hover:scale-110">✏️</button>
                 <button @click="confirmDelete(cred)" class="w-4 mr-2 transform hover:text-red-500 hover:scale-110">🗑️</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- No Credentials Message -->
    <div v-if="!credentialStore.isLoading && credentials.length === 0" class="text-center text-gray-500 py-6">
      No credentials found. Add one!
    </div>

    <!-- TODO: Add Create/Edit Modal Component (requires tag selection) -->

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useCredentialStore } from '../store/credential'

const credentialStore = useCredentialStore()
const credentials = computed(() => credentialStore.credentials)

// Modal state placeholders
const showModal = ref(false)
const selectedCredential = ref(null)
const isEditMode = ref(false)

onMounted(() => {
  credentialStore.fetchCredentials()
})

// Placeholder actions
function openCreateModal() {
  alert('Placeholder: Open Create Credential Modal');
}
function openEditModal(cred) {
   alert(`Placeholder: Open Edit Credential Modal for ${cred.username}`);
}
function confirmDelete(cred) {
  if (confirm(`Are you sure you want to delete the credential set "${cred.username}"?`)) {
     alert(`Placeholder: Delete credential ${cred.id}`);
     // credentialStore.deleteCredential(cred.id);
  }
}
function closeModal() { /* ... */ }
async function handleSave(data) { /* ... */ }

</script>

<style scoped>
/* Add any page-specific styles */
</style> 