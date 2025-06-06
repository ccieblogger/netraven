import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../store/auth'; // Import Pinia store for auth checks

// Import Page Components
import Login from '../pages/Login.vue';
import Dashboard from '../pages/Dashboard.vue'; // Use the consolidated dashboard component
import Devices from '../pages/Devices.vue';
import JobsDashboard from '../pages/JobsDashboard.vue';
import Logs from '../pages/Logs.vue';
import Users from '../pages/Users.vue';
import Unauthorized from '../pages/Unauthorized.vue';
import JobMonitor from '../pages/JobMonitor.vue'; // Import the JobMonitor component
import Tags from '../pages/Tags.vue'; // Import the Tags component
import Credentials from '../pages/Credentials.vue'; // Import the Credentials component
import ConnectionLogs from '../pages/Logs.vue';
import JobLogs from '../pages/JobLogs.vue';
import DeviceDetail from '../pages/DeviceDetail.vue';
import Jobs from '../pages/Jobs.vue';
import BulkDeviceImport from '../pages/BulkDeviceImport.vue'; // Import the BulkDeviceImport component

// Placeholder components for routes to work initially
// const PlaceholderComponent = { template: '<div>Placeholder Page</div>' }; // No longer needed

const routes = [
  { 
    path: '/', 
    redirect: '/dashboard' // Redirect root to dashboard
  },
  {
    path: '/login',
    name: 'Login',
    component: Login, // Use actual Login component
    meta: { requiresAuth: false }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard, // Use actual Dashboard component
    meta: { requiresAuth: true, roles: ['admin', 'user'] } 
  },
  {
    path: '/devices',
    name: 'Devices',
    component: Devices, // Use actual Devices component
    meta: { requiresAuth: true, roles: ['admin', 'user'] } 
  },
  {
    path: '/devices/:id',
    name: 'DeviceDetail',
    component: DeviceDetail,
    meta: { requiresAuth: true, roles: ['admin', 'user'] }
  },
  {
    path: '/devices/bulk-import',
    name: 'BulkDeviceImport',
    component: BulkDeviceImport,
    meta: { requiresAuth: true, roles: ['admin', 'user'] }
  },
  {
    path: '/tags',
    name: 'Tags',
    component: Tags, // Use the Tags component
    meta: { requiresAuth: true, roles: ['admin', 'user'] }
  },
  {
    path: '/credentials',
    name: 'Credentials',
    component: Credentials, // Use the Credentials component
    meta: { requiresAuth: true, roles: ['admin', 'user'] }
  },
  {
    path: '/jobs',
    name: 'Jobs',
    component: Jobs, // Use jobs list as default
    meta: { requiresAuth: true, roles: ['admin', 'user'] } 
  },
  {
    path: '/jobs-dashboard',
    name: 'JobsDashboard',
    component: JobsDashboard,
    meta: { requiresAuth: true, roles: ['admin', 'user'] }
  },
  {
    path: '/jobs/:id',
    name: 'JobMonitor',
    component: JobMonitor, // Use JobMonitor component
    meta: { requiresAuth: true, roles: ['admin', 'user'] }
  },
  {
    path: '/connection-logs',
    name: 'ConnectionLogs',
    component: ConnectionLogs,
    meta: { requiresAuth: true, roles: ['admin', 'user'] }
  },
  {
    path: '/job-logs',
    name: 'JobLogs',
    component: JobLogs,
    meta: { requiresAuth: true, roles: ['admin', 'user'] }
  },
  {
    path: '/logs',
    name: 'Logs',
    component: Logs,
    meta: { requiresAuth: true, roles: ['admin', 'user'] }
  },
  {
    path: '/users',
    name: 'Users',
    component: Users, // Use actual Users component
    meta: { requiresAuth: true, roles: ['admin'] } // Example: Admin only
  },
  {
    path: '/unauthorized',
    name: 'Unauthorized',
    component: Unauthorized, // Use actual Unauthorized component
    meta: { requiresAuth: false }
  },
  // Backups section
  {
    path: '/backups',
    component: () => import('../layouts/BackupsLayout.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'user'] },
    children: [
      { 
        path: 'snapshots', 
        name: 'Snapshots', 
        component: () => import('../pages/ConfigSnapshots.vue'),
        meta: { requiresAuth: true, roles: ['admin', 'user'] }
      },
      { 
        path: 'snapshots/:device/:snapshotId',
        name: 'ConfigRawView',
        component: () => import('../pages/ConfigRawView.vue'),
        meta: { requiresAuth: true, roles: ['admin', 'user'] }
      },
      // Add config diff as a child route
      {
        path: 'diff',
        name: 'ConfigDiff',
        component: () => import('../pages/ConfigDiff.vue'),
        meta: { requiresAuth: true, roles: ['admin', 'user'] }
      },
      { 
        path: 'schedules', 
        name: 'BackupSchedules', 
        component: () => import('../pages/BackupSchedules.vue'),
        meta: { requiresAuth: true, roles: ['admin', 'user'] }
      },
      { 
        path: 'audit-logs', 
        name: 'AuditLogs', 
        component: () => import('../pages/AuditLogs.vue'),
        meta: { requiresAuth: true, roles: ['admin', 'user'] }
      },
      // Redirect /backups to /backups/snapshots by default
      { path: '', redirect: 'snapshots' }
    ]
  },
  // Catch-all route (optional)
  // { path: '/:pathMatch(.*)*', name: 'NotFound', component: NotFoundComponent }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

// Navigation Guard (as per frontend_sot.md)
router.beforeEach(async (to, from, next) => { // Make async
  const requiresAuth = to.meta.requiresAuth;
  const requiredRoles = to.meta.roles;
  const auth = useAuthStore(); // Get auth store instance
  
  // Attempt to load user profile if token exists but user data is missing
  // This handles page refreshes where the store state is lost but token persists
  if (auth.token && !auth.user) {
     await auth.fetchUserProfile(); 
  }

  // Use computed properties from the store
  const isAuthenticated = auth.isAuthenticated; 
  const userRole = auth.userRole; 

  if (requiresAuth && !isAuthenticated) {
    // If route requires auth and user is not logged in, redirect to login
    console.log('Guard: Redirecting to login, requires auth.');
    next({ name: 'Login', query: { redirect: to.fullPath } }); // Pass redirect query
  } else if (requiresAuth && requiredRoles && !requiredRoles.includes(userRole)) {
    // If route requires specific role and user doesn't have it, redirect to unauthorized
    console.log(`Guard: Redirecting to unauthorized, requires role: ${requiredRoles}, user has: ${userRole}`);
    next({ name: 'Unauthorized' });
  } else {
    // Otherwise, allow navigation
    next();
  }
});

export default router;
