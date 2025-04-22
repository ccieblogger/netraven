import api from './api' // assumes you have an axios instance exported from api.js

const jobsDashboardService = {
  getScheduledJobs() { return api.get('/jobs/scheduled') },
  getRecentJobs() { return api.get('/jobs/recent') },
  getJobTypes() { return api.get('/jobs/job-types') },
  getSystemStatus() { return api.get('/jobs/status') },
}

export default jobsDashboardService 