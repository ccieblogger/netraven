import { defineStore } from 'pinia';
import axios from 'axios';

export const useBackupStore = defineStore('backup', {
  state: () => ({
    backups: 0, // Initialize backups count as 0
  }),
  actions: {
    async fetchBackups() {
      try {
        const response = await axios.get('/api/backups/count'); // Fetch the count of backups
        this.backups = response.data.count; // Store the count
      } catch (error) {
        console.error('Failed to fetch backups:', error);
      }
    },
  },
});