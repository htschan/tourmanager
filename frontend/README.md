# Tour Manager Frontend

Eine moderne Vue.js Progressive Web App (PWA) für die Visualisierung und Verwaltung von GPX-Touren.

## Features

- 🌍 **Interactive Karten** mit OpenStreetMap
- 📱 **Progressive Web App** (PWA) mit Offline-Unterstützung
- 🔍 **Erweiterte Filter** für Touren
- 📊 **Detaillierte Statistiken** und Übersichten
- 📍 **Standort-basierte Suche** 
- 🎨 **Responsive Design** für alle Geräte
- ⚡ **Schnelle Performance** mit Vite

## Technologie-Stack

- **Vue 3** - Composition API
- **Vite** - Build Tool & Dev Server
- **Pinia** - State Management
- **Vue Router** - Navigation
- **Leaflet** - Interaktive Karten
- **Axios** - HTTP Client
- **PWA** - Service Worker & Manifest

## Installation

```bash
# Dependencies installieren
npm install

# Development Server starten
npm run dev

# Production Build
npm run build

# Production Preview
npm run preview
```

## PWA Features

- 📱 Installierbar auf allen Geräten
- 🔄 Auto-Update bei neuen Versionen
- 💾 Offline-Kartencaching
- 📲 Native App-ähnliche Erfahrung

## API Integration

Die App kommuniziert mit dem FastAPI Backend:

- `VITE_API_BASE_URL`: Backend URL (Standard: http://localhost:8000)

## Entwicklung

```bash
# Development mit Hot Reload
npm run dev

# Linting & Formatting
npm run lint
npm run format
```

## Docker

```bash
# Image bauen
docker build -t tour-manager-frontend .

# Container starten
docker run -p 3000:3000 -e VITE_API_BASE_URL=http://localhost:8000 tour-manager-frontend
```

## Karten-Features

- 🗺️ OpenStreetMap Integration
- 📍 GPS-Standortunterstützung
- 🎯 Tour-Routen Visualisierung
- 🔍 Interaktive Tour-Auswahl
- 📱 Touch-optimierte Bedienung

## Browser-Unterstützung

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile Browsers
