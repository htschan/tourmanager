<template>
  <div class="home">
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <h1>🚴 Tour Manager</h1>
        <p>Verwalte und visualisiere deine GPX-Touren</p>
        <div class="hero-actions">
          <router-link to="/map" class="btn btn-primary">
            🗺️ Karte öffnen
          </router-link>
          <button @click="findNearbyTours" class="btn btn-secondary" :disabled="loadingLocation">
            📍 Touren in der Nähe
          </button>
        </div>
      </div>
    </section>

    <!-- Quick Stats -->
    <section v-if="summary" class="stats-section">
      <div class="grid grid-3">
        <div class="stat-card">
          <div class="stat-number">{{ summary.total_tours }}</div>
          <div class="stat-label">Touren</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ formatDistance(summary.total_distance) }}</div>
          <div class="stat-label">Kilometer</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ formatElevation(summary.total_elevation_up) }}</div>
          <div class="stat-label">Höhenmeter</div>
        </div>
      </div>
    </section>

    <!-- Filters -->
    <section class="filters-section">
      <div class="card">
        <div class="card-header">Filter</div>
        <div class="grid grid-2">
          <div class="form-group">
            <label class="form-label">Tour-Typ</label>
            <select v-model="filters.tourType" @change="applyFilters" class="form-select">
              <option value="">Alle Typen</option>
              <option v-for="type in tourTypes" :key="type" :value="type">
                {{ type }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label">
              <input type="checkbox" v-model="filters.ebikeOnly" @change="applyFilters">
              Nur E-Bike Touren
            </label>
          </div>

          <div class="form-group">
            <label class="form-label">Von Datum</label>
            <input 
              type="date" 
              v-model="filters.dateFrom" 
              @change="applyFilters"
              class="form-input"
            >
          </div>

          <div class="form-group">
            <label class="form-label">Bis Datum</label>
            <input 
              type="date" 
              v-model="filters.dateTo" 
              @change="applyFilters"
              class="form-input"
            >
          </div>

          <div class="form-group">
            <label class="form-label">Min. Distanz (km)</label>
            <input 
              type="number" 
              v-model.number="filters.minDistance" 
              @change="applyFilters"
              class="form-input"
              min="0"
              step="0.1"
            >
          </div>

          <div class="form-group">
            <label class="form-label">Max. Distanz (km)</label>
            <input 
              type="number" 
              v-model.number="filters.maxDistance" 
              @change="applyFilters"
              class="form-input"
              min="0"
              step="0.1"
            >
          </div>
        </div>

        <div class="filter-actions">
          <button @click="resetFilters" class="btn btn-secondary">
            🔄 Filter zurücksetzen
          </button>
          <button @click="applyFilters" class="btn btn-primary">
            🔍 Anwenden
          </button>
        </div>
      </div>
    </section>

    <!-- Debug Info -->
     <!--
    <section class="debug-section" style="background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px; font-family: monospace;">
      <h3>🐛 Debug Information</h3>
      <p><strong>Total tours in store:</strong> {{ tours.length }}</p>
      <p><strong>Filtered tours count:</strong> {{ filteredTours.length }}</p>
      <p><strong>Loading state:</strong> {{ loading }}</p>
      <p><strong>Error state:</strong> {{ error || 'None' }}</p>
      <p><strong>Current filters:</strong></p>
      <pre style="background: white; padding: 8px; margin: 5px 0;">{{ JSON.stringify(filters, null, 2) }}</pre>
      <p><strong>First 3 tour names:</strong> {{ tours.slice(0, 3).map(t => t.name).join(', ') }}</p>
      <p><strong>Last 3 tour names:</strong> {{ tours.slice(-3).map(t => t.name).join(', ') }}</p>
      <p><strong>API Tests:</strong></p>
      <button @click="testApiDirectly" class="btn btn-sm" style="margin: 5px;">Test API Directly</button>
      <div v-if="apiTestResult" style="background: white; padding: 8px; margin: 5px 0;">
        <strong>API Test Result:</strong> {{ apiTestResult }}
      </div>
    </section>
-->
    <!-- Tour List -->
    <section class="tours-section">
      <div class="section-header">
        <h2>Touren ({{ filteredTours.length }})</h2>
        <div class="view-toggle">
          <button 
            @click="viewMode = 'cards'"
            :class="['btn', viewMode === 'cards' ? 'btn-primary' : 'btn-secondary']"
          >
            🗂️ Karten
          </button>
          <button 
            @click="viewMode = 'list'"
            :class="['btn', viewMode === 'list' ? 'btn-primary' : 'btn-secondary']"
          >
            📋 Liste
          </button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Lade Touren...</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="error-state">
        <p>❌ {{ error }}</p>
        <button @click="loadTours" class="btn btn-primary">
          🔄 Erneut versuchen
        </button>
      </div>

      <!-- Tours Grid/List -->
      <div v-else-if="filteredTours.length > 0" :class="['tours-container', `tours-${viewMode}`]">
        <TourCard 
          v-for="tour in filteredTours" 
          :key="tour.id" 
          :tour="tour"
          :view-mode="viewMode"
        />
      </div>

      <!-- Empty State -->
      <div v-else class="empty-state">
        <p>🔍 Keine Touren gefunden</p>
        <p>Versuche andere Filtereinstellungen oder füge neue Touren hinzu.</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useTourStore } from '../stores/tours'
import { useToastStore } from '../stores/toast'
import { locationApi, tourApi } from '../services/api'
import TourCard from '../components/TourCard.vue'

const tourStore = useTourStore()
const toastStore = useToastStore()

const viewMode = ref('cards')
const loadingLocation = ref(false)
const apiTestResult = ref('')
const STORAGE_KEY = 'tour-manager-filters'

// Get reactive store state
const { tours, loading, error, summary, filters } = storeToRefs(tourStore)
const filteredTours = computed(() => tourStore.filteredTours)
const tourTypes = computed(() => tourStore.tourTypes)

// Methods
const loadTours = async () => {
  try {
    await tourStore.fetchTours()
    await tourStore.fetchSummary()
    await tourStore.fetchTourTypes()
  } catch (err) {
    toastStore.error('Fehler beim Laden der Touren')
  }
}

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
    // If there's an error loading filters, reset them
    localStorage.removeItem(STORAGE_KEY)
  }
}

const saveFilters = () => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filters.value))
    console.log('📤 Saved filters:', filters.value)
  } catch (err) {
    console.error('Error saving filters:', err)
  }
}

const applyFilters = () => {
  saveFilters() // Save filters when applied
}

const resetFilters = async () => {
  tourStore.resetFilters()
  localStorage.removeItem(STORAGE_KEY) // Clear saved filters
  toastStore.success('Filter zurückgesetzt')
}

const findNearbyTours = async () => {
  loadingLocation.value = true
  
  try {
    const position = await locationApi.getCurrentPosition()
    const nearbyTours = await tourStore.fetchNearbyTours(
      position.latitude, 
      position.longitude, 
      10
    )
    
    if (nearbyTours.length > 0) {
      toastStore.success(`${nearbyTours.length} Touren in der Nähe gefunden`)
      // Filter to show only nearby tours
      const nearbyIds = new Set(nearbyTours.map(t => t.id))
      const currentTours = tours.value || []
      tours.value = currentTours.filter(t => nearbyIds.has(t.id))
    } else {
      toastStore.info('Keine Touren in der Nähe gefunden')
    }
  } catch (err) {
    toastStore.error(err.message)
  } finally {
    loadingLocation.value = false
  }
}

const testApiDirectly = async () => {
  try {
    apiTestResult.value = 'Testing...'
    const response = await tourApi.getTours({ limit: 999999 })
    apiTestResult.value = `API returned ${response.data.length} tours directly`
    console.log('Direct API test:', response.data.length, 'tours')
  } catch (err) {
    apiTestResult.value = `API test failed: ${err.message}`
    console.error('Direct API test failed:', err)
  }
}

// Watch filters for changes and save them
watch(
  () => filters.value,
  (newFilters) => {
    if (newFilters) {
      saveFilters()
    }
  },
  { deep: true } // Watch nested properties
)

// Utility functions
const formatDistance = (distance) => {
  if (distance >= 1000) {
    return `${(distance / 1000).toFixed(1)}k`
  }
  return `${Math.round(distance)}`
}

const formatElevation = (elevation) => {
  return `${Math.round(elevation)}m`
}

// Lifecycle
onMounted(async () => {
  console.log('🔄 Home.vue mounted - starting to load tours')
  loadSavedFilters() // Load saved filters first
  await loadTours()
  console.log('✅ Home.vue tours loaded - total in store:', tours.value?.length || 0)
  console.log('✅ Home.vue filtered tours:', filteredTours.value?.length || 0)
})
</script>

<style scoped>
.hero {
  background: linear-gradient(135deg, #3498db, #2980b9);
  color: white;
  text-align: center;
  padding: 4rem 2rem;
  margin: -2rem -1rem 2rem -1rem;
  border-radius: 0 0 20px 20px;
}

.hero-content h1 {
  font-size: 3rem;
  margin-bottom: 1rem;
  font-weight: 700;
}

.hero-content p {
  font-size: 1.2rem;
  margin-bottom: 2rem;
  opacity: 0.9;
}

.hero-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.stats-section {
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.stat-number {
  font-size: 2.5rem;
  font-weight: 700;
  color: #3498db;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #7f8c8d;
  font-weight: 500;
}

.filters-section {
  margin-bottom: 2rem;
}

.filter-actions {
  margin-top: 1rem;
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.tours-section {
  margin-bottom: 2rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.view-toggle {
  display: flex;
  gap: 0.5rem;
}

.tours-container.tours-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.tours-container.tours-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: 3rem;
  color: #7f8c8d;
}

.loading-state .spinner {
  margin: 0 auto 1rem;
}

@media (max-width: 768px) {
  .hero-content h1 {
    font-size: 2rem;
  }
  
  .hero-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .section-header {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .tours-container.tours-cards {
    grid-template-columns: 1fr;
  }
  
  .filter-actions {
    justify-content: center;
  }
}
</style>
