<template>
  <div class="tour-detail">
    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Lade Tour-Details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <h2>Fehler beim Laden der Tour</h2>
      <p>{{ error }}</p>
      <button @click="loadTourData" class="btn btn-primary">Erneut versuchen</button>
      <router-link to="/" class="btn btn-secondary">Zurück zur Übersicht</router-link>
    </div>

    <!-- Tour Data -->
    <div v-else-if="tour" class="tour-content">
      <!-- Back Navigation -->
      <div class="back-nav">
        <router-link to="/" class="btn btn-text">
          ← Zurück zur Übersicht
        </router-link>
      </div>

      <!-- Tour Header -->
      <header class="tour-header">
        <h1>{{ tour.name }}</h1>
        <div class="tour-badges">
          <span :class="['type-badge', `type-${tour.type.toLowerCase()}`]">
            {{ tour.type }}
          </span>
          <span v-if="tour.ebike" class="ebike-badge">⚡ E-Bike</span>
          <span class="date-badge">📅 {{ formatDate(tour.date) }}</span>
        </div>
      </header>

      <!-- Tour Map -->
      <section class="tour-map-container" ref="mapContainer">
        <h2>Streckenverlauf</h2>
        <div class="map-wrapper">
          <div id="tour-map" class="tour-map"></div>
          <div v-if="!tour.track_geojson" class="no-map-data">
            Keine Geodaten für diese Tour verfügbar
          </div>
        </div>
      </section>

      <!-- Tour Stats -->
      <section class="tour-stats">
        <h2>Tour-Daten</h2>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">📏</div>
            <div class="stat-value">{{ formatDistance(tour.distance_km) }}</div>
            <div class="stat-label">Distanz</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">⏱️</div>
            <div class="stat-value">{{ formatDuration(tour.duration_s) }}</div>
            <div class="stat-label">Dauer</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">🏃</div>
            <div class="stat-value">{{ formatSpeed(tour.speed_kmh) }}</div>
            <div class="stat-label">Geschwindigkeit</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">⛰️</div>
            <div class="stat-value">{{ formatElevation(tour.elevation_up) }}</div>
            <div class="stat-label">Höhenmeter (Aufstieg)</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">🏔️</div>
            <div class="stat-value">{{ formatElevation(tour.elevation_down) }}</div>
            <div class="stat-label">Höhenmeter (Abstieg)</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">📌</div>
            <div class="stat-value">{{ formatCoordinates(tour.start_lat, tour.start_lon) }}</div>
            <div class="stat-label">Startpunkt</div>
          </div>
        </div>
      </section>

      <!-- External Links -->
      <section class="tour-links" v-if="tour.komoothref">
        <h2>Externe Links</h2>
        <a :href="tour.komoothref" target="_blank" class="btn btn-primary">
          <span class="icon">🔗</span> Auf Komoot ansehen
        </a>
      </section>

      <!-- Nearby Tours -->
      <section class="nearby-tours" v-if="nearbyTours.length > 0">
        <h2>Ähnliche Touren in der Nähe</h2>
        <div class="tour-cards">
          <TourCard 
            v-for="nearbyTour in nearbyTours" 
            :key="nearbyTour.id" 
            :tour="nearbyTour"
            :view-mode="'cards'"
          />
        </div>
      </section>
    </div>

    <!-- Tour Not Found -->
    <div v-else class="not-found-container">
      <h2>Tour nicht gefunden</h2>
      <p>Die angegebene Tour konnte nicht gefunden werden.</p>
      <router-link to="/" class="btn btn-primary">Zurück zur Übersicht</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'
import { useTourStore } from '../stores/tours'
import { useToastStore } from '../stores/toast'
import TourCard from '../components/TourCard.vue'

// Initialize Leaflet in a way that works with Vite
let L

// Map reference
const map = ref(null)
const mapContainer = ref(null)

// Stores
const tourStore = useTourStore()
const toastStore = useToastStore()
const { loading, error } = storeToRefs(tourStore)
const tour = ref(null)

// Route & Router
const route = useRoute()
const router = useRouter()

// Nearby Tours
const nearbyTours = ref([])

// Watch for route changes to load new tour data
watch(
  () => route.params.id,
  (newId) => {
    if (newId) {
      loadTourData()
    }
  }
)

// Format utilities
const formatDate = (dateString) => {
  try {
    return format(new Date(dateString), 'dd. MMMM yyyy', { locale: de })
  } catch {
    return dateString
  }
}

const formatDistance = (distance) => {
  return `${distance.toFixed(1)} km`
}

const formatDuration = (seconds) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (hours > 0) {
    return `${hours} Std ${minutes} Min`
  }
  return `${minutes} Minuten`
}

const formatSpeed = (speed) => {
  return `${speed.toFixed(1)} km/h`
}

const formatElevation = (elevation) => {
  return `${Math.round(elevation)} m`
}

const formatCoordinates = (lat, lon) => {
  return `${lat.toFixed(5)}, ${lon.toFixed(5)}`
}

// Load tour data by ID
const loadTourData = async () => {
  const tourId = parseInt(route.params.id)
  if (!tourId) {
    router.push('/')
    return
  }

  try {
    tour.value = await tourStore.fetchTourDetail(tourId)
    
    // After getting the tour, load nearby tours based on start location
    if (tour.value) {
      loadNearbyTours()
      
      // Setup map after tour data is loaded
      setTimeout(() => {
        initMap()
      }, 100)
    }
  } catch (err) {
    toastStore.error('Fehler beim Laden der Tour')
    console.error('Error loading tour:', err)
  }
}

// Load nearby tours based on start location
const loadNearbyTours = async () => {
  try {
    if (!tour.value) return
    
    const { start_lat, start_lon, id } = tour.value
    const nearby = await tourStore.fetchNearbyTours(start_lat, start_lon, 10)
    
    // Filter out the current tour
    nearbyTours.value = nearby.filter(t => t.id !== id).slice(0, 3)
  } catch (err) {
    console.error('Error loading nearby tours:', err)
  }
}

// Initialize map with tour data
const initMap = async () => {
  if (!tour.value?.track_geojson) return

  // Dynamically import Leaflet
  if (!L) {
    const leaflet = await import('leaflet')
    L = leaflet.default
    
    // Import CSS
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = 'https://unpkg.com/leaflet@1.7.1/dist/leaflet.css'
    document.head.appendChild(link)
  }

  // Initialize map if container exists
  const mapDiv = document.getElementById('tour-map')
  if (!mapDiv) return

  // Create map if it doesn't exist
  if (!map.value) {
    map.value = L.map('tour-map')
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map.value)
  }

  // Add tour track to map
  try {
    const trackData = tour.value.track_geojson
    const geoJsonLayer = L.geoJSON(trackData, {
      style: {
        color: '#3388ff',
        weight: 5,
        opacity: 0.8
      }
    }).addTo(map.value)

    // Fit map to track bounds
    map.value.fitBounds(geoJsonLayer.getBounds())

    // Add start/end markers if coordinates exist
    if (trackData.coordinates && trackData.coordinates.length > 0) {
      // Start marker
      const startCoords = trackData.coordinates[0]
      L.marker([startCoords[1], startCoords[0]], {
        icon: L.divIcon({
          html: '🚩',
          iconSize: [20, 20],
          className: 'start-marker'
        })
      }).addTo(map.value)

      // End marker
      const endCoords = trackData.coordinates[trackData.coordinates.length - 1]
      L.marker([endCoords[1], endCoords[0]], {
        icon: L.divIcon({
          html: '🏁',
          iconSize: [20, 20],
          className: 'end-marker'
        })
      }).addTo(map.value)
    }
  } catch (error) {
    console.error('Error rendering map:', error)
    toastStore.error('Fehler beim Laden der Karte')
  }
}

// Lifecycle hooks
onMounted(() => {
  loadTourData()
})
</script>

<style scoped>
.tour-detail {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
}

.loading-container,
.error-container,
.not-found-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  text-align: center;
}

.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top: 4px solid #3498db;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.back-nav {
  margin-bottom: 1rem;
}

.tour-header {
  margin-bottom: 2rem;
}

.tour-header h1 {
  margin-bottom: 0.5rem;
  font-size: 1.8rem;
}

.tour-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.type-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
  background-color: #e0e0e0;
}

.type-fahrradtour {
  background-color: #4caf50;
  color: white;
}

.type-wanderung {
  background-color: #ff9800;
  color: white;
}

.type-lauf {
  background-color: #2196f3;
  color: white;
}

.type-inline {
  background-color: #9c27b0;
  color: white;
}

.ebike-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
  background-color: #f39c12;
  color: white;
}

.date-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
  background-color: #e0e0e0;
}

.tour-map-container {
  margin-bottom: 2rem;
}

.map-wrapper {
  position: relative;
  height: 400px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.tour-map {
  height: 100%;
}

.no-map-data {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  font-weight: 500;
  color: #666;
}

.tour-stats {
  margin-bottom: 2rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1rem;
}

.stat-card {
  background-color: white;
  border-radius: 12px;
  padding: 1rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.stat-icon {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.9rem;
  color: #666;
}

.tour-links {
  margin-bottom: 2rem;
}

.nearby-tours h2 {
  margin-bottom: 1rem;
}

.tour-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

/* Responsive styles */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }
  
  .map-wrapper {
    height: 300px;
  }
}
</style>
