<template>
  <!-- Using the same structure as DefaultLayout but focusing on Backups-specific content -->
  <div class="p-2">
    <!-- Tabs for easy navigation between backup sections -->
    <div class="mb-4 border-b border-divider">
      <nav class="-mb-px flex space-x-6" aria-label="Backups navigation">
        <router-link
          to="/backups/configurations"
          class="py-2 px-1 border-b-2 font-medium text-sm"
          :class="[
            route.path.includes('/configurations') 
              ? 'border-primary text-primary' 
              : 'border-transparent text-text-secondary hover:border-gray-300 hover:text-text-primary'
          ]"
        >
          Configuration Snapshots
        </router-link>
        <router-link
          to="/backups/schedules"
          class="py-2 px-1 border-b-2 font-medium text-sm"
          :class="[
            route.path.includes('/schedules') 
              ? 'border-primary text-primary' 
              : 'border-transparent text-text-secondary hover:border-gray-300 hover:text-text-primary'
          ]"
        >
          Backup Schedules
        </router-link>
        <router-link
          to="/backups/audit-logs"
          class="py-2 px-1 border-b-2 font-medium text-sm"
          :class="[
            route.path.includes('/audit-logs') 
              ? 'border-primary text-primary' 
              : 'border-transparent text-text-secondary hover:border-gray-300 hover:text-text-primary'
          ]"
        >
          Audit Logs
        </router-link>
      </nav>
    </div>
    
    <!-- Router view for the selected backup section -->
    <router-view />
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router';

const route = useRoute();
</script>
