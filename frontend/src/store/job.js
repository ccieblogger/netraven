import { defineStore } from 'pinia';
import { ref } from 'vue';
import api from '../services/api';
// import { useNotificationStore } from './notifications'; // Optional for user feedback

export const useJobStore = defineStore('jobs', () => {
  // const notifications = useNotificationStore();
  const jobs = ref([]);
  const isLoading = ref(false);
  const error = ref(null);
  const runStatus = ref(null); // To store status of manual run trigger

  async function fetchJobs() {
    isLoading.value = true;
    error.value = null;
    try {
      const response = await api.get('/jobs/');
      // Handle pagination response structure
      if (response.data && response.data.items) {
        // API returns paginated response with items array
        jobs.value = response.data.items;
      } else if (Array.isArray(response.data)) {
        // Fallback for array response
        jobs.value = response.data;
      } else {
        // Default to empty array if response format is unexpected
        jobs.value = [];
      }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch jobs';
      console.error("Fetch Jobs Error:", err);
    } finally {
      isLoading.value = false;
    }
  }

  async function createJob(jobData) {
    isLoading.value = true;
    error.value = null;
    try {
      const response = await api.post('/jobs/', jobData);
      jobs.value.push(response.data);
      // notifications.addMessage({ type: 'success', text: 'Job created successfully' });
      return true;
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to create job';
      console.error("Create Job Error:", err);
      // notifications.addMessage({ type: 'error', text: error.value });
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  async function updateJob(jobId, jobData) {
    isLoading.value = true;
    error.value = null;
    try {
      const response = await api.put(`/jobs/${jobId}/`, jobData);
      const index = jobs.value.findIndex(j => j.id === jobId);
      if (index !== -1) {
        jobs.value[index] = response.data;
      }
      // notifications.addMessage({ type: 'success', text: 'Job updated successfully' });
      return true;
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update job';
      console.error("Update Job Error:", err);
      // notifications.addMessage({ type: 'error', text: error.value });
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  async function deleteJob(jobId) {
    isLoading.value = true;
    error.value = null;
    try {
      await api.delete(`/jobs/${jobId}/`);
      jobs.value = jobs.value.filter(j => j.id !== jobId);
      // notifications.addMessage({ type: 'success', text: 'Job deleted successfully' });
      return true;
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to delete job';
      console.error("Delete Job Error:", err);
      // notifications.addMessage({ type: 'error', text: error.value });
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  async function runJobNow(jobId) {
    runStatus.value = { jobId: jobId, status: 'running', error: null }; // Reset status
    try {
      const response = await api.post(`/jobs/run/${jobId}`);
      runStatus.value = { jobId: jobId, status: 'queued', data: response.data, error: null };
      // notifications.addMessage({ type: 'info', text: `Job ${jobId} queued successfully.` });
      return true;
    } catch (err) {
      const errorDetail = err.response?.data?.detail || 'Failed to trigger job run';
      runStatus.value = { jobId: jobId, status: 'failed', error: errorDetail };
      console.error(`Run Job ${jobId} Error:`, err);
      // notifications.addMessage({ type: 'error', text: errorDetail });
      return false;
    }
  }

  function $reset() {
    jobs.value = [];
    isLoading.value = false;
    error.value = null;
    runStatus.value = null;
  }

  return {
    jobs, isLoading, error, runStatus,
    fetchJobs, createJob, updateJob, deleteJob, runJobNow,
    $reset
  };
});
