import axios from 'axios'

// Base API configuration
const API_BASE_URL = window.APP_CONFIG?.apiBaseUrl || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

console.log('🔧 API_BASE_URL:', API_BASE_URL)

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token to requests if available
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // Handle common errors
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.detail || 'Ein Fehler ist aufgetreten'
      error.message = message
    } else if (error.request) {
      // Request was made but no response received
      error.message = 'Keine Verbindung zum Server möglich'
    } else {
      // Something else happened
      error.message = 'Ein unbekannter Fehler ist aufgetreten'
    }
    return Promise.reject(error)
  }
)

// Tour API endpoints
export const tourApi = {
  // Get all tours with filters
  getTours: (params = {}) => {
    return api.get('/api/tours', { params })
  },

  // Get specific tour details
  getTourDetail: (tourId) => {
    return api.get(`/api/tours/${tourId}`)
  },

  // Get tours near a location
  getNearbyTours: (locationData) => {
    return api.post('/api/tours/nearby', locationData)
  },

  // Get tours summary/statistics
  getSummary: () => {
    return api.get('/api/tours/summary')
  },

  // Get available tour types
  getTourTypes: () => {
    return api.get('/api/tours/types')
  },

  // Get tours as GeoJSON for map display
  getToursGeoJSON: (params = {}) => {
    console.log('🔧 API getToursGeoJSON - params received:', params)
    console.log('🔧 API getToursGeoJSON - calling:', '/api/tours/geojson', { params })
    return api.get('/api/tours/geojson', { params })
  }
}

// Location services
export const locationApi = {
  // Get current position
  getCurrentPosition: () => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation wird von diesem Browser nicht unterstützt'))
        return
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy
          })
        },
        (error) => {
          let message = 'Standort konnte nicht ermittelt werden'
          switch (error.code) {
            case error.PERMISSION_DENIED:
              message = 'Standortzugriff wurde verweigert'
              break
            case error.POSITION_UNAVAILABLE:
              message = 'Standort ist nicht verfügbar'
              break
            case error.TIMEOUT:
              message = 'Zeitüberschreitung beim Ermitteln des Standorts'
              break
          }
          reject(new Error(message))
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 300000 // 5 minutes
        }
      )
    })
  },

  // Watch position changes
  watchPosition: (successCallback, errorCallback) => {
    if (!navigator.geolocation) {
      errorCallback(new Error('Geolocation wird von diesem Browser nicht unterstützt'))
      return null
    }

    return navigator.geolocation.watchPosition(
      successCallback,
      errorCallback,
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000 // 1 minute
      }
    )
  },

  // Stop watching position
  clearWatch: (watchId) => {
    if (watchId && navigator.geolocation) {
      navigator.geolocation.clearWatch(watchId)
    }
  }
}

export default api
