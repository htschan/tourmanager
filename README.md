# Project Overview: Tour Manager

Eine vollständige Webapplikation zur Verwaltung und Visualisierung von GPX-Touren.

## 🏗️ Architektur

```
tour-manager/
├── backend/           # FastAPI Python Backend
│   ├── main.py       # API Server
│   ├── Dockerfile    # Container Config
│   └── requirements.txt
├── frontend/          # Vue.js PWA Frontend  
│   ├── src/          # Source Code
│   ├── package.json  # Dependencies
│   └── Dockerfile    # Container Config
├── scripts/          # GPX Import Scripts
│   ├── import_gpx.py # Datenbank Import
│   └── touren.db     # SQLite Datenbank
└── docker-compose.yml # Komplettes Setup
```

## 🚀 Quick Start

### Mit Docker (Empfohlen)
```bash
# Alle Services starten
docker-compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

### Manuell
```bash
# Backend starten
cd backend
pip install -r requirements.txt
python main.py

# Frontend starten (in neuem Terminal)
cd frontend
npm install
npm run dev
```

## ✨ Features

### Backend (FastAPI)
- 🗃️ **SQLite Integration** für Tour-Daten
- 🌍 **Geospatiale Suche** (Haversine-Formel)
- 📊 **REST API** mit automatischer Dokumentation
- 🔍 **Erweiterte Filter** (Typ, Datum, Distanz, Höhe)
- 🗺️ **GeoJSON Export** für Kartendarstellung
- 📈 **Statistiken** und Zusammenfassungen

### Frontend (Vue.js PWA)
- 🗺️ **Interaktive Karten** mit OpenStreetMap/Leaflet
- 📱 **Progressive Web App** (installierbar)
- 🎨 **Responsive Design** (Mobile-First)
- 📍 **GPS-Standortunterstützung**
- 🔍 **Live-Filter** und Suche
- 📊 **Detaillierte Tour-Statistiken**
- ⚡ **Vite** für schnelle Entwicklung

### GPX Import System
- 📥 **Batch-Import** aller GPX-Dateien
- 🔗 **Komoot-Integration** (ID & URL Extraktion)
- 🚫 **Duplikat-Erkennung** 
- 📊 **Automatische Typ-Erkennung** (Bike/Hike/Inline)
- ⚡ **E-Bike Erkennung**
- 📏 **Höhenprofil-Analyse**

## 🗺️ Karten-Features

- **Tour-Routen Visualisierung** mit farbkodierten Linien
- **Standort-basierte Suche** in konfigurierbarem Radius
- **Interactive Tooltips** mit Tour-Informationen
- **Vollbild-Modus** für detaillierte Ansicht
- **Touch-optimierte Bedienung** für Mobile

## 📊 API Endpoints

- `GET /api/tours` - Gefilterte Tour-Liste
- `GET /api/tours/{id}` - Tour-Details mit Kartendaten
- `POST /api/tours/nearby` - Standort-basierte Suche
- `GET /api/tours/geojson` - GeoJSON für Karten
- `GET /api/tours/summary` - Statistik-Dashboard
- `GET /docs` - Swagger API Dokumentation

## 🛠️ Entwicklung

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development  
```bash
cd frontend
npm install
npm run dev
```

### GPX Import
```bash
cd scripts
python import_gpx.py
```

## 🐳 Production Deployment

```bash
# Alle Services mit Docker starten
docker-compose up -d

# Services einzeln skalieren
docker-compose up --scale backend=2 --scale frontend=2
```

## 📱 PWA Installation

Die Frontend-App kann als PWA auf jedem Gerät installiert werden:
- **Desktop**: Browser → Installieren Button
- **Mobile**: "Zum Homescreen hinzufügen"
- **Offline-Unterstützung** für Karten und Daten

## 🔧 Konfiguration

### Environment Variables
```bash
# Backend
DATABASE_PATH=/path/to/touren.db

# Frontend  
VITE_API_BASE_URL=http://localhost:8000
```

### Docker Compose Override
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  backend:
    environment:
      - DEBUG=true
  frontend:
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
```

## 📋 Roadmap

- [ ] **Benutzer-Authentifizierung**
- [ ] **Tour-Upload Interface** 
- [ ] **Social Features** (Teilen, Bewertungen)
- [ ] **Erweiterte Statistiken** (Heatmaps, Trends)
- [ ] **Offline-Modus** für Tour-Details
- [ ] **Export-Funktionen** (GPX, PDF Reports)

## 🤝 Contributing

1. Fork das Repository
2. Feature Branch erstellen
3. Änderungen committen
4. Pull Request erstellen

## 📄 Lizenz

MIT License - siehe LICENSE Datei für Details
