import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

// Leaflet CSS (required for maps to work properly)
import 'leaflet/dist/leaflet.css'

// Views
import Home from './views/Home.vue'
import TourDetail from './views/TourDetail.vue'
import Map from './views/Map.vue'
import Statistics from './views/Statistics.vue'

// PWA Registration
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(registration => {
        console.log('SW registered: ', registration)
      })
      .catch(registrationError => {
        console.log('SW registration failed: ', registrationError)
      })
  })
}

// Router Setup
const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/tour/:id', name: 'TourDetail', component: TourDetail, props: true },
  { path: '/map', name: 'Map', component: Map },
  { path: '/statistics', name: 'Statistics', component: Statistics }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Pinia Store
const pinia = createPinia()

// Create App
const app = createApp(App)
app.use(pinia)
app.use(router)
app.mount('#app')
