import { reactive } from 'vue';
import axios from 'axios';

const backupStore = reactive({
  backups: 0,

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

export default backupStore;