import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Home from '../views/Home.vue'
import Map from '../views/Map.vue'
import Statistics from '../views/Statistics.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import ProfileView from '../views/Profile.vue'
import AdminView from '../views/AdminView.vue'
import UploadView from '../views/UploadView.vue'
import TourDetailView from '../views/TourDetailView.vue'
import ToursBrowseView from '../views/ToursBrowseView.vue'
import VerifyEmail from '../views/VerifyEmail.vue'

const routes = [
  {
    path: '/admin',
    name: 'Admin',
    component: AdminView,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterView,
    meta: { requiresAuth: false }
  },
  {
    path: '/verify-email',
    name: 'VerifyEmail',
    component: VerifyEmail,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { requiresAuth: true }
  },
  {
    path: '/map',
    name: 'Map',
    component: Map,
    meta: { requiresAuth: true }
  },
  {
    path: '/statistics',
    name: 'Statistics',
    component: Statistics,
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: ProfileView,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: AdminView,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/upload',
    name: 'Upload',
    component: UploadView,
    meta: { requiresAuth: true }
  },
  {
    path: '/tour/:id',
    name: 'TourDetail',
    component: TourDetailView,
    meta: { requiresAuth: true }
  },
  {
    path: '/tours',
    name: 'ToursBrowse',
    component: ToursBrowseView,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // Check if route requires auth
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return next({ name: 'Login' })
  }
  
  // Check if route requires admin
  if (to.meta.requiresAdmin) {
    console.log('Admin check:', {
      user: authStore.user,
      role: authStore.user?.role,
      isAdmin: authStore.isAdmin,
      route: to.path
    })
    if (!authStore.isAdmin) {
      console.log('Admin access denied')
      return next({ name: 'Home' })
    }
  }
  
  // If trying to access login/register while authenticated
  if ((to.name === 'Login' || to.name === 'Register') && authStore.isAuthenticated) {
    return next({ name: 'Home' })
  }
  
  next()
})

// Make router instance available globally for programmatic navigation from outside Vue components
// This allows the API interceptor to redirect to login when token expires
window.__VUE_ROUTER__ = router

export default router
