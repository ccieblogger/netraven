import { defineStore } from 'pinia'
import jobsDashboardService from '../services/jobsDashboardService'

export const useJobsDashboardStore = defineStore('jobsDashboard', {
  state: () => ({
    scheduledJobs: [],
    recentJobs: [],
    jobTypes: [],
    systemStatus: null,
    loading: false,
    error: null,
  }),
  actions: {
    async fetchScheduledJobs() {
      this.loading = true; this.error = null;
      try {
        const res = await jobsDashboardService.getScheduledJobs();
        this.scheduledJobs = res.data;
      } catch (e) {
        this.error = e.message || 'Failed to load scheduled jobs';
      } finally {
        this.loading = false;
      }
    },
    async fetchRecentJobs() {
      this.loading = true; this.error = null;
      try {
        const res = await jobsDashboardService.getRecentJobs();
        this.recentJobs = res.data;
      } catch (e) {
        this.error = e.message || 'Failed to load recent jobs';
      } finally {
        this.loading = false;
      }
    },
    async fetchJobTypes() {
      this.loading = true; this.error = null;
      try {
        const res = await jobsDashboardService.getJobTypes();
        this.jobTypes = res.data;
      } catch (e) {
        this.error = e.message || 'Failed to load job types';
      } finally {
        this.loading = false;
      }
    },
    async fetchSystemStatus() {
      this.loading = true; this.error = null;
      try {
        const res = await jobsDashboardService.getSystemStatus();
        this.systemStatus = res.data;
      } catch (e) {
        this.error = e.message || 'Failed to load system status';
      } finally {
        this.loading = false;
      }
    },
    async fetchAll() {
      this.loading = true; this.error = null;
      try {
        await Promise.all([
          this.fetchScheduledJobs(),
          this.fetchRecentJobs(),
          this.fetchJobTypes(),
          this.fetchSystemStatus()
        ]);
      } catch (e) {
        this.error = e.message || 'Failed to load dashboard data';
      } finally {
        this.loading = false;
      }
    }
  }
}) 