<template>
  <div class="tour-detail">
    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>L# Map references
const map = ref(null)
const mapContainer = ref(null)
const tourMapElement = ref(null) Tour-Details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <h2>Fehler beim Laden der Tour</h2>
      <p>{{ error }}</p>
      <button @click="loadTourData" class="btn btn-primary">Erneu      // Start m      // Start marker (green circle)
      L.marker([startCoords[1], startCoords[0]], {
        icon: L.divIcon({
          html: '<div style="display:flex;align-items:center;justify-content:center;background:#ffffff;border-radius:50%;width:30px;height:30px;box-shadow:0 1px 3px rgba(0,0,0,0.3);"><span style="font-size:20px;">🟢</span></div>',
          iconSize: [30, 30],
          className: 'start-marker-icon'
        }),
        title: 'Start der Tour'
      }).addTo(map.value);reen circle)
      L.marker([startCoords[1], startCoords[0]], {
        icon: L.divIcon({
          html: '<div style="display:flex;align-items:center;justify-content:center;background:#ffffff;border-radius:50%;width:30px;height:30px;box-shadow:0 1px 3px rgba(0,0,0,0.3);"><span style="font-size:20px;">🟢</span></div>',
          iconSize: [30, 30],
          className: 'start-marker-icon'
        }),
        title: 'Start der Tour'
      }).addTo(map.value);hen</button>
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
      <section id="map" class="tour-map-container" ref="mapContainer">
        <h2>Streckenverlauf</h2>
        <!-- Add a debug element to verify rendering -->
        <div id="map-debug" style="padding: 5px; background-color: #f8f8f8; border: 1px solid #ddd; margin-bottom: 10px;">
          Map container rendered at {{ new Date().toISOString() }}
        </div>
        <div class="map-wrapper">
          <!-- Always render map container with explicit ID and key for proper rerendering -->
          <div 
            id="tour-map" 
            ref="tourMapElement" 
            :key="`tour-map-${tour?.id || 'default'}`"
            class="tour-map" 
            style="height: 400px; width: 100%; border: 2px solid #ccc;"
          ></div>
          <!-- Show message as overlay if no data -->
          <div v-if="tour && !tour.track_geojson" class="no-map-data">
            Keine Geodaten für diese Tour verfügbar
          </div>
          <div class="map-legend">
            <div class="legend-item">
              <div class="legend-color" style="background-color: #3388ff; height: 5px;"></div>
              <span>Aktuelle Tour</span>
            </div>
            <div class="legend-item">
              <div class="legend-color" style="background-color: #888888; height: 2px;"></div>
              <span>Andere Touren</span>
            </div>
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
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'
import { useTourStore } from '../stores/tours'
import { useToastStore } from '../stores/toast'
import { tourApi } from '../services/api'
import TourCard from '../components/TourCard.vue'

// Import Leaflet directly instead of dynamic import
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Map reference
const map = ref(null)
const mapContainer = ref(null)
const tourMapElement = ref(null)

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

// Watch for tour data changes to initialize map
watch(
  () => tour.value,
  async (newTour) => {
    if (newTour?.track_geojson) {
      // Give DOM time to update
      await nextTick()
      setTimeout(async () => {
        console.log('Tour data changed, reinitializing map')
        await initMap()
      }, 500)
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
  console.log('Initializing map...', tour.value?.id)
  
  if (!tour.value) {
    console.warn('No tour data available')
    return
  }
  
  // Force clean up any existing map
  if (map.value) {
    console.log('Cleaning up existing map')
    map.value.remove()
    map.value = null
  }
  
  // Wait for the component to render completely
  await nextTick()
  
  // More robust approach to getting the map container
  let mapDiv = null;
  
  try {
    // Try using the ref if available (using optional chaining to avoid errors)
    if (tourMapElement?.value) {
      console.log('Found map container via tourMapElement ref')
      mapDiv = tourMapElement.value;
    } 
    // Next try by ID
    else if (document.getElementById('tour-map')) {
      console.log('Found map container via getElementById')
      mapDiv = document.getElementById('tour-map');
    } 
    // Try another selector as fallback
    else {
      console.log('Trying alternative selector for map container')
      mapDiv = document.querySelector('.tour-map');
      
      if (!mapDiv) {
        console.error('Map container not found, creating fallback container')
        // Create a fallback container as a last resort
        const mapWrapper = document.querySelector('.map-wrapper')
        if (mapWrapper) {
          mapDiv = document.createElement('div')
          mapDiv.id = 'tour-map'
          mapDiv.className = 'tour-map'
          mapDiv.style.height = '400px'
          mapDiv.style.width = '100%'
          mapWrapper.appendChild(mapDiv)
          console.log('Created fallback map container')
        } else {
          console.error('Map wrapper not found')
          toastStore.error('Karte kann nicht angezeigt werden')
          return
        }
      }
    }
    
    if (!mapDiv) {
      throw new Error('Map container not available after all attempts');
    }
  } catch (error) {
    console.error('Error finding map container:', error);
    toastStore.error('Fehler beim Laden der Karte: Container nicht gefunden');
    return;
  }

  console.log('Creating new map instance')
  try {
    // Add detailed debug info
    console.log('Map div details:', {
      id: mapDiv.id,
      className: mapDiv.className,
      isConnected: mapDiv.isConnected,
      parentElement: mapDiv.parentElement ? mapDiv.parentElement.tagName : 'none'
    })
    
    // Create a fresh map instance - use the element directly instead of the ID
    map.value = L.map(mapDiv, {
      zoomControl: true,
      attributionControl: true
    })
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map.value)
    
    console.log('Map created successfully')
  } catch (error) {
    console.error('Error creating map:', error)
    toastStore.error('Fehler beim Erstellen der Karte')
    return
  }

  let currentTourLayer = null
  let allToursLayer = null

  // First, load all other tours to display as background
  try {
    console.log('Loading all tours GeoJSON data')
    const response = await tourApi.getToursGeoJSON()
    const allToursGeoJSON = response.data
    
    // Add all tours layer with gray styling
    allToursLayer = L.geoJSON(allToursGeoJSON, {
      style: (feature) => {
        // Style differently if it's the current tour
        if (feature.properties.id === tour.value.id) {
          return {
            color: '#3388ff',
            weight: 5,
            opacity: 0.8
          }
        }
        // Style for all other tours
        return {
          color: '#888888',
          weight: 2,
          opacity: 0.5
        }
      },
      onEachFeature: (feature, layer) => {
        // Add hover effect for other tours
        if (feature.properties.id !== tour.value.id) {
          layer.on({
            mouseover: (e) => {
              e.target.setStyle({
                weight: 3,
                opacity: 0.7,
                color: '#aaaaaa'
              })
            },
            mouseout: (e) => {
              allToursLayer.resetStyle(e.target)
            },
            click: (e) => {
              // Navigate to the clicked tour
              if (feature.properties.id !== tour.value.id) {
                router.push(`/tours/${feature.properties.id}`)
              }
            }
          })
        }
      }
    }).addTo(map.value)
    
    console.log('Added all tours layer to map')
  } catch (error) {
    console.error('Error loading all tours GeoJSON:', error)
    // Continue with just the current tour
  }

  // Now add the current tour track to map with prominent styling
  try {
    if (!tour.value.track_geojson) {
      console.warn('No track_geojson data available for current tour')
      return
    }
    
    // Handle track_geojson which might be a string or an object
    let trackData = tour.value.track_geojson
    
    // If trackData is a string, try to parse it
    if (typeof trackData === 'string') {
      try {
        console.log('Parsing track_geojson from string')
        trackData = JSON.parse(trackData)
      } catch (parseErr) {
        console.error('Failed to parse track_geojson string:', parseErr)
        throw new Error('Invalid GeoJSON data format')
      }
    }
    
    // Convert LineString to a proper GeoJSON feature object
    const geoJsonFeature = {
      type: "Feature",
      properties: {
        id: tour.value.id,
        name: tour.value.name
      },
      geometry: trackData
    }
    
    // Add current tour with prominent styling
    currentTourLayer = L.geoJSON(geoJsonFeature, {
      style: {
        color: '#3388ff',
        weight: 5,
        opacity: 0.8
      }
    }).addTo(map.value)

    console.log('Added current tour layer to map')

    // Fit map to current tour bounds
    try {
      const bounds = currentTourLayer.getBounds()
      map.value.fitBounds(bounds)
    } catch (boundsError) {
      console.error('Error fitting map to bounds:', boundsError)
      // Set a default view if bounds can't be determined
      map.value.setView([tour.value.start_lat, tour.value.start_lon], 12)
    }

    // Add start/end markers with better styling
    console.log('Adding start/end markers...');
    if (trackData.coordinates && trackData.coordinates.length >= 2) {
      const startCoords = trackData.coordinates[0];
      const endCoords = trackData.coordinates[trackData.coordinates.length - 1];
      
      // Start marker (green circle)
      L.marker([startCoords[1], startCoords[0]], {
        icon: L.divIcon({
          html: '<div style="display:flex;align-items:center;justify-content:center;background:#ffffff;border-radius:50%;width:30px;height:30px;box-shadow:0 1px 3px rgba(0,0,0,0.3);"><span style="font-size:16px;">�</span></div>',
          iconSize: [30, 30],
          className: 'start-marker-icon'
        })
      }).addTo(map.value);
      
      // End marker (red circle)
      L.marker([endCoords[1], endCoords[0]], {
        icon: L.divIcon({
          html: '<div style="display:flex;align-items:center;justify-content:center;background:#ffffff;border-radius:50%;width:30px;height:30px;box-shadow:0 1px 3px rgba(0,0,0,0.3);"><span style="font-size:20px;">🔴</span></div>',
          iconSize: [30, 30],
          className: 'end-marker-icon'
        }),
        title: 'Ende der Tour'
      }).addTo(map.value);
    }
  } catch (error) {
    console.error('Error rendering current tour map:', error)
    toastStore.error('Fehler beim Laden der Karte')
  }
}

// Scroll to map section if hash is present
const scrollToMapIfNeeded = () => {
  if (window.location.hash === '#map') {
    setTimeout(() => {
      const mapElement = document.getElementById('map')
      if (mapElement) {
        mapElement.scrollIntoView({ behavior: 'smooth' })
      }
    }, 1000) // Longer delay to ensure everything is rendered
  }
}

// Lifecycle hooks
onMounted(async () => {
  console.log('TourDetailView mounted, loading data')
  await loadTourData()
  
  // Use nextTick to ensure DOM is updated
  await nextTick()
  
  // Multiple attempts with increasing timeouts to ensure map renders correctly
  // This addresses potential timing issues in different environments
  const attemptMapInitialization = async (attempt = 1, maxAttempts = 3) => {
    if (attempt > maxAttempts) {
      console.error(`Failed to initialize map after ${maxAttempts} attempts`)
      toastStore.error('Karte konnte nicht initialisiert werden')
      return
    }
    
    if (tour.value?.track_geojson) {
      console.log(`Initializing map attempt ${attempt}/${maxAttempts}`)
      try {
        await initMap()
        console.log('Map initialization successful')
        scrollToMapIfNeeded()
      } catch (error) {
        console.warn(`Map initialization attempt ${attempt} failed:`, error)
        // Exponential backoff for retries (500ms, 1000ms, 2000ms)
        const timeout = Math.pow(2, attempt - 1) * 500
        setTimeout(() => attemptMapInitialization(attempt + 1, maxAttempts), timeout)
      }
    }
  }
  
  // Start the initialization attempts
  attemptMapInitialization()
})

// Watch for changes to the tour data and reinitialize map when it changes
watch(() => tour.value?.id, async (newVal, oldVal) => {
  if (newVal && newVal !== oldVal) {
    console.log('Tour data changed, reinitializing map')
    await nextTick()
    await initMap()
  }
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
  height: 400px !important;
  width: 100% !important;
  z-index: 1;
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
  background-color: rgba(245, 245, 245, 0.8);
  font-size: 1.1rem;
  color: #666;
}

.map-legend {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background-color: rgba(255, 255, 255, 0.8);
  border-radius: 4px;
  padding: 8px 12px;
  box-shadow: 0 1px 5px rgba(0, 0, 0, 0.2);
  z-index: 1000;
}

.legend-item {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.legend-item:last-child {
  margin-bottom: 0;
}

.legend-color {
  width: 30px;
  margin-right: 8px;
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
