import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Home from '../views/Home.vue'
import Map from '../views/Map.vue'
import Statistics from '../views/Statistics.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import ProfileView from '../views/Profile.vue'
import AdminView from '../views/AdminView.vue'

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

export default router
