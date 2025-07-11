import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// Leaflet CSS (required for maps to work properly)
import 'leaflet/dist/leaflet.css'

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

// Pinia Store
const pinia = createPinia()

// Create App
const app = createApp(App)
app.use(pinia)
app.use(router)
app.mount('#app')
