<template>
  <div class="tour-detail">
    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Lade Tour-Details...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-state">
      <h2>❌ Fehler</h2>
      <p>{{ error }}</p>
      <router-link to="/" class="btn btn-primary">
        🏠 Zurück zur Übersicht
      </router-link>
    </div>

    <!-- Tour Details -->
    <div v-else-if="localTour" class="tour-content">
      <!-- Header -->
      <div class="tour-header">
        <div class="tour-title">
          <h1>{{ localTour.name }}</h1>
          <div class="tour-badges">
            <span :class="['type-badge', `type-${localTour.type.toLowerCase()}`]">
              {{ localTour.type }}
            </span>
            <span v-if="localTour.ebike" class="ebike-badge">
              ⚡ E-Bike
            </span>
          </div>
        </div>
        <div class="tour-actions">
          <button @click="goBack" class="btn btn-secondary">
            ← Zurück
          </button>
          <a 
            v-if="localTour?.komoothref" 
            :href="localTour.komoothref" 
            target="_blank" 
            class="btn btn-primary"
          >
            🔗 Komoot öffnen
          </a>
        </div>
      </div>

      <!-- Stats Grid -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">📏</div>
          <div class="stat-content">
            <div class="stat-value">{{ localTour.distance_km.toFixed(1) }} km</div>
            <div class="stat-label">Distanz</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">⏱️</div>
          <div class="stat-content">
            <div class="stat-value">{{ formatDuration(localTour.duration_s) }}</div>
            <div class="stat-label">Dauer</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">🏃</div>
          <div class="stat-content">
            <div class="stat-value">{{ localTour.speed_kmh.toFixed(1) }} km/h</div>
            <div class="stat-label">Ø Geschwindigkeit</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">⛰️</div>
          <div class="stat-content">
            <div class="stat-value">{{ Math.round(localTour.elevation_up) }} m</div>
            <div class="stat-label">Höhenmeter ↗</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">📅</div>
          <div class="stat-content">
            <div class="stat-value">{{ formatDate(localTour.date) }}</div>
            <div class="stat-label">Datum</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">📍</div>
          <div class="stat-content">
            <div class="stat-value">{{ formatCoordinate(localTour.start_lat, localTour.start_lon) }}</div>
            <div class="stat-label">Startpunkt</div>
          </div>
        </div>
      </div>

      <!-- Map -->
      <div class="tour-map-section">
        <div class="section-header">
          <h2>🗺️ Route</h2>
          <div class="map-controls">
            <button @click="centerOnTrack" class="btn btn-secondary">
              🎯 Route zentrieren
            </button>
            <button @click="toggleFullscreen" class="btn btn-secondary">
              {{ isFullscreen ? '↙️ Verkleinern' : '↗️ Vollbild' }}
            </button>
          </div>
        </div>
        
        <div 
          ref="mapContainer" 
          :class="['tour-map', { 'fullscreen': isFullscreen }]"
        ></div>
      </div>

      <!-- Additional Info -->
      <div v-if="localTour.elevation_down > 0" class="additional-info">
        <div class="card">
          <div class="card-header">📈 Höhenprofil Information</div>
          <div class="elevation-details">
            <div class="elevation-item">
              <span class="elevation-icon">↗️</span>
              <span class="elevation-label">Anstieg:</span>
              <span class="elevation-value">{{ Math.round(localTour.elevation_up) }} m</span>
            </div>
            <div class="elevation-item">
              <span class="elevation-icon">↘️</span>
              <span class="elevation-label">Abstieg:</span>
              <span class="elevation-value">{{ Math.round(localTour.elevation_down) }} m</span>
            </div>
            <div class="elevation-item">
              <span class="elevation-icon">📊</span>
              <span class="elevation-label">Netto-Höhenunterschied:</span>
              <span class="elevation-value">{{ Math.round(localTour.elevation_up - localTour.elevation_down) }} m</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// Component setup
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTourStore } from '../stores/tours'
import { useToastStore } from '../stores/toast'
import L from 'leaflet'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'

const route = useRoute()
const router = useRouter()
const tourStore = useTourStore()
const toastStore = useToastStore()

const loading = ref(false)
const error = ref(null)
const localTour = ref(null)
const mapContainer = ref(null)
const map = ref(null)
const trackLayer = ref(null)
const isFullscreen = ref(false)

const loadTour = async () => {
  const id = parseInt(route.params.id)
  if (!id) {
    error.value = 'Ungültige Tour-ID'
    return
  }

  loading.value = true
  error.value = null

  try {
    const tourData = await tourStore.fetchTourDetail(id)
    console.log('Tour data received:', tourData)
    localTour.value = tourData
  } catch (err) {
    console.error('Error loading tour:', err)
    error.value = 'Fehler beim Laden der Tour-Details'
  } finally {
    loading.value = false
  }
}

const initMap = async () => {
  // Wait for the container to be available in the DOM
  await nextTick()
  
  if (!mapContainer.value || !localTour.value) {
    console.log('Map container or tour data not ready', {
      hasContainer: !!mapContainer.value,
      hasTour: !!localTour.value
    })
    return
  }

  try {
    // Clean up existing map if it exists
    if (map.value) {
      map.value.remove()
      map.value = null
    }

    console.log('Initializing map with tour:', {
      id: localTour.value.id,
      name: localTour.value.name,
      hasTrack: !!localTour.value.track_geojson
    })

    // Initialize map
    map.value = L.map(mapContainer.value).setView([localTour.value.start_lat, localTour.value.start_lon], 13)

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18
    }).addTo(map.value)

    // Add start marker
    L.marker([localTour.value.start_lat, localTour.value.start_lon])
      .addTo(map.value)
      .bindPopup('🚀 Start')

    // Add track
    if (localTour.value.track_geojson) {
      const trackData = localTour.value.track_geojson
      console.log('Adding track to map:', trackData)

      trackLayer.value = L.geoJSON(trackData, {
        style: {
          color: '#3498db',
          weight: 4,
          opacity: 0.8
        }
      }).addTo(map.value)

      // Center on track bounds
      const bounds = trackLayer.value.getBounds()
      map.value.fitBounds(bounds, {
        padding: [50, 50]
      })
    }
  } catch (err) {
    console.error('Failed to initialize map:', err)
    toastStore.error('Fehler beim Initialisieren der Karte')
  }
}

// Watch for both map container and tour data
watch(
  [mapContainer, localTour],
  async ([newContainer, newTour]) => {
    if (newContainer && newTour) {
      console.log('Both map container and tour data are ready, initializing map')
      await initMap()
    } else {
      console.log('Map dependencies not ready:', {
        hasContainer: !!newContainer,
        hasTour: !!newTour
      })
    }
  },
  { immediate: true }
)

const centerOnTrack = () => {
  if (map.value && trackLayer.value) {
    const bounds = trackLayer.value.getBounds()
    map.value.fitBounds(bounds, {
      padding: [50, 50]
    })
  } else if (map.value && localTour.value) {
    // Fallback to start point if no track
    map.value.setView([localTour.value.start_lat, localTour.value.start_lon], 13)
  }
}

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
  
  setTimeout(() => {
    if (map.value) {
      map.value.invalidateSize()
      if (trackLayer.value) {
        map.value.fitBounds(trackLayer.value.getBounds())
      }
    }
  }, 300)
}

const goBack = () => {
  router.go(-1)
}

// Utility functions
const formatDuration = (seconds) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
}

const formatDate = (dateString) => {
  try {
    return format(new Date(dateString), 'dd.MM.yyyy HH:mm', { locale: de })
  } catch {
    return dateString
  }
}

const formatCoordinate = (lat, lon) => {
  return `${lat.toFixed(4)}, ${lon.toFixed(4)}`
}

// Lifecycle
onMounted(async () => {
  try {
    await loadTour()
  } catch (err) {
    console.error('Error in mounted hook:', err)
    error.value = 'Fehler beim Laden der Tour'
  }
})

onUnmounted(() => {
  // Clean up map when component is unmounted
  if (map.value) {
    map.value.remove()
    map.value = null
  }
  if (trackLayer.value) {
    trackLayer.value = null
  }
})
</script>

<style scoped>
.tour-detail {
  max-width: 1000px;
  margin: 0 auto;
}

.loading-state,
.error-state {
  text-align: center;
  padding: 4rem 2rem;
}

.tour-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  gap: 2rem;
}

.tour-title h1 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 2rem;
}

.tour-badges {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.type-badge {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.9rem;
}

.type-bike { background: #e74c3c; color: white; }
.type-hike { background: #27ae60; color: white; }
.type-inline { background: #9b59b6; color: white; }
.type-undefined { background: #95a5a6; color: white; }

.ebike-badge {
  background: #f39c12;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.9rem;
}

.tour-actions {
  display: flex;
  gap: 1rem;
  flex-shrink: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  font-size: 2rem;
  opacity: 0.8;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #3498db;
  margin-bottom: 0.25rem;
}

.stat-label {
  color: #7f8c8d;
  font-size: 0.9rem;
  font-weight: 500;
}

.tour-map-section {
  margin-bottom: 2rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.map-controls {
  display: flex;
  gap: 1rem;
}

.tour-map {
  height: 400px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transition: all 0.3s ease;
}

.tour-map.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 2000;
  border-radius: 0;
}

.additional-info {
  margin-bottom: 2rem;
}

.elevation-details {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.elevation-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.elevation-icon {
  font-size: 1.2rem;
  width: 2rem;
  text-align: center;
}

.elevation-label {
  flex: 1;
  font-weight: 500;
  color: #7f8c8d;
}

.elevation-value {
  font-weight: 700;
  color: #2c3e50;
}

@media (max-width: 768px) {
  .tour-header {
    flex-direction: column;
  }
  
  .tour-actions {
    align-self: stretch;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .section-header {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .map-controls {
    align-self: stretch;
  }
  
  .tour-map {
    height: 300px;
  }
}

/* Leaflet overrides */
:deep(.leaflet-popup-content-wrapper) {
  border-radius: 8px;
}
</style>
