import { defineStore } from 'pinia';

export const useJobStore = defineStore('job', {
  state: () => ({
    selectedJobId: null, // ID of the job being viewed/monitored
    selectedJobDetails: null, // Full details of the selected job
    jobRunResults: [], // Results of devices for a specific job run
    recentJobs: [], // List of recent job runs for dashboard
  }),
  actions: {
    // Action to fetch and set details for a specific job
    async fetchJobDetails(jobId) {
      // Placeholder: Replace with API call using Axios
      // try {
      //   const response = await api.get(`/jobs/${jobId}`);
      //   this.selectedJobDetails = response.data;
      //   this.selectedJobId = jobId;
      // } catch (error) {
      //   console.error('Failed to fetch job details:', error);
      //   // Handle error (e.g., show notification)
      // }
      this.selectedJobId = jobId; // Temporary placeholder
      this.selectedJobDetails = { id: jobId, name: `Placeholder Job ${jobId}`, status: 'completed' }; // Placeholder
    },
    // Action to fetch results for a specific job run
    async fetchJobRunResults(jobId) {
      // Placeholder: Replace with API call
      // try {
      //   const response = await api.get(`/logs?job_id=${jobId}`); // Or a dedicated results endpoint
      //   this.jobRunResults = response.data;
      // } catch (error) {
      //   console.error('Failed to fetch job results:', error);
      // }
      this.jobRunResults = [ // Placeholder
          { device: 'core1', status: 'success', log_id: 88 },
          { device: 'edge2', status: 'fail', error: 'timeout', log_id: 89 }
      ];
    },
    // Action to fetch recent jobs for the dashboard
    async fetchRecentJobs() {
      // Placeholder: Replace with API call
      // try {
      //   const response = await api.get('/jobs?limit=10&sort=desc'); 
      //   this.recentJobs = response.data;
      // } catch (error) {
      //   console.error('Failed to fetch recent jobs:', error);
      // }
      this.recentJobs = [
          { id: 120, devices: 12, status: 'Success', runTime: '1:05' },
          { id: 121, devices: 8, status: 'Failed', runTime: '0:50' }
      ]; // Placeholder
    },
    // Action to clear selected job data when navigating away
    clearSelectedJob() {
      this.selectedJobId = null;
      this.selectedJobDetails = null;
      this.jobRunResults = [];
    }
  }
});
