<template>
  <div class="map-view">
    <!-- Map Header with Controls -->
    <div class="map-header">
      <h1>🗺️ Tour-Karte</h1>
      <div class="map-controls">
        <button 
          @click="getCurrentLocation" 
          :disabled="loadingLocation"
          class="btn btn-outline"
        >
          <span v-if="loadingLocation">📍 Suche...</span>
          <span v-else>📍 Aktueller Standort</span>
        </button>
        <button 
          @click="showAllTours" 
          class="btn btn-outline"
          :disabled="tourLayers.length === 0"
        >
          🌍 Alle Touren
        </button>
      </div>
    </div>

    <!-- Map Filters -->
    <div class="map-filters">
      <div class="filter-row">
        <div class="filter-group">
          <label>Tour-Typ:</label>
          <select v-model="filters.tourType" @change="applyFilters">
            <option value="">Alle</option>
            <option v-for="type in computedTourTypes" :key="type" :value="type">
              {{ type }}
            </option>
          </select>
        </div>
        
        <div class="filter-group">
          <label>Von:</label>
          <input 
            type="date" 
            v-model="filters.dateFrom" 
            @change="applyFilters"
          />
        </div>
        
        <div class="filter-group">
          <label>Bis:</label>
          <input 
            type="date" 
            v-model="filters.dateTo" 
            @change="applyFilters"
          />
        </div>
        
        <button @click="clearFilters" class="btn btn-outline">
          🗑️ Filter löschen
        </button>
      </div>
    </div>

    <!-- Map Container -->
    <div class="map-container">
      <div ref="mapContainer" class="map"></div>
      
      <!-- Loading Overlay -->
      <div v-if="loadingMap" class="map-loading">
        <div class="loading-spinner"></div>
        <p>Lade Touren...</p>
      </div>
      
      <!-- Selected Tour Info Panel -->
      <div v-if="selectedTour" class="selected-tour-info card">
        <div class="tour-info-header">
          <h3>{{ selectedTour.name }}</h3>
          <button @click="clearSelection" class="btn-close">×</button>
        </div>
        
        <div class="tour-info-details">
          <div class="tour-detail">
            <span class="label">Typ:</span>
            <span class="value">
              {{ selectedTour.type }}
              <span v-if="selectedTour.ebike" class="ebike-badge">E-Bike</span>
            </span>
          </div>
          
          <div class="tour-detail">
            <span class="label">Datum:</span>
            <span class="value">{{ formatDate(selectedTour.date) }}</span>
          </div>
          
          <div class="tour-detail">
            <span class="label">Distanz:</span>
            <span class="value">{{ selectedTour.distance_km.toFixed(1) }} km</span>
          </div>
          
          <div class="tour-detail">
            <span class="label">Start:</span>
            <span class="value">
              {{ selectedTour.start_lat.toFixed(4) }}, {{ selectedTour.start_lon.toFixed(4) }}
            </span>
          </div>
        </div>
        
        <div class="tour-info-actions">
          <button @click="zoomToTour(selectedTour)" class="btn btn-primary">
            🔍 Zur Tour zoomen
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { storeToRefs } from 'pinia'
import L from 'leaflet'
import { useTourStore } from '../stores/tours'
import { useToastStore } from '../stores/toast'
import { locationApi } from '../services/api'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'

const STORAGE_KEY = 'tour-manager-filters' // Use same key as Home.vue

const tourStore = useTourStore()
const toastStore = useToastStore()

// Get reactive store state
const { tours, loading, error, tourTypes, filters, filteredTours } = storeToRefs(tourStore)

// Local state
const mapContainer = ref(null)
const map = ref(null)
const loadingMap = ref(false)
const loadingLocation = ref(false)
const selectedTour = ref(null)
const currentLocationMarker = ref(null)
const tourLayers = ref([])

// Load saved filters from localStorage
const loadSavedFilters = () => {
  try {
    const savedFilters = localStorage.getItem(STORAGE_KEY)
    if (savedFilters) {
      const parsedFilters = JSON.parse(savedFilters)
      tourStore.updateFilters(parsedFilters)
      console.log('📥 Loaded saved filters:', parsedFilters)
    }
  } catch (err) {
    console.error('Error loading saved filters:', err)
    localStorage.removeItem(STORAGE_KEY)
  }
}

// Save filters to localStorage
const saveFilters = () => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filters.value))
    console.log('📤 Saved filters:', filters.value)
  } catch (err) {
    console.error('Error saving map filters:', err)
  }
}

// Watch for filter changes
watch(
  () => filters.value,
  (newFilters) => {
    if (newFilters) {
      saveFilters()
      applyFilters() // Reapply filters when they change
    }
  },
  { deep: true }
)

// Watch for filtered tours to change
watch(
  () => filteredTours.value,
  (newTours) => {
    if (map.value && !loadingMap.value) {
      console.log('🗺️ Filtered tours changed, reloading map data...')
      loadMapData()
    }
  }
)

// Computed
const computedTourTypes = computed(() => tourTypes.value)

// Tour type colors
const typeColors = {
  'Bike': '#e74c3c',
  'Hike': '#27ae60',
  'Inline': '#9b59b6',
  'Undefined': '#95a5a6'
}

// Methods
const initMap = async () => {
  console.log('🗺️ initMap - Starting...')
  
  await nextTick()
  console.log('🗺️ initMap - After nextTick')
  
  if (!mapContainer.value) {
    console.error('🗺️ initMap - mapContainer.value is null!')
    return
  }
  
  console.log('🗺️ initMap - mapContainer is available')

  try {
    // Initialize map
    console.log('🗺️ initMap - Creating Leaflet map...')
    map.value = L.map(mapContainer.value).setView([47.3769, 8.5417], 10) // Centered on Switzerland
    console.log('🗺️ initMap - Leaflet map created')

    // Add OpenStreetMap tiles
    console.log('🗺️ initMap - Adding tile layer...')
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18
    }).addTo(map.value)
    console.log('🗺️ initMap - Tile layer added')      // Load saved filters and tour data
    console.log('🗺️ initMap - Loading saved filters...')
    loadSavedFilters()
    
    console.log('🗺️ initMap - About to call loadMapData...')
    await loadMapData()
    console.log('🗺️ initMap - loadMapData completed')
    
  } catch (error) {
    console.error('🗺️ initMap - Error during map initialization:', error)
    throw error
  }
}

const loadMapData = async () => {
  console.log('🗺️ === LOAD MAP DATA START ===')
  
  if (!map.value) {
    console.error('🗺️ Map not ready, skipping data load')
    return
  }
  
  if (loading.value) {
    console.log('🗺️ Store is loading, waiting...')
    return
  }
  
  loadingMap.value = true
  
  try {
    // Use the filtered tours from the store
    const currentTours = filteredTours.value || []
    if (!currentTours.length) {
      console.log('🗺️ No filtered tours available')
      return
    }
    console.log(`🗺️ Using ${currentTours.length} filtered tours from store`)
      // Convert store tours to GeoJSON format
    const features = toursToFeatures(currentTours)
    console.log(`🗺️ Converted ${features.length} tours to GeoJSON format`)

    // Create GeoJSON collection
    const geojsonData = {
      type: "FeatureCollection",
      features
    }
    
    // Clear existing layers before adding new ones
    clearTourLayers()
    
    // Add tours to map with error handling for each layer
    let addedLayers = 0
    const bounds = []
    
    for (const [index, feature] of features.entries()) {
      const tour = feature.properties
      const color = typeColors[tour.type] || typeColors['Undefined']
      
      try {
        const layer = L.geoJSON(feature, {
          style: {
            color: color,
            weight: 3,
            opacity: 0.8
          }
        }).addTo(map.value)
        
        layer.on('click', () => selectTour(tour))
        
        layer.bindTooltip(`
          <strong>${tour.name}</strong><br>
          ${tour.type} • ${tour.distance_km.toFixed(1)} km<br>
          ${formatDate(tour.date)}
        `, { sticky: true })
        
        tourLayers.value.push(layer)
        bounds.push(layer.getBounds())
        addedLayers++
      } catch (err) {
        console.error(`🗺️ Error adding feature ${index} to map:`, err)
      }
    }
    
    console.log(`🗺️ Successfully added ${addedLayers} layers to map`)
    
    // Fit map to all tour bounds if we have any
    if (bounds.length > 0) {
      const allBounds = L.latLngBounds(bounds)
      map.value.fitBounds(allBounds.pad(0.1))
    }
    
    toastStore.success(`${addedLayers} Touren auf der Karte angezeigt`)
    
  } catch (error) {
    console.error('🗺️ Error loading map data:', error)
    toastStore.error(`Fehler beim Laden der Touren: ${error.message}`)
  } finally {
    loadingMap.value = false
  }
}

const clearFilters = () => {
  // Use the store's updateFilters method to reset filters
  tourStore.updateFilters({
    tourType: '',
    dateFrom: '',
    dateTo: '',
    limit: 999999
  })
  localStorage.removeItem(STORAGE_KEY)
  applyFilters()
  toastStore.success('Filter zurückgesetzt')
}

const zoomToTour = (tour) => {
  if (!map.value || !tour) return
  
  // Find the tour layer and zoom to it
  const tourLayer = tourLayers.value.find(layer => {
    const layerTour = layer.feature?.properties
    return layerTour && layerTour.id === tour.id
  })
  
  if (tourLayer && tourLayer.getBounds) {
    map.value.fitBounds(tourLayer.getBounds(), { padding: [20, 20] })
  } else {
    // Fallback: zoom to start coordinates
    map.value.setView([tour.start_lat, tour.start_lon], 14)
  }
}

const applyFilters = () => {
  if (!map.value) {
    console.log('🗺️ Map not ready, skipping filter application')
    return
  }
  
  console.log('🗺️ ===== APPLY FILTERS START =====')
  console.log('🗺️ Current filters:', filters.value)
  
  // Use the store's filtered tours
  const currentTours = filteredTours.value || []
  console.log(`🗺️ Using ${currentTours.length} filtered tours from store`)
  
  // Clear existing tour layers
  console.log('🗺️ Clearing existing tour layers...')
  clearTourLayers()
  
  // Convert filtered tours to GeoJSON using helper
  const features = toursToFeatures(currentTours)
  console.log(`🗺️ Filtered tours: ${filteredTours.length} tours converted to ${features.length} GeoJSON features`)
  
  // Save filters to localStorage
  saveFilters()
  
  // Track bounds for later map fitting
  const bounds = []
  let addedLayers = 0
  
  // Add each tour to the map with proper error handling
  for (const feature of features) {
    const tour = feature.properties
    const color = typeColors[tour.type] || typeColors['Undefined']
    
    try {
      const layer = L.geoJSON(feature, {
        style: {
          color: color,
          weight: 3,
          opacity: 0.8
        }
      }).addTo(map.value)
      
      layer.on('click', () => selectTour(tour))
      
      layer.bindTooltip(`
        <strong>${tour.name}</strong><br>
        ${tour.type} • ${tour.distance_km.toFixed(1)} km<br>
        ${formatDate(tour.date)}
      `, { sticky: true })
      
      tourLayers.value.push(layer)
      bounds.push(layer.getBounds())
      addedLayers++
    } catch (err) {
      console.error(`🗺️ Error adding tour ${tour.id} to map:`, err)
    }
  }
  
  // Fit map to show all visible tours
  if (bounds.length > 0) {
    const allBounds = L.latLngBounds(bounds)
    map.value.fitBounds(allBounds.pad(0.1))
  }
  
  console.log(`🗺️ Successfully added ${addedLayers} layers to map`)
  console.log('🗺️ ===== APPLY FILTERS END =====')
  
  toastStore.success(`${addedLayers} gefilterte Touren angezeigt`)
}

const clearTourLayers = () => {
  tourLayers.value.forEach(layer => {
    map.value.removeLayer(layer)
  })
  tourLayers.value = []
}

const selectTour = (tour) => {
  selectedTour.value = tour
  
  // Zoom to tour if possible
  const tourLayer = tourLayers.value.find(layer => {
    const layerTour = layer.feature?.properties
    return layerTour && layerTour.id === tour.id
  })
  
  if (tourLayer) {
    map.value.fitBounds(tourLayer.getBounds())
  }
}

const clearSelection = () => {
  selectedTour.value = null
}

const getCurrentLocation = async () => {
  loadingLocation.value = true
  
  try {
    const position = await locationApi.getCurrentPosition()
    
    // Remove existing location marker
    if (currentLocationMarker.value) {
      map.value.removeLayer(currentLocationMarker.value)
    }
    
    // Add new location marker
    currentLocationMarker.value = L.marker([position.latitude, position.longitude])
      .addTo(map.value)
      .bindPopup('📍 Ihr aktueller Standort')
      .openPopup()
    
    // Center map on location
    map.value.setView([position.latitude, position.longitude], 13)
    
    toastStore.success('Standort gefunden')
    
  } catch (err) {
    toastStore.error(err.message)
  } finally {
    loadingLocation.value = false
  }
}

const showAllTours = () => {
  if (tourLayers.value.length > 0) {
    const group = new L.featureGroup(tourLayers.value)
    map.value.fitBounds(group.getBounds().pad(0.1))
  }
}

const formatDate = (dateString) => {
  try {
    return format(new Date(dateString), 'dd.MM.yyyy', { locale: de })
  } catch {
    return dateString
  }
}

// Convert an array of tours to GeoJSON features
const toursToFeatures = (tours) => {
  const features = []
  for (const tour of tours) {
    const feature = convertToGeoJSON(tour)
    if (feature) features.push(feature)
  }
  return features
}

// Lifecycle
onMounted(async () => {
  console.log('🗺️ ===== MAP COMPONENT MOUNTED =====')
  
  try {
    // Load saved filters first
    loadSavedFilters()
    
    // Load tour types if needed
    if (!tourTypes.value?.length) {
      console.log('🗺️ Loading tour types...')
      await tourStore.fetchTourTypes()
      console.log('🗺️ Tour types loaded:', tourTypes.value.length)
    }
    
    // Check Leaflet availability
    if (typeof L === 'undefined') {
      throw new Error('Leaflet (L) is not available')
    }
    
    if (!mapContainer.value) {
      throw new Error('Map container ref is null')
    }
    
    // Initialize map
    console.log('🗺️ Initializing map...')
    await initMap()
    console.log('🗺️ Map initialization complete')
    
  } catch (error) {
    console.error('🗺️ Error during map component initialization:', error)
    toastStore.error('Fehler beim Initialisieren der Karte')
  }
})

onUnmounted(() => {
  if (map.value) {
    map.value.remove()
  }
})

const convertToGeoJSON = (tour) => {
  if (!tour.track_geojson) {
    console.warn(`🗺️ Tour ${tour.id} has no track_geojson data`)
    return null
  }
  
  try {
    const trackData = JSON.parse(tour.track_geojson)
    return {
      type: "Feature",
      geometry: trackData,
      properties: {
        id: tour.id,
        name: tour.name,
        type: tour.type,
        date: tour.date,
        distance_km: tour.distance_km,
        start_lat: tour.start_lat,
        start_lon: tour.start_lon,
        ebike: tour.ebike
      }
    }
  } catch (err) {
    console.warn(`🗺️ Failed to parse track_geojson for tour ${tour.id}:`, err)
    return null
  }
}
</script>

<style scoped>
.map-view {
  height: calc(100vh - 140px);
  display: flex;
  flex-direction: column;
}

.map-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.map-header h1 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.8rem;
}

.map-controls {
  display: flex;
  gap: 1rem;
}

.map-filters {
  margin-bottom: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.filter-row {
  display: flex;
  gap: 1rem;
  align-items: end;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.filter-group label {
  font-size: 0.9rem;
  font-weight: 500;
  color: #495057;
}

.filter-group select,
.filter-group input {
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.9rem;
  min-width: 120px;
}

.filter-group select:focus,
.filter-group input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-outline {
  background: white;
  color: #007bff;
  border: 1px solid #007bff;
}

.btn-outline:hover:not(:disabled) {
  background: #007bff;
  color: white;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6c757d;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.btn-close:hover {
  background: #f8f9fa;
  color: #495057;
}

.map-container {
  flex: 1;
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.map {
  width: 100%;
  height: 100%;
  min-height: 400px;
}

.map-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(255,255,255,0.95);
  padding: 2rem;
  border-radius: 12px;
  text-align: center;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.selected-tour-info {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 320px;
  z-index: 1000;
  max-height: 400px;
  overflow-y: auto;
}

.card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  padding: 1.5rem;
}

.tour-info-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.tour-info-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.1rem;
  line-height: 1.3;
  flex: 1;
  margin-right: 1rem;
}

.tour-info-details {
  margin-bottom: 1.5rem;
}

.tour-detail {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
}

.tour-detail:last-child {
  margin-bottom: 0;
}

.tour-detail .label {
  font-weight: 500;
  color: #6c757d;
}

.tour-detail .value {
  font-weight: 600;
  color: #2c3e50;
  text-align: right;
  flex: 1;
  margin-left: 1rem;
}

.ebike-badge {
  background: #f39c12;
  color: white;
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  margin-left: 0.5rem;
  font-weight: 500;
}

.tour-info-actions {
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .map-header {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .map-controls {
    align-self: stretch;
  }
  
  .filter-row {
    flex-direction: column;
    gap: 1rem;
  }
  
  .filter-group {
    width: 100%;
  }
  
  .filter-group select,
  .filter-group input {
    min-width: 100%;
  }
  
  .selected-tour-info {
    position: static;
    width: 100%;
    margin-top: 1rem;
    max-height: none;
  }
  
  .map-view {
    height: auto;
    min-height: calc(100vh - 140px);
  }
}

/* Leaflet overrides */
:deep(.leaflet-popup-content-wrapper) {
  border-radius: 8px;
}

:deep(.leaflet-tooltip) {
  border-radius: 8px;
  background: rgba(0,0,0,0.8);
  color: white;
  border: none;
  font-size: 0.85rem;
}

:deep(.leaflet-control-zoom) {
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

:deep(.leaflet-control-zoom a) {
  border-radius: 0;
  border: none;
  color: #495057;
}

:deep(.leaflet-control-zoom a:first-child) {
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}

:deep(.leaflet-control-zoom a:last-child) {
  border-bottom-left-radius: 8px;
  border-bottom-right-radius: 8px;
}
</style>
