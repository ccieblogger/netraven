import { createRouter, createWebHistory } from 'vue-router';
// import { useAuthStore } from '../store/auth'; // Import Pinia store for auth checks

// Placeholder Page Imports (create these components later)
// import Login from '../pages/Login.vue';
// import Dashboard from '../pages/Dashboard.vue';
// import Devices from '../pages/Devices.vue';
// import Jobs from '../pages/Jobs.vue';
// import Logs from '../pages/Logs.vue';
// import Users from '../pages/Users.vue';
// import Unauthorized from '../pages/Unauthorized.vue';

// Placeholder components for routes to work initially
const PlaceholderComponent = { template: '<div>Placeholder Page</div>' };

const routes = [
  { 
    path: '/', 
    redirect: '/dashboard' // Redirect root to dashboard
  },
  {
    path: '/login',
    name: 'Login',
    component: PlaceholderComponent, // Replace with actual Login component
    meta: { requiresAuth: false }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: PlaceholderComponent, // Replace with actual Dashboard component
    meta: { requiresAuth: true, roles: ['admin', 'user'] } 
  },
  {
    path: '/devices',
    name: 'Devices',
    component: PlaceholderComponent, // Replace with actual Devices component
    meta: { requiresAuth: true, roles: ['admin', 'user'] } 
  },
  {
    path: '/jobs',
    name: 'Jobs',
    component: PlaceholderComponent, // Replace with actual Jobs component
    meta: { requiresAuth: true, roles: ['admin', 'user'] } 
  },
  {
    path: '/logs',
    name: 'Logs',
    component: PlaceholderComponent, // Replace with actual Logs component
    meta: { requiresAuth: true, roles: ['admin', 'user'] } 
  },
  {
    path: '/users',
    name: 'Users',
    component: PlaceholderComponent, // Replace with actual Users component
    meta: { requiresAuth: true, roles: ['admin'] } // Example: Admin only
  },
  {
    path: '/unauthorized',
    name: 'Unauthorized',
    component: PlaceholderComponent, // Replace with actual Unauthorized component
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
router.beforeEach((to, from, next) => {
  const requiresAuth = to.meta.requiresAuth;
  const requiredRoles = to.meta.roles;
  // const auth = useAuthStore(); // Get auth store instance
  
  // Placeholder auth state (replace with Pinia store access)
  const isAuthenticated = false; // Example: Check auth.token
  const userRole = null; // Example: Get auth.role

  if (requiresAuth && !isAuthenticated) {
    // If route requires auth and user is not logged in, redirect to login
    console.log('Redirecting to login, requires auth.');
    next({ name: 'Login' });
  } else if (requiresAuth && requiredRoles && !requiredRoles.includes(userRole)) {
    // If route requires specific role and user doesn't have it, redirect to unauthorized
    console.log(`Redirecting to unauthorized, requires role: ${requiredRoles}, user has: ${userRole}`);
    next({ name: 'Unauthorized' });
  } else {
    // Otherwise, allow navigation
    next();
  }
});

export default router;
