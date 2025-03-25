import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../store/auth'

// Import views
import Dashboard from '../views/Dashboard.vue'
import DeviceList from '../views/DeviceList.vue'
import DeviceDetail from '../views/DeviceDetail.vue'
import BackupList from '../views/BackupList.vue'
import BackupDetail from '../views/BackupDetail.vue'
import TagList from '../views/TagList.vue'
import TagRuleList from '../views/TagRuleList.vue'
import JobLogList from '../views/JobLogList.vue'
import JobLogDetail from '../views/JobLogDetail.vue'
import ScheduledJobList from '../views/ScheduledJobList.vue'
import Login from '../views/Login.vue'
import RouteTest from '../views/RouteTest.vue'
import GatewayDashboard from '../views/GatewayDashboard.vue'
import CredentialList from '../views/CredentialList.vue'
import CredentialDashboard from '../views/CredentialDashboard.vue'
import CredentialAnalytics from '../views/CredentialAnalytics.vue'
import KeyManagement from '@/views/KeyManagement.vue'
import AdminSettings from '@/views/AdminSettings.vue'
import AuditLogs from '@/views/AuditLogs.vue'

// Define routes
const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/devices',
    name: 'Devices',
    component: DeviceList,
    meta: { requiresAuth: true }
  },
  {
    path: '/devices/:id',
    name: 'DeviceDetail',
    component: DeviceDetail,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/backups',
    name: 'Backups',
    component: BackupList,
    meta: { requiresAuth: true }
  },
  {
    path: '/backups/:id',
    name: 'BackupDetail',
    component: BackupDetail,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/tags',
    name: 'Tags',
    component: TagList,
    meta: { requiresAuth: true }
  },
  {
    path: '/tag-rules',
    name: 'TagRules',
    component: TagRuleList,
    meta: { requiresAuth: true }
  },
  {
    path: '/credentials',
    name: 'Credentials',
    component: CredentialList,
    meta: { requiresAuth: true }
  },
  {
    path: '/credentials/dashboard',
    name: 'CredentialDashboard',
    component: CredentialDashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/credentials/analytics',
    name: 'CredentialAnalytics',
    component: CredentialAnalytics,
    meta: { requiresAuth: true }
  },
  {
    path: '/job-logs',
    name: 'JobLogs',
    component: JobLogList,
    meta: { requiresAuth: true }
  },
  {
    path: '/job-logs/device/:deviceId',
    name: 'DeviceJobLogs',
    component: JobLogList,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/job-logs/:id',
    name: 'JobLogDetail',
    component: JobLogDetail,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/scheduled-jobs',
    name: 'ScheduledJobs',
    component: ScheduledJobList,
    meta: { requiresAuth: true }
  },
  {
    path: '/gateway',
    name: 'Gateway',
    component: GatewayDashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/route-test',
    name: 'RouteTest',
    component: RouteTest,
    meta: { requiresAuth: false }
  },
  {
    path: '/keys',
    name: 'KeyManagement',
    component: KeyManagement,
    meta: {
      requiresAuth: true,
      adminOnly: true
    }
  },
  {
    path: '/admin-settings',
    name: 'AdminSettings',
    component: AdminSettings,
    meta: {
      requiresAuth: true,
      adminOnly: true
    }
  },
  {
    path: '/audit-logs',
    name: 'AuditLogs',
    component: AuditLogs,
    meta: {
      requiresAuth: true,
      adminOnly: true
    }
  }
]

// Create router
const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// Robust navigation guard for authentication
router.beforeEach((to, from, next) => {
  console.log('Router navigation: from', from.path, 'to', to.path);
  console.log('Router matched route:', to.matched);
  
  // Check if the route requires authentication
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false);
  
  // Skip authentication check for login and public pages
  if (to.path === '/login' || !requiresAuth) {
    // If user is already logged in and tries to access login page, redirect to dashboard
    if (to.path === '/login' && localStorage.getItem('access_token')) {
      console.log('Router: User already logged in, redirecting to dashboard');
      return next('/');
    }
    return next();
  }

  // Check if user is authenticated
  const token = localStorage.getItem('access_token');
  
  if (!token) {
    console.log('Router: No token found, redirecting to login');
    // Save the intended route to redirect after login
    localStorage.setItem('redirect_after_login', to.fullPath);
    return next('/login');
  }
  
  // Check if route requires admin role
  const adminOnly = to.matched.some(record => record.meta.adminOnly);
  
  // If route requires admin privileges, verify user role
  if (adminOnly) {
    const authStore = useAuthStore();
    
    if (!authStore.hasRole('admin')) {
      console.log('Router: User is not an admin, access denied');
      return next('/');  // Redirect to dashboard
    }
  }
  
  return next();
});

export default router 