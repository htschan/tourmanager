import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { tourApi } from '../services/api'

export const useTourStore = defineStore('tours', () => {
  // State
  const tours = ref([])
  const currentTour = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const summary = ref(null)
  const availableTourTypes = ref([])

  // Filters
  const filters = ref({
    tourType: '',
    dateFrom: '',
    dateTo: '',
    ebikeOnly: false,
    minDistance: null,
    maxDistance: null,
    minElevation: null
  })

  // Getters
  const filteredTours = computed(() => {
    console.log('filteredTours computed - Total tours:', tours.value.length)
    console.log('filteredTours computed - Current filters:', filters.value)
    
    const result = tours.value.filter(tour => {
      if (filters.value.tourType && tour.type !== filters.value.tourType) return false
      if (filters.value.ebikeOnly && !tour.ebike) return false
      if (filters.value.minDistance && tour.distance_km < filters.value.minDistance) return false
      if (filters.value.maxDistance && tour.distance_km > filters.value.maxDistance) return false
      if (filters.value.minElevation && tour.elevation_up < filters.value.minElevation) return false
      
      // Date filtering
      if (filters.value.dateFrom || filters.value.dateTo) {
        const tourDate = new Date(tour.date)
        if (filters.value.dateFrom) {
          const fromDate = new Date(filters.value.dateFrom)
          if (tourDate < fromDate) return false
        }
        if (filters.value.dateTo) {
          const toDate = new Date(filters.value.dateTo)
          // Add 1 day to include the entire end date
          toDate.setDate(toDate.getDate() + 1)
          if (tourDate >= toDate) return false
        }
      }
      
      return true
    })
    
    console.log('filteredTours computed - Filtered result length:', result.length)
    return result
  })

  const tourTypes = computed(() => {
    // Use API-fetched types if available, otherwise fall back to computed from tours
    if (availableTourTypes.value.length > 0) {
      return availableTourTypes.value.sort()
    }
    
    const types = [...new Set(tours.value.map(tour => tour.type))]
    // Always include "Inline" as an option, even if no tours of that type exist
    if (!types.includes('Inline')) {
      types.push('Inline')
    }
    return types.sort()
  })

  // Actions
  const fetchTours = async (params = {}) => {
    loading.value = true
    error.value = null
    
    try {
      // For client-side filtering, we want to load ALL tours
      // So we send a very high limit to get all records
      const apiParams = { 
        limit: 999999,  // Very high limit to get all tours
        offset: 0,
        ...params 
      }
      const response = await tourApi.getTours(apiParams)
      tours.value = response.data
    } catch (err) {
      error.value = err.message || 'Fehler beim Laden der Touren'
      console.error('Error fetching tours:', err)
    } finally {
      loading.value = false
    }
  }

  const fetchTourDetail = async (tourId) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await tourApi.getTourDetail(tourId)
      currentTour.value = response.data
      return response.data
    } catch (err) {
      error.value = err.message || 'Fehler beim Laden der Tour-Details'
      console.error('Error fetching tour detail:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchNearbyTours = async (latitude, longitude, radiusKm = 10) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await tourApi.getNearbyTours({
        latitude,
        longitude,
        radius_km: radiusKm
      })
      return response.data
    } catch (err) {
      error.value = err.message || 'Fehler beim Suchen nahegelegener Touren'
      console.error('Error fetching nearby tours:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchSummary = async () => {
    try {
      const response = await tourApi.getSummary()
      summary.value = response.data
      return response.data
    } catch (err) {
      error.value = err.message || 'Fehler beim Laden der Zusammenfassung'
      console.error('Error fetching summary:', err)
      throw err
    }
  }

  const fetchToursGeoJSON = async (params = {}) => {
    try {
      console.log('🌐 fetchToursGeoJSON - params:', params)
      const response = await tourApi.getToursGeoJSON(params)
      console.log('🌐 fetchToursGeoJSON - response features count:', response.data.features.length)
      return response.data
    } catch (err) {
      error.value = err.message || 'Fehler beim Laden der Kartendaten'
      console.error('Error fetching GeoJSON:', err)
      throw err
    }
  }

  const fetchTourTypes = async () => {
    try {
      const response = await tourApi.getTourTypes()
      availableTourTypes.value = response.data.types
      return response.data.types
    } catch (err) {
      error.value = err.message || 'Fehler beim Laden der Tour-Typen'
      console.error('Error fetching tour types:', err)
      throw err
    }
  }

  const updateFilters = (newFilters) => {
    filters.value = { ...filters.value, ...newFilters }
  }

  const resetFilters = () => {
    filters.value.tourType = ''
    filters.value.dateFrom = ''
    filters.value.dateTo = ''
    filters.value.ebikeOnly = false
    filters.value.minDistance = null
    filters.value.maxDistance = null
    filters.value.minElevation = null
  }

  const clearError = () => {
    error.value = null
  }

  return {
    // State
    tours,
    currentTour,
    loading,
    error,
    summary,
    filters,
    
    // Getters
    filteredTours,
    tourTypes,
    
    // Actions
    fetchTours,
    fetchTourDetail,
    fetchNearbyTours,
    fetchSummary,
    fetchToursGeoJSON,
    fetchTourTypes,
    updateFilters,
    resetFilters,
    clearError
  }
})
