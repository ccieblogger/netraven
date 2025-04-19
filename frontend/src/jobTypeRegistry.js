// Job Type Registry for extensible job UI
// Add new job types here as needed
export const jobTypeRegistry = {
  reachability: {
    label: 'Check Reachability',
    icon: 'NetworkCheckIcon', // Placeholder, replace with actual icon component if needed
    resultComponent: 'ReachabilityResults', // Placeholder, can be a string or imported component
    logComponents: {
      job: 'JobLogTable',
      connection: 'ConnectionLogTable'
    }
  },
  backup: {
    label: 'Device Backup',
    icon: 'BackupIcon',
    resultComponent: 'BackupResults',
    logComponents: {
      job: 'JobLogTable'
    }
  }
  // Add more job types as needed
} 