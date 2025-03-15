import { createRouter, createWebHistory } from 'vue-router'

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
    path: '/job-logs',
    name: 'JobLogs',
    component: JobLogList,
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
  }
]

// Create router
const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// Robust navigation guard for authentication
router.beforeEach((to, from, next) => {
  console.log(`Router: Navigating from ${from.path || '/'} to ${to.path}`);

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
    // Store the intended destination to redirect after login
    const redirectPath = to.path !== '/' ? to.fullPath : undefined;
    return next({
      path: '/login',
      query: redirectPath ? { redirect: redirectPath } : {}
    });
  }
  
  // User has token, allow navigation
  next();
});

export default router 