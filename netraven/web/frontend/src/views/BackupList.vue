<template>
  <MainLayout>
    <h1 class="text-2xl font-bold mb-6">Backup List</h1>
    
    <div v-if="loading" class="text-center py-8">
      <p>Loading backups...</p>
    </div>
    
    <div v-else-if="backups.length === 0" class="text-center py-8 bg-white rounded-lg shadow p-6">
      <p class="text-gray-500">No backups found.</p>
      <button 
        @click="refreshBackups" 
        class="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
      >
        Refresh
      </button>
    </div>
    
    <div v-else class="bg-white rounded-lg shadow overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Device
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Date
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="backup in backups" :key="backup.id">
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="flex items-center">
                <div class="text-sm font-medium text-gray-900">
                  {{ backup.device_name || backup.device_id }}
                </div>
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm text-gray-900">{{ formatDate(backup.created_at) }}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                :class="statusClass(backup.status)">
                {{ backup.status }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
              <router-link :to="`/backups/${backup.id}`" class="text-blue-600 hover:text-blue-900 mr-3">
                View
              </router-link>
              <button 
                @click="restoreBackup(backup.id)" 
                class="text-green-600 hover:text-green-900" 
                :disabled="backup.status !== 'success'"
              >
                Restore
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </MainLayout>
</template>

<script>
import { ref, onMounted } from 'vue';
import MainLayout from '../components/MainLayout.vue';
import { useBackupStore } from '../store/backups';

export default {
  name: 'BackupList',
  components: {
    MainLayout
  },
  setup() {
    const backupStore = useBackupStore();
    const loading = ref(true);
    const backups = ref([]);

    const fetchBackups = async () => {
      loading.value = true;
      try {
        await backupStore.fetchBackups();
        backups.value = backupStore.backups;
      } catch (error) {
        console.error('Failed to fetch backups:', error);
      } finally {
        loading.value = false;
      }
    };

    const refreshBackups = () => {
      fetchBackups();
    };

    const formatDate = (dateString) => {
      if (!dateString) return 'Unknown';
      const date = new Date(dateString);
      return date.toLocaleString();
    };

    const statusClass = (status) => {
      switch (status) {
        case 'success':
          return 'bg-green-100 text-green-800';
        case 'failed':
          return 'bg-red-100 text-red-800';
        case 'in_progress':
          return 'bg-yellow-100 text-yellow-800';
        default:
          return 'bg-gray-100 text-gray-800';
      }
    };

    const restoreBackup = async (backupId) => {
      try {
        await backupStore.restoreBackup(backupId);
        // Optionally show a success message
      } catch (error) {
        console.error('Failed to restore backup:', error);
      }
    };

    onMounted(() => {
      fetchBackups();
    });

    return {
      loading,
      backups,
      refreshBackups,
      formatDate,
      statusClass,
      restoreBackup
    };
  }
};
</script> 