import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../store/auth'; // Import Pinia store for auth checks

// Import Page Components
import Login from '../pages/Login.vue';
import Dashboard from '../pages/Dashboard.vue';
import Devices from '../pages/Devices.vue';
import Jobs from '../pages/Jobs.vue';
import Logs from '../pages/Logs.vue';
import Users from '../pages/Users.vue';
import Unauthorized from '../pages/Unauthorized.vue';

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
    path: '/jobs',
    name: 'Jobs',
    component: Jobs, // Use actual Jobs component
    meta: { requiresAuth: true, roles: ['admin', 'user'] } 
  },
  {
    path: '/logs',
    name: 'Logs',
    component: Logs, // Use actual Logs component
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
