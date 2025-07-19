<template>
  <div :class="['tour-card', `tour-card-${viewMode}`, { 'tour-card-ebike': tour.ebike }]">
    <div v-if="viewMode === 'cards'" class="card-mode">
      <!-- Card Header -->
      <div class="tour-header">
        <div class="tour-title">
          <h3>{{ tour.name }}</h3>
          <div class="tour-badges">
            <span :class="['type-badge', `type-${tour.type.toLowerCase()}`]">
              {{ tour.type }}
            </span>
            <span v-if="tour.ebike" class="ebike-badge">⚡</span>
          </div>
        </div>
      </div>

      <!-- Card Stats -->
      <div class="tour-stats">
        <div class="stat-item">
          <span class="stat-icon">📏</span>
          <span class="stat-value">{{ tour.distance_km.toFixed(1) }} km</span>
        </div>
        <div class="stat-item">
          <span class="stat-icon">⏱️</span>
          <span class="stat-value">{{ formatDuration(tour.duration_s) }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-icon">🏃</span>
          <span class="stat-value">{{ tour.speed_kmh.toFixed(1) }} km/h</span>
        </div>
        <div class="stat-item">
          <span class="stat-icon">⛰️</span>
          <span class="stat-value">{{ Math.round(tour.elevation_up) }} m</span>
        </div>
      </div>

      <!-- Card Footer -->
      <div class="tour-footer">
        <div class="tour-date">
          📅 {{ formatDate(tour.date) }}
        </div>
        <div class="tour-actions">
          <button @click.stop="navigateToMap" class="btn btn-map btn-sm">
            🗺️ Karte
          </button>
          <router-link :to="`/tour/${tour.id}`" class="btn btn-primary btn-sm">
            Details →
          </router-link>
        </div>
      </div>
    </div>

    <div v-else class="list-mode">
      <!-- List Header -->
      <div class="list-header">
        <div class="list-title">
          <h4>{{ tour.name }}</h4>
          <div class="list-badges">
            <span :class="['type-badge-sm', `type-${tour.type.toLowerCase()}`]">
              {{ tour.type }}
            </span>
            <span v-if="tour.ebike" class="ebike-badge-sm">⚡</span>
          </div>
        </div>
        <div class="list-actions">
          <button @click.stop="navigateToMap" class="btn btn-map btn-sm">
            🗺️ Karte
          </button>
          <router-link :to="`/tour/${tour.id}`" class="btn btn-primary btn-sm">
            Details
          </router-link>
        </div>
      </div>

      <!-- List Stats -->
      <div class="list-stats">
        <div class="list-stat">
          <span class="list-stat-label">Distanz:</span>
          <span class="list-stat-value">{{ tour.distance_km.toFixed(1) }} km</span>
        </div>
        <div class="list-stat">
          <span class="list-stat-label">Dauer:</span>
          <span class="list-stat-value">{{ formatDuration(tour.duration_s) }}</span>
        </div>
        <div class="list-stat">
          <span class="list-stat-label">Geschwindigkeit:</span>
          <span class="list-stat-value">{{ tour.speed_kmh.toFixed(1) }} km/h</span>
        </div>
        <div class="list-stat">
          <span class="list-stat-label">Höhenmeter:</span>
          <span class="list-stat-value">{{ Math.round(tour.elevation_up) }} m</span>
        </div>
        <div class="list-stat">
          <span class="list-stat-label">Datum:</span>
          <span class="list-stat-value">{{ formatDate(tour.date) }}</span>
        </div>
      </div>
    </div>

    <!-- Komoot Link -->
    <a 
      v-if="tour?.komoothref" 
      :href="tour.komoothref" 
      target="_blank"
      class="komoot-link"
      title="In Komoot öffnen"
    >
      🔗
    </a>
  </div>
</template>

<script setup>
import { format } from 'date-fns'
import { de } from 'date-fns/locale'

defineProps({
  tour: {
    type: Object,
    required: true
  },
  viewMode: {
    type: String,
    default: 'cards',
    validator: value => ['cards', 'list'].includes(value)
  }
})

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
    return format(new Date(dateString), 'dd.MM.yyyy', { locale: de })
  } catch {
    return dateString
  }
}

// Navigate directly to tour detail page map section
const navigateToMap = () => {
  router.push(`/tour/${tour.id}#map`)
}
</script>

<style scoped>
.tour-card {
  position: relative;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: all 0.3s ease;
  overflow: hidden;
}

.tour-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}

.tour-card-ebike {
  border-left: 4px solid #f39c12;
}

.komoot-link {
  position: absolute;
  top: 10px;
  right: 10px;
  font-size: 1.2rem;
  text-decoration: none;
  opacity: 0.7;
  transition: opacity 0.3s;
}

.komoot-link:hover {
  opacity: 1;
}

/* Card Mode Styles */
.card-mode {
  padding: 1.5rem;
}

.tour-header {
  margin-bottom: 1rem;
}

.tour-title h3 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
  font-size: 1.1rem;
  font-weight: 600;
  line-height: 1.3;
}

.tour-badges {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.type-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.type-bike { background: #e74c3c; color: white; }
.type-hike { background: #27ae60; color: white; }
.type-inline { background: #9b59b6; color: white; }
.type-undefined { background: #95a5a6; color: white; }

.ebike-badge {
  background: #f39c12;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.tour-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.stat-icon {
  opacity: 0.7;
}

.stat-value {
  font-weight: 600;
  color: #2c3e50;
}

.tour-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #ecf0f1;
}

.tour-date {
  color: #7f8c8d;
  font-size: 0.9rem;
}

/* List Mode Styles */
.list-mode {
  padding: 1rem 1.5rem;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
  gap: 1rem;
}

.list-title {
  flex: 1;
}

.list-title h4 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
  font-size: 1rem;
  font-weight: 600;
}

.list-badges {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
}

.type-badge-sm {
  padding: 0.15rem 0.5rem;
  border-radius: 8px;
  font-size: 0.7rem;
  font-weight: 600;
}

.type-badge-sm.type-bike { background: #e74c3c; color: white; }
.type-badge-sm.type-hike { background: #27ae60; color: white; }
.type-badge-sm.type-inline { background: #9b59b6; color: white; }
.type-badge-sm.type-undefined { background: #95a5a6; color: white; }

.ebike-badge-sm {
  background: #f39c12;
  color: white;
  padding: 0.15rem 0.4rem;
  border-radius: 8px;
  font-size: 0.7rem;
  font-weight: 600;
}

.list-actions {
  flex-shrink: 0;
}

.list-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.5rem;
  font-size: 0.85rem;
}

.list-stat {
  display: flex;
  justify-content: space-between;
  padding: 0.25rem 0;
}

.list-stat-label {
  color: #7f8c8d;
  font-weight: 500;
}

.list-stat-value {
  font-weight: 600;
  color: #2c3e50;
}

/* Button Styles */
.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.85rem;
}

/* Responsive Design */
@media (max-width: 768px) {
  .tour-stats {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
  
  .tour-footer {
    flex-direction: column;
    gap: 0.75rem;
    align-items: flex-start;
  }
  
  .list-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .list-actions {
    align-self: stretch;
  }
  
  .list-stats {
    grid-template-columns: 1fr;
    gap: 0.25rem;
  }
}

/* List mode specific responsive */
.tour-card-list {
  margin-bottom: 0.5rem;
}

.tour-card-list:hover {
  transform: none;
}

.tour-actions {
  display: flex;
  gap: 8px;
}

.btn-map {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-map:hover {
  background-color: #45a049;
}
</style>
