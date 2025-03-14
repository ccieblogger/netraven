import { createRouter, createWebHistory } from 'vue-router'

// Import views
import Dashboard from '../views/Dashboard.vue'
import DeviceList from '../views/DeviceList.vue'
import DeviceDetail from '../views/DeviceDetail.vue'
import BackupList from '../views/BackupList.vue'
import BackupDetail from '../views/BackupDetail.vue'
import TagList from '../views/TagList.vue'
import TagRuleList from '../views/TagRuleList.vue'
import Login from '../views/Login.vue'
import RouteTest from '../views/RouteTest.vue'

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

  // Skip authentication check for login and public pages
  if (to.path === '/login') {
    return next();
  }

  // Check if user is authenticated
  const token = localStorage.getItem('access_token');
  
  if (!token) {
    console.log('Router: No token found, redirecting to login');
    return next('/login');
  }
  
  // User has token, allow navigation
  next();
});

export default router 