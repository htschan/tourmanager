<template>
  <div class="tours-browse">
    <header class="browse-header">
      <h1>Tour Browser</h1>
      <p>Durchsuche und filtere alle verfügbaren Touren</p>
    </header>

    <!-- Search and Filter Bar -->
    <div class="filter-container">
      <div class="search-box">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="Tour suchen..." 
          class="search-input"
          @input="applyFilters"
        >
        <span class="search-icon">🔍</span>
      </div>

      <div class="filter-options">
        <div class="filter-group">
          <label>Tour-Typ:</label>
          <select v-model="filters.tourType" @change="applyFilters" class="filter-select">
            <option value="">Alle Typen</option>
            <option v-for="type in tourTypes" :key="type" :value="type">
              {{ type }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label>Sortieren nach:</label>
          <select v-model="sortBy" @change="applyFilters" class="filter-select">
            <option value="date">Datum</option>
            <option value="distance">Distanz</option>
            <option value="duration">Dauer</option>
            <option value="elevation">Höhenmeter</option>
            <option value="name">Name</option>
          </select>
        </div>

        <div class="filter-group">
          <label>Richtung:</label>
          <select v-model="sortOrder" @change="applyFilters" class="filter-select">
            <option value="desc">Absteigend</option>
            <option value="asc">Aufsteigend</option>
          </select>
        </div>
      </div>

      <div class="advanced-filters-toggle" @click="toggleAdvancedFilters">
        {{ showAdvancedFilters ? 'Weniger Filter ▲' : 'Mehr Filter ▼' }}
      </div>
    </div>

    <!-- Advanced Filters -->
    <div class="advanced-filters" v-if="showAdvancedFilters">
      <div class="advanced-filters-grid">
        <div class="filter-group">
          <label>Von Datum:</label>
          <input 
            type="date" 
            v-model="filters.dateFrom" 
            @change="applyFilters"
            class="filter-input"
          >
        </div>

        <div class="filter-group">
          <label>Bis Datum:</label>
          <input 
            type="date" 
            v-model="filters.dateTo" 
            @change="applyFilters"
            class="filter-input"
          >
        </div>

        <div class="filter-group">
          <label>Min. Distanz (km):</label>
          <input 
            type="number" 
            v-model.number="filters.minDistance" 
            @change="applyFilters"
            class="filter-input"
            min="0"
            step="0.1"
          >
        </div>

        <div class="filter-group">
          <label>Max. Distanz (km):</label>
          <input 
            type="number" 
            v-model.number="filters.maxDistance" 
            @change="applyFilters"
            class="filter-input"
            min="0"
            step="0.1"
          >
        </div>

        <div class="filter-group">
          <label>Min. Höhenmeter:</label>
          <input 
            type="number" 
            v-model.number="filters.minElevation" 
            @change="applyFilters"
            class="filter-input"
            min="0"
          >
        </div>

        <div class="filter-group">
          <div class="checkbox-group">
            <input 
              type="checkbox" 
              id="ebikeOnly" 
              v-model="filters.ebikeOnly" 
              @change="applyFilters"
            >
            <label for="ebikeOnly">Nur E-Bike Touren</label>
          </div>
        </div>
      </div>

      <div class="filter-actions">
        <button @click="resetFilters" class="btn btn-secondary">
          🔄 Filter zurücksetzen
        </button>
      </div>
    </div>

    <!-- View Mode Toggle -->
    <div class="view-mode-toggle">
      <button 
        @click="viewMode = 'cards'"
        :class="['toggle-btn', viewMode === 'cards' ? 'active' : '']"
      >
        🗂️ Karten
      </button>
      <button 
        @click="viewMode = 'list'"
        :class="['toggle-btn', viewMode === 'list' ? 'active' : '']"
      >
        📋 Liste
      </button>
      <button 
        @click="viewMode = 'table'"
        :class="['toggle-btn', viewMode === 'table' ? 'active' : '']"
      >
        📊 Tabelle
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Lade Touren...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <p>❌ {{ error }}</p>
      <button @click="loadTours" class="btn btn-primary">
        🔄 Erneut versuchen
      </button>
    </div>

    <!-- Tours Display -->
    <div v-else>
      <!-- Results Summary -->
      <div class="results-summary">
        {{ filteredTours.length }} Touren gefunden
      </div>

      <!-- Cards View -->
      <div v-if="viewMode === 'cards'" class="tours-cards">
        <TourCard 
          v-for="tour in displayedTours" 
          :key="tour.id" 
          :tour="tour"
          :view-mode="'cards'"
        />
      </div>

      <!-- List View -->
      <div v-else-if="viewMode === 'list'" class="tours-list">
        <TourCard 
          v-for="tour in displayedTours" 
          :key="tour.id" 
          :tour="tour"
          :view-mode="'list'"
        />
      </div>

      <!-- Table View -->
      <div v-else-if="viewMode === 'table'" class="tours-table">
        <table>
          <thead>
            <tr>
              <th @click="changeSort('name')">Name</th>
              <th @click="changeSort('type')">Typ</th>
              <th @click="changeSort('date')">Datum</th>
              <th @click="changeSort('distance')">Distanz</th>
              <th @click="changeSort('duration')">Dauer</th>
              <th @click="changeSort('elevation')">Höhenmeter</th>
              <th>Aktionen</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="tour in displayedTours" :key="tour.id">
              <td>{{ tour.name }}</td>
              <td>
                <span :class="['type-badge-sm', `type-${tour.type.toLowerCase()}`]">
                  {{ tour.type }}
                </span>
                <span v-if="tour.ebike" class="ebike-badge-sm">⚡</span>
              </td>
              <td>{{ formatDate(tour.date) }}</td>
              <td>{{ formatDistance(tour.distance_km) }}</td>
              <td>{{ formatDuration(tour.duration_s) }}</td>
              <td>{{ formatElevation(tour.elevation_up) }}</td>
              <td>
                <router-link :to="`/tour/${tour.id}`" class="action-btn">
                  Details
                </router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="pagination">
        <button 
          @click="prevPage" 
          :disabled="currentPage <= 1" 
          class="pagination-btn"
        >
          ← Vorherige
        </button>
        
        <span class="page-info">
          Seite {{ currentPage }} von {{ totalPages }}
        </span>
        
        <button 
          @click="nextPage" 
          :disabled="currentPage >= totalPages" 
          class="pagination-btn"
        >
          Nächste →
        </button>
      </div>

      <!-- Empty State -->
      <div v-if="filteredTours.length === 0" class="empty-state">
        <p>🔍 Keine Touren gefunden</p>
        <p>Versuche andere Filtereinstellungen oder füge neue Touren hinzu.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useTourStore } from '../stores/tours'
import { useToastStore } from '../stores/toast'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'
import TourCard from '../components/TourCard.vue'

// Store references
const tourStore = useTourStore()
const toastStore = useToastStore()

// Get reactive store state
const { tours, loading, error, filters } = storeToRefs(tourStore)
const tourTypes = computed(() => tourStore.tourTypes)

// View state
const viewMode = ref('cards')
const showAdvancedFilters = ref(false)
const searchQuery = ref('')
const sortBy = ref('date')
const sortOrder = ref('desc')
const currentPage = ref(1)
const itemsPerPage = ref(12)

// Toggle advanced filters
const toggleAdvancedFilters = () => {
  showAdvancedFilters.value = !showAdvancedFilters.value
}

// Filter and sort tours
const filteredTours = computed(() => {
  // First get tours that match the store filters
  let result = tourStore.filteredTours

  // Then apply local search filter if search query exists
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(tour => 
      tour.name.toLowerCase().includes(query) || 
      tour.type.toLowerCase().includes(query)
    )
  }

  // Sort the results
  return sortTours(result)
})

// Sort tours based on current sort settings
const sortTours = (toursToSort) => {
  return [...toursToSort].sort((a, b) => {
    let comparison = 0
    
    switch (sortBy.value) {
      case 'name':
        comparison = a.name.localeCompare(b.name)
        break
      case 'type':
        comparison = a.type.localeCompare(b.type)
        break
      case 'date':
        comparison = new Date(a.date) - new Date(b.date)
        break
      case 'distance':
        comparison = a.distance_km - b.distance_km
        break
      case 'duration':
        comparison = a.duration_s - b.duration_s
        break
      case 'elevation':
        comparison = a.elevation_up - b.elevation_up
        break
      default:
        comparison = new Date(a.date) - new Date(b.date)
    }
    
    return sortOrder.value === 'asc' ? comparison : -comparison
  })
}

// Pagination
const totalPages = computed(() => 
  Math.ceil(filteredTours.value.length / itemsPerPage.value)
)

const displayedTours = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return filteredTours.value.slice(start, end)
})

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    window.scrollTo(0, 0)
  }
}

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    window.scrollTo(0, 0)
  }
}

// Reset to first page when filters change
watch([() => filteredTours.value.length, searchQuery], () => {
  currentPage.value = 1
})

// Change sort method
const changeSort = (field) => {
  if (sortBy.value === field) {
    // Toggle direction if clicking the same field
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    // New field, set to default sort order (desc)
    sortBy.value = field
    sortOrder.value = 'desc'
  }
}

// Format functions
const formatDate = (dateString) => {
  try {
    return format(new Date(dateString), 'dd.MM.yyyy', { locale: de })
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
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
}

const formatElevation = (elevation) => {
  return `${Math.round(elevation)} m`
}

// Load tours and apply filters
const loadTours = async () => {
  try {
    await tourStore.fetchTours()
    await tourStore.fetchTourTypes()
    
    // Apply any saved filters
    applyFilters()
  } catch (err) {
    toastStore.error('Fehler beim Laden der Touren')
  }
}

const applyFilters = () => {
  // Update store filters
  tourStore.updateFilters(filters.value)
  
  // When applying filters, reset to first page
  currentPage.value = 1
}

const resetFilters = () => {
  tourStore.resetFilters()
  searchQuery.value = ''
  sortBy.value = 'date'
  sortOrder.value = 'desc'
  currentPage.value = 1
  
  toastStore.success('Filter zurückgesetzt')
}

// Load data on component mount
onMounted(() => {
  loadTours()
})
</script>

<style scoped>
.tours-browse {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
}

.browse-header {
  text-align: center;
  margin-bottom: 2rem;
}

.browse-header h1 {
  margin-bottom: 0.5rem;
}

.filter-container {
  background-color: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 1.5rem;
}

.search-box {
  position: relative;
  margin-bottom: 1rem;
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 2.5rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1.2rem;
  color: #666;
}

.filter-options {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1rem;
}

.filter-group {
  flex: 1;
  min-width: 200px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-group label {
  font-weight: 500;
  font-size: 0.9rem;
}

.filter-select,
.filter-input {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.9rem;
}

.checkbox-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: auto;
  padding: 0.5rem 0;
}

.advanced-filters-toggle {
  text-align: center;
  color: #3498db;
  font-weight: 500;
  cursor: pointer;
  padding: 0.5rem;
}

.advanced-filters {
  background-color: #f8f8f8;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.advanced-filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.filter-actions {
  display: flex;
  justify-content: flex-end;
}

.view-mode-toggle {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
  gap: 0.5rem;
}

.toggle-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-btn.active {
  background-color: #3498db;
  color: white;
  border-color: #3498db;
}

.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: 3rem 0;
}

.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top: 4px solid #3498db;
  width: 30px;
  height: 30px;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.results-summary {
  text-align: right;
  margin-bottom: 1rem;
  font-weight: 500;
  color: #666;
}

.tours-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.tours-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.tours-table {
  overflow-x: auto;
  margin-bottom: 2rem;
}

table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
}

table th,
table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

table th {
  background-color: #f5f5f5;
  cursor: pointer;
  position: relative;
}

table th:hover {
  background-color: #eee;
}

.type-badge-sm,
.ebike-badge-sm {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  margin-right: 0.25rem;
  white-space: nowrap;
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

.ebike-badge-sm {
  background-color: #f39c12;
  color: white;
}

.action-btn {
  display: inline-block;
  padding: 0.3rem 0.8rem;
  background-color: #3498db;
  color: white;
  border-radius: 4px;
  text-decoration: none;
  font-size: 0.8rem;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
}

.pagination-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.pagination-btn:hover:not(:disabled) {
  background-color: #3498db;
  color: white;
  border-color: #3498db;
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-weight: 500;
}

/* Responsive styles */
@media (max-width: 768px) {
  .filter-group {
    min-width: 100%;
  }
  
  .tours-cards {
    grid-template-columns: 1fr;
  }
  
  .tours-table {
    font-size: 0.9rem;
  }
  
  .filter-options {
    flex-direction: column;
    gap: 0.75rem;
  }
}
</style>
