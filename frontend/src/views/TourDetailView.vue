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
          <span class="distance-badge">📏 {{ formatDistance(tour.distance_km) }}</span>
        </div>
      </header>

      <!-- Tour Map -->
      <section id="map" class="tour-map-container" ref="mapContainer">
        <h2>Streckendetails</h2>
        <p class="tour-description">Tour vom {{ formatDate(tour?.date) }} • {{ formatDistance(tour?.distance_km) }}</p>
        <!-- Add a debug element to verify rendering -->
        <div id="map-debug" style="padding: 5px; background-color: #f8f8f8; border: 1px solid #ddd; margin-bottom: 10px;">
          Map container rendered at {{ new Date().toISOString() }}
        </div>
        <!-- Map container with all elements together in a single wrapper -->
        <div 
          id="tour-map-wrapper" 
          class="tour-map-wrapper"
          style="position: relative; height: 500px; width: 100%; margin-bottom: 1rem;"
        >
          <!-- The actual map container -->
          <div 
            id="tour-map" 
            ref="tourMapElement" 
            :key="`tour-map-${tour?.id || 'default'}`"
            class="tour-map" 
            style="height: 100%; width: 100%; border: 2px solid #ccc; border-radius: 8px; overflow: hidden;"
          ></div>
          
          <!-- Show message as overlay if no data -->
          <div v-if="tour && !tour.track_geojson" class="no-map-data">
            Keine Geodaten für diese Tour verfügbar
          </div>
          
          <!-- Map legend as a direct child of the wrapper -->
          <div class="map-legend">
            <div class="legend-item">
              <div class="legend-color" style="background-color: #3388ff; height: 5px;"></div>
              <span>Tour: {{ tour?.name }}</span>
            </div>
            <div class="legend-item">
              <div class="legend-color" style="background-color: #00CC00; height: 5px; border-radius: 50%;"></div>
              <span>Start</span>
            </div>
            <div class="legend-item">
              <div class="legend-color" style="background-color: #FF0000; height: 5px; border-radius: 50%;"></div>
              <span>Ende</span>
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
      // Give DOM time to update - need longer timeout for production environment
      await nextTick()
      
      // Determine if we're in production mode
      const isProd = process.env.NODE_ENV === 'production';
      const timeout = isProd ? 1000 : 500; // Longer timeout in production
      
      console.log(`Waiting ${timeout}ms for DOM update in ${isProd ? 'production' : 'development'} mode`);
      
      setTimeout(async () => {
        console.log('Tour data changed, reinitializing map');
        await initMap();
      }, timeout);
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

// Helper function to ensure map elements are available in DOM
const ensureMapElements = () => {
  console.log('Checking for map elements in the DOM...');
  const mapWrapper = document.getElementById('tour-map-wrapper');
  const mapContainer = document.getElementById('tour-map');
  
  if (!mapWrapper || !mapContainer) {
    console.log('Map elements not found, will retry...');
    return false;
  }
  
  console.log('Map elements found in the DOM');
  return true;
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
  
  // More robust approach to getting or creating the map container
  let mapDiv = null;
  const mapWrapperID = 'tour-map-wrapper';
  const mapContainerID = 'tour-map';
  
  try {
    // Try multiple approaches to find the map container
    
    // First approach: use Vue ref (most reliable in Vue components)
    if (tourMapElement?.value) {
      console.log('✅ Found map container via tourMapElement ref')
      mapDiv = tourMapElement.value;
    } 
    // Second approach: get by ID
    else if (document.getElementById(mapContainerID)) {
      console.log('✅ Found map container via getElementById')
      mapDiv = document.getElementById(mapContainerID);
    } 
    // Third approach: query selector with multiple options for better Docker Swarm compatibility
    else {
      console.log('Trying query selectors for map container...')
      // Try multiple selectors to maximize chance of finding the container in different environments
      const selectors = [
        `#${mapContainerID}`, 
        `.tour-map`, 
        `div[id="${mapContainerID}"]`,
        `[id="${mapContainerID}"]`
      ];
      
      for (const selector of selectors) {
        mapDiv = document.querySelector(selector);
        if (mapDiv) {
          console.log(`✅ Found map container via selector: ${selector}`);
          break;
        }
      }
    }
    
    // If we still don't have a container, create one
    if (!mapDiv) {
      console.log('🔨 Creating a new map container...');
      
      // Find the parent where we should insert the map
      let parentElement = null;
      
      // Try different possible parent elements
      const possibleParents = [
        document.getElementById(mapWrapperID),
        document.querySelector('.tour-map-wrapper'),
        document.querySelector('.tour-map-container'), 
        document.getElementById('map'),
        document.querySelector('section')
      ];
      
      for (const parent of possibleParents) {
        if (parent) {
          parentElement = parent;
          console.log(`✅ Found parent element: ${parent.tagName}#${parent.id || 'no-id'}`);
          break;
        }
      }
      
      if (!parentElement) {
        // Last resort: use the main content div
        parentElement = document.querySelector('.tour-content') || document.body;
        console.log('⚠️ Using fallback parent element');
      }
      
      // Create new map container with Docker Swarm-friendly approach
      mapDiv = document.createElement('div');
      mapDiv.id = mapContainerID;
      mapDiv.className = 'tour-map';
      mapDiv.style.cssText = 'height: 500px; width: 100%; border: 2px solid #ccc; position: relative; z-index: 1;';
      mapDiv.setAttribute('data-tour-id', tour.value?.id || 'default');
      
      // Empty the parent first to avoid multiple map containers
      if (parentElement.querySelector('.tour-map')) {
        console.log('⚠️ Found existing map elements, cleaning up first');
        const existingElements = parentElement.querySelectorAll('.tour-map');
        existingElements.forEach(el => el.remove());
      }
      
      // Add to the DOM
      parentElement.appendChild(mapDiv);
      console.log('✅ Created and appended new map container');
      
      // Force a small delay to ensure DOM is updated
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    // Additional verification and debugging
    console.log('🔍 Map container details:', {
      id: mapDiv.id,
      className: mapDiv.className,
      isConnected: mapDiv.isConnected,
      parentElement: mapDiv.parentElement ? mapDiv.parentElement.tagName : 'none',
      clientWidth: mapDiv.clientWidth,
      clientHeight: mapDiv.clientHeight
    });
    
    if (!mapDiv.clientWidth || !mapDiv.clientHeight) {
      console.warn('⚠️ Map container has zero width/height - forcing dimensions');
      mapDiv.style.width = '100%';
      mapDiv.style.height = '500px';
    }
  } catch (error) {
    console.error('❌ Error finding/creating map container:', error);
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
    
    // Create a fresh map instance with enhanced options
    try {
      map.value = L.map(mapDiv, {
        zoomControl: false,  // We'll add custom zoom control
        attributionControl: true,
        maxZoom: 18,
        scrollWheelZoom: true,
        doubleClickZoom: true,
        fadeAnimation: false, // Disable animations in Docker Swarm for better compatibility
        markerZoomAnimation: false,
        preferCanvas: true // Better performance in Docker Swarm
      });
    } catch (mapCreationError) {
      console.error('Error creating Leaflet map:', mapCreationError);
      
      // Try one more time with a clean div
      console.log('Attempting map creation with a fresh div element...');
      
      const freshDiv = document.createElement('div');
      freshDiv.id = 'tour-map-fresh';
      freshDiv.className = 'tour-map';
      freshDiv.style.cssText = 'height: 500px; width: 100%; border: 2px solid #ccc; position: relative; z-index: 1;';
      
      // Replace the old div
      mapDiv.parentElement.replaceChild(freshDiv, mapDiv);
      mapDiv = freshDiv;
      
      // Try again with the fresh div
      map.value = L.map(mapDiv, {
        zoomControl: false,
        attributionControl: true,
        maxZoom: 18,
        preferCanvas: true
      });
    }
    
    // Add custom positioned zoom control
    L.control.zoom({
      position: 'topright'
    }).addTo(map.value);
    
    // Add scale control
    L.control.scale({
      imperial: false,
      position: 'bottomleft'
    }).addTo(map.value);
    
    // Add primary tile layer (OpenStreetMap)
    const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map.value)
    
    // Add optional satellite layer for switching
    const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    });
    
    // Add layer control
    const baseLayers = {
      "Karte": osmLayer,
      "Satellit": satelliteLayer
    };
    L.control.layers(baseLayers, {}, {position: 'topright'}).addTo(map.value);
    
    console.log('Map created successfully')
  } catch (error) {
    console.error('Error creating map:', error)
    toastStore.error('Fehler beim Erstellen der Karte')
    return
  }

  let currentTourLayer = null
  
  // We'll only show the current tour on the map
  console.log('Rendering only the current tour on the map')

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
    
    // Add current tour with more prominent styling
    currentTourLayer = L.geoJSON(geoJsonFeature, {
      style: {
        color: '#3388ff',
        weight: 6,
        opacity: 0.9,
        lineJoin: 'round',
        lineCap: 'round'
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
      // Check the format of coordinates to ensure proper handling
      try {
        const startCoord = trackData.coordinates[0];
        const endCoord = trackData.coordinates[trackData.coordinates.length - 1];
        
        // Safety check for coordinate format - need at least 2 values for lon/lat
        if (startCoord.length >= 2 && endCoord.length >= 2) {
          const startLon = startCoord[0];
          const startLat = startCoord[1];
          const endLon = endCoord[0];
          const endLat = endCoord[1];
          
          console.log('Start coordinates:', startLat, startLon);
          console.log('End coordinates:', endLat, endLon);
          
          // Start marker (green flag)
          L.marker([startLat, startLon], {
            icon: L.divIcon({
              html: '<div style="display:flex;align-items:center;justify-content:center;background:#ffffff;border-radius:50%;width:40px;height:40px;box-shadow:0 2px 5px rgba(0,0,0,0.4);"><span style="font-size:24px;">🚩</span></div>',
              iconSize: [40, 40],
              className: 'start-marker-icon'
            }),
            title: 'Start der Tour: ' + tour.value.name
          }).addTo(map.value);
          
          // Add a popup with tour info at start point
          L.popup()
            .setLatLng([startLat, startLon])
            .setContent(`
              <div class="tour-popup">
                <h4>${tour.value.name}</h4>
                <p>Distanz: ${(tour.value.distance_km).toFixed(1)} km</p>
                <p>Datum: ${new Date(tour.value.date).toLocaleDateString()}</p>
              </div>
            `)
            .addTo(map.value);
          
          // End marker (checkered flag)
          L.marker([endLat, endLon], {
            icon: L.divIcon({
              html: '<div style="display:flex;align-items:center;justify-content:center;background:#ffffff;border-radius:50%;width:40px;height:40px;box-shadow:0 2px 5px rgba(0,0,0,0.4);"><span style="font-size:24px;">🏁</span></div>',
              iconSize: [40, 40],
              className: 'end-marker-icon'
            }),
            title: 'Ende der Tour: ' + tour.value.name
          }).addTo(map.value);
        } else {
          console.error('Invalid coordinate format, not enough values for lat/lon:', startCoord, endCoord);
        }
      } catch (coordError) {
        console.error('Error processing coordinates:', coordError);
      }
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
  console.log('Environment:', process.env.NODE_ENV || 'unknown');
  
  // Add special event listener to help with Docker Swarm environment
  document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded event fired');
  });
  
  await loadTourData()
  
  // Use nextTick to ensure DOM is updated
  await nextTick()
  
  // Docker Swarm environments may need extra time for DOM to be fully processed
  const isProd = process.env.NODE_ENV === 'production';
  if (isProd) {
    console.log('Production environment detected, adding extra initialization delay');
    await new Promise(resolve => setTimeout(resolve, 800));
  }
  
  // Multiple attempts with increasing timeouts to ensure map renders correctly
  // This addresses potential timing issues in different environments
  const attemptMapInitialization = async (attempt = 1, maxAttempts = 5) => { // Increased max attempts for Docker Swarm
    if (attempt > maxAttempts) {
      console.error(`Failed to initialize map after ${maxAttempts} attempts`)
      toastStore.error('Karte konnte nicht initialisiert werden')
      return
    }
    
    // First check if map elements exist in DOM
    const elementsReady = ensureMapElements();
    if (!elementsReady && attempt < maxAttempts) {
      console.log(`Map elements not ready, retrying (attempt ${attempt}/${maxAttempts})`);
      const timeout = Math.pow(2, attempt - 1) * 500;
      setTimeout(() => attemptMapInitialization(attempt + 1, maxAttempts), timeout);
      return;
    }
    
    if (tour.value?.track_geojson) {
      console.log(`Initializing map attempt ${attempt}/${maxAttempts}`)
      try {
        await initMap()
        console.log('Map initialization successful')
        scrollToMapIfNeeded()
      } catch (error) {
        console.warn(`Map initialization attempt ${attempt} failed:`, error)
        // Exponential backoff for retries with longer times for production
        const baseTimeout = isProd ? 1000 : 500;
        const timeout = Math.pow(2, attempt - 1) * baseTimeout
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

.tour-description {
  margin-top: -0.5rem;
  margin-bottom: 1rem;
  color: #666;
  font-size: 0.9rem;
}

.tour-map-wrapper {
  position: relative;
  height: 500px; /* Increased height for better visibility */
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
  margin-bottom: 1rem;
}

.tour-map {
  height: 500px !important; /* Match the map-wrapper height */
  width: 100% !important;
  z-index: 1;
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
  background-color: rgba(245, 245, 245, 0.9);
  font-size: 1.2rem;
  color: #555;
  border: 2px dashed #ccc;
}

.map-legend {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 6px;
  padding: 10px 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  font-size: 0.9rem;
  border: 1px solid #eee;
}

/* Style for leaflet popups */
:deep(.leaflet-popup-content) {
  margin: 10px;
}

:deep(.tour-popup) {
  min-width: 150px;
}

:deep(.tour-popup h4) {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

:deep(.tour-popup p) {
  margin: 4px 0;
  font-size: 12px;
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
  
  .tour-map-wrapper {
    height: 300px;
  }
}
</style>
