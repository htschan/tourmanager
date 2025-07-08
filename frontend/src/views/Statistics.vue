<template>
  <div class="statistics">
    <div class="stats-header">
      <h1>📊 Statistiken</h1>
      <button @click="refreshStats" class="btn btn-primary" :disabled="loading">
        🔄 Aktualisieren
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Lade Statistiken...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-state">
      <p>❌ {{ error }}</p>
      <button @click="refreshStats" class="btn btn-primary">
        🔄 Erneut versuchen
      </button>
    </div>

    <!-- Statistics Content -->
    <div v-else-if="summary" class="stats-content">
      <!-- Overview Cards -->
      <div class="overview-section">
        <h2>📈 Übersicht</h2>
        <div class="overview-grid">
          <div class="overview-card">
            <div class="card-icon">🗂️</div>
            <div class="card-content">
              <div class="card-number">{{ summary.total_tours }}</div>
              <div class="card-label">Gesamte Touren</div>
            </div>
          </div>

          <div class="overview-card">
            <div class="card-icon">📏</div>
            <div class="card-content">
              <div class="card-number">{{ formatDistance(summary.total_distance) }}</div>
              <div class="card-label">Gesamtdistanz</div>
            </div>
          </div>

          <div class="overview-card">
            <div class="card-icon">⏱️</div>
            <div class="card-content">
              <div class="card-number">{{ formatDuration(summary.total_duration) }}</div>
              <div class="card-label">Gesamtzeit</div>
            </div>
          </div>

          <div class="overview-card">
            <div class="card-icon">⛰️</div>
            <div class="card-content">
              <div class="card-number">{{ formatElevation(summary.total_elevation_up) }}</div>
              <div class="card-label">Gesamte Höhenmeter</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tour Types Distribution -->
      <div class="types-section">
        <h2>🏷️ Tour-Typen Verteilung</h2>
        <div class="types-grid">
          <div 
            v-for="(count, type) in summary.types" 
            :key="type"
            :class="['type-card', `type-${type.toLowerCase()}`]"
          >
            <div class="type-header">
              <span class="type-icon">{{ getTypeIcon(type) }}</span>
              <span class="type-name">{{ type }}</span>
            </div>
            <div class="type-stats">
              <div class="type-count">{{ count }}</div>
              <div class="type-percentage">
                {{ Math.round((count / summary.total_tours) * 100) }}%
              </div>
            </div>
            <div class="type-bar">
              <div 
                class="type-bar-fill"
                :style="{ width: `${(count / Math.max(...Object.values(summary.types))) * 100}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Average Statistics -->
      <div class="averages-section">
        <h2>📊 Durchschnittswerte</h2>
        <div class="averages-grid">
          <div class="average-card">
            <div class="average-icon">📏</div>
            <div class="average-content">
              <div class="average-value">
                {{ formatDistance(summary.total_distance / summary.total_tours) }}
              </div>
              <div class="average-label">Ø Distanz pro Tour</div>
            </div>
          </div>

          <div class="average-card">
            <div class="average-icon">⏱️</div>
            <div class="average-content">
              <div class="average-value">
                {{ formatDuration(summary.total_duration / summary.total_tours) }}
              </div>
              <div class="average-label">Ø Dauer pro Tour</div>
            </div>
          </div>

          <div class="average-card">
            <div class="average-icon">🏃</div>
            <div class="average-content">
              <div class="average-value">
                {{ calculateAverageSpeed().toFixed(1) }} km/h
              </div>
              <div class="average-label">Ø Geschwindigkeit</div>
            </div>
          </div>

          <div class="average-card">
            <div class="average-icon">⛰️</div>
            <div class="average-content">
              <div class="average-value">
                {{ Math.round(summary.total_elevation_up / summary.total_tours) }} m
              </div>
              <div class="average-label">Ø Höhenmeter pro Tour</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Records -->
      <div v-if="records" class="records-section">
        <h2>🏆 Rekorde</h2>
        <div class="records-grid">
          <div class="record-card" v-if="records.longest">
            <div class="record-header">
              <span class="record-icon">📏</span>
              <span class="record-title">Längste Tour</span>
            </div>
            <div class="record-content">
              <div class="record-value">{{ records.longest.distance_km.toFixed(1) }} km</div>
              <div class="record-name">{{ records.longest.name }}</div>
              <div class="record-date">{{ formatDate(records.longest.date) }}</div>
            </div>
          </div>

          <div class="record-card" v-if="records.highest">
            <div class="record-header">
              <span class="record-icon">⛰️</span>
              <span class="record-title">Meiste Höhenmeter</span>
            </div>
            <div class="record-content">
              <div class="record-value">{{ Math.round(records.highest.elevation_up) }} m</div>
              <div class="record-name">{{ records.highest.name }}</div>
              <div class="record-date">{{ formatDate(records.highest.date) }}</div>
            </div>
          </div>

          <div class="record-card" v-if="records.fastest">
            <div class="record-header">
              <span class="record-icon">🏃</span>
              <span class="record-title">Schnellste Tour</span>
            </div>
            <div class="record-content">
              <div class="record-value">{{ records.fastest.speed_kmh.toFixed(1) }} km/h</div>
              <div class="record-name">{{ records.fastest.name }}</div>
              <div class="record-date">{{ formatDate(records.fastest.date) }}</div>
            </div>
          </div>

          <div class="record-card" v-if="records.duration">
            <div class="record-header">
              <span class="record-icon">⏱️</span>
              <span class="record-title">Längste Dauer</span>
            </div>
            <div class="record-content">
              <div class="record-value">{{ formatDuration(records.duration.duration_s) }}</div>
              <div class="record-name">{{ records.duration.name }}</div>
              <div class="record-date">{{ formatDate(records.duration.date) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useTourStore } from '../stores/tours'
import { useToastStore } from '../stores/toast'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'

const tourStore = useTourStore()
const toastStore = useToastStore()

const records = ref(null)

// Computed
const { summary, loading, error } = tourStore

// Methods
const refreshStats = async () => {
  try {
    await tourStore.fetchSummary()
    await loadRecords()
    toastStore.success('Statistiken aktualisiert')
  } catch (err) {
    toastStore.error('Fehler beim Laden der Statistiken')
  }
}

const loadRecords = async () => {
  try {
    await tourStore.fetchTours({ limit: 1000 }) // Load more tours for records
    const tours = tourStore.tours
    
    if (tours.length === 0) return
    
    records.value = {
      longest: tours.reduce((max, tour) => 
        tour.distance_km > max.distance_km ? tour : max
      ),
      highest: tours.reduce((max, tour) => 
        tour.elevation_up > max.elevation_up ? tour : max
      ),
      fastest: tours.reduce((max, tour) => 
        tour.speed_kmh > max.speed_kmh ? tour : max
      ),
      duration: tours.reduce((max, tour) => 
        tour.duration_s > max.duration_s ? tour : max
      )
    }
  } catch (err) {
    console.error('Error loading records:', err)
  }
}

const calculateAverageSpeed = () => {
  if (!summary.value || summary.value.total_duration === 0) return 0
  
  // Convert total duration from seconds to hours
  const totalHours = summary.value.total_duration / 3600
  return summary.value.total_distance / totalHours
}

const getTypeIcon = (type) => {
  const icons = {
    'Bike': '🚴',
    'Hike': '🥾',
    'Inline': '🛼',
    'Undefined': '❓'
  }
  return icons[type] || '📍'
}

// Utility functions
const formatDistance = (distance) => {
  if (distance >= 1000) {
    return `${(distance / 1000).toFixed(1)}k km`
  }
  return `${Math.round(distance)} km`
}

const formatDuration = (seconds) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (hours > 24) {
    const days = Math.floor(hours / 24)
    const remainingHours = hours % 24
    return `${days}d ${remainingHours}h`
  } else if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
}

const formatElevation = (elevation) => {
  if (elevation >= 1000) {
    return `${(elevation / 1000).toFixed(1)}k m`
  }
  return `${Math.round(elevation)} m`
}

const formatDate = (dateString) => {
  try {
    return format(new Date(dateString), 'dd.MM.yyyy', { locale: de })
  } catch {
    return dateString
  }
}

// Lifecycle
onMounted(() => {
  refreshStats()
})
</script>

<style scoped>
.statistics {
  max-width: 1200px;
  margin: 0 auto;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.loading-state,
.error-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #7f8c8d;
}

.stats-content > div {
  margin-bottom: 3rem;
}

.stats-content h2 {
  color: #2c3e50;
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
}

/* Overview Section */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.overview-card {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.card-icon {
  font-size: 3rem;
  opacity: 0.8;
}

.card-number {
  font-size: 2.5rem;
  font-weight: 700;
  color: #3498db;
  margin-bottom: 0.5rem;
}

.card-label {
  color: #7f8c8d;
  font-weight: 500;
}

/* Types Section */
.types-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.type-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  border-left: 4px solid #3498db;
}

.type-card.type-bike { border-left-color: #e74c3c; }
.type-card.type-hike { border-left-color: #27ae60; }
.type-card.type-inline { border-left-color: #9b59b6; }
.type-card.type-undefined { border-left-color: #95a5a6; }

.type-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.type-icon {
  font-size: 1.5rem;
}

.type-name {
  font-weight: 600;
  color: #2c3e50;
}

.type-stats {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.5rem;
}

.type-count {
  font-size: 2rem;
  font-weight: 700;
  color: #3498db;
}

.type-percentage {
  color: #7f8c8d;
  font-weight: 500;
}

.type-bar {
  height: 4px;
  background: #ecf0f1;
  border-radius: 2px;
  overflow: hidden;
}

.type-bar-fill {
  height: 100%;
  background: #3498db;
  transition: width 0.3s ease;
}

.type-card.type-bike .type-bar-fill { background: #e74c3c; }
.type-card.type-hike .type-bar-fill { background: #27ae60; }
.type-card.type-inline .type-bar-fill { background: #9b59b6; }
.type-card.type-undefined .type-bar-fill { background: #95a5a6; }

/* Averages Section */
.averages-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.average-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  text-align: center;
}

.average-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  opacity: 0.8;
}

.average-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: #3498db;
  margin-bottom: 0.5rem;
}

.average-label {
  color: #7f8c8d;
  font-weight: 500;
}

/* Records Section */
.records-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.record-card {
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  border: 2px solid #f39c12;
}

.record-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.record-icon {
  font-size: 1.5rem;
}

.record-title {
  font-weight: 600;
  color: #2c3e50;
}

.record-value {
  font-size: 2rem;
  font-weight: 700;
  color: #f39c12;
  margin-bottom: 0.5rem;
}

.record-name {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.25rem;
  font-size: 0.9rem;
}

.record-date {
  color: #7f8c8d;
  font-size: 0.8rem;
}

@media (max-width: 768px) {
  .stats-header {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .overview-grid,
  .types-grid,
  .averages-grid,
  .records-grid {
    grid-template-columns: 1fr;
  }
  
  .overview-card {
    flex-direction: column;
    text-align: center;
  }
}
</style>
