# Project Overview: Tour Manager

[![Docker Build](https://github.com/USERNAME/REPO/actions/workflows/docker-build.yml/badge.svg)](https://github.com/USERNAME/REPO/actions/workflows/docker-build.yml)

Eine vollständige Webapplikation zur Verwaltung und Visualisierung von GPX-Touren.

Das Projekt wurde kreiert durch Github Copilot mit dem Claude Sonnet 3.7 Model im Agent-Modus.

## Komoot

Der Download von GPX-Touren erfolgt von deinem Konto in komoot.de mit dem Tool https://github.com/timschneeb/KomootGPX.

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
docker compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:3000

# Karten-Funktionalität testen
cd scripts
./test_map.sh
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
- 🔐 **Benutzerauthentifizierung** mit JWT und Admin-Benutzer
- 🚀 **Automatische Initialisierung** der Datenbank und Admin-Account
- 🏥 **Health Check** Endpoint für Container-Orchestrierung
- 🔄 **Automatische Wiederherstellung** bei Datenbankfehlern

### Frontend (Vue.js PWA)
- 🗺️ **Interaktive Karten** mit OpenStreetMap/Leaflet
- 📱 **Progressive Web App** (installierbar)
- 🎨 **Responsive Design** (Mobile-First)
- 📍 **GPS-Standortunterstützung**
- 🔍 **Live-Filter** und Suche
- 📊 **Detaillierte Tour-Statistiken**
- ⚡ **Vite** für schnelle Entwicklung
- 🔐 **Authentifizierung** mit JWT
- 🌓 **Dark/Light Mode** Support
- 🏗️ **Build Info** (Timestamp & Git SHA)
- 🐞 **Debug Panel** für Entwicklung
- 🔄 **Automatische Aktualisierung** der Tour-Daten
- 🗺️ **Multi-Layer Karten** (aktuelle Tour + alle anderen Touren)

### GPX Import System
- 📥 **Batch-Import** aller GPX-Dateien
- 🔗 **Komoot-Integration** (ID & URL Extraktion)
- 🚫 **Duplikat-Erkennung** 
- 📊 **Automatische Typ-Erkennung** (Bike/Hike/Inline)
- ⚡ **E-Bike Erkennung**
- 📏 **Höhenprofil-Analyse**
- 🔄 **Inkrementeller Import** neuer Touren

## 🚢 Deployment

### Docker Compose (Entwicklung)
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./scripts:/app/scripts
      - ./data:/app/data
    environment:
      - JWT_SECRET_KEY=your-dev-key
      - DOCKER_ENV=true
      - DATABASE_PATH=/app/data/tourmanager.db

  frontend:
    build: ./frontend
    ports:
      - "3001:3000"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
```

### Docker Stack (Production)
```yaml
services:
  tourm-backend:
    image: hub.bansom.synology.me/tourmbackend:latest
    restart: on-failure:5
    ports:
      - 8000:8000
    volumes:
      - /volume1/docker/tourmbackend:/app/scripts
      - /volume1/docker/tourmdata:/app/data
    secrets:
      - jwt_secret
    environment:
      - JWT_SECRET_KEY_FILE=/run/secrets/jwt_secret
      - DATABASE_PATH=/app/data/tourmanager.db
      - DOCKER_ENV=true

  tourm-frontend:
    image: hub.bansom.synology.me/tourmui:latest
    restart: unless-stopped
    ports:
      - 3001:3000
    environment:
      - VITE_API_BASE_URL=https://tourmbackend.bansom.synology.me

secrets:
  jwt_secret:
    external: true
    name: tourm_jwt_secret
```

## 🔧 Troubleshooting

### Map Rendering Issues
- **Problem**: Map container not found error in the console
- **Solution**:
  1. Ensure the DOM is fully loaded using Vue's `nextTick()`
  2. Use proper Vue refs for the map container
  3. Increase the wait time before map initialization

### Database Connection Issues
- **Problem**: Application fails to connect to the database
- **Solution**:
  1. Check the `DATABASE_PATH` environment variable
  2. Ensure the database file exists and has proper permissions
  3. Verify the container has access to the database volume

## �🗺️ Karten-Features

- **Tour-Routen Visualisierung** mit farbkodierten Linien
- **Überlagerte GeoJSON-Daten** für alle Touren auf einer Karte
- **Standort-basierte Suche** in konfigurierbarem Radius
- **Interactive Tooltips** mit Tour-Informationen
- **Vollbild-Modus** für detaillierte Ansicht
- **Touch-optimierte Bedienung** für Mobile
- **Clustering** für bessere Performance
- **Debug-Overlay** für Entwicklung
- **Interaktive Legende** zur Unterscheidung von aktueller Tour und anderen Touren
- **Start-/Endpunkt Markierungen** für Tour-Navigation

## 🔐 Authentifizierung & Datenbank

### Admin Benutzer
- Ein Admin-Benutzer wird automatisch bei der ersten Ausführung erstellt
- **Standardzugangsdaten:**
  - Benutzername: `admin`
  - Passwort: `admin`

### Datenbank
- SQLite Datenbank wird automatisch initialisiert
- Unterstützt read/write Operationen in Docker-Umgebung
- GPX-Touren werden automatisch importiert und kategorisiert

## 📊 API Endpoints

### Tour-Management
- `GET /api/tours` - Gefilterte Tour-Liste
- `GET /api/tours/{id}` - Tour-Details mit Kartendaten
- `POST /api/tours/nearby` - Standort-basierte Suche
- `GET /api/tours/geojson` - GeoJSON für Karten
- `GET /api/tours/summary` - Statistik-Dashboard

### Authentifizierung
- `POST /api/auth/login` - Benutzer Login
- `POST /api/auth/refresh` - Token auffrischen
- `GET /api/auth/me` - Aktuelle Benutzerinformationen

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

### Karten-Debugging
```bash
# Test-Skript für Karten-Rendering ausführen
cd scripts
./test_map.sh

# Zugriff auf die Tour-Detail-Ansicht mit Map
http://localhost:3000/tours/<tour_id>

# Überprüfen der GeoJSON-Endpunkte
curl -s http://localhost:8000/api/tours/geojson | head

# Prüfen ob Map-Container korrekt initialisiert wird
# (Browser-Konsole auf Fehler prüfen)
```

Das neue Test-Skript `scripts/test_map.sh` bietet eine automatisierte Prüfung der Karten-Funktionalität:
- Findet eine Test-Tour aus der Datenbank
- Prüft die API-Endpunkte auf korrekte Antworten
- Gibt Links zum manuellen Testen im Browser

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

## 🐞 Fehlerbehandlung & Troubleshooting

### Karten-Rendering Probleme
- **Problem**: "Map container not found" Fehler in der Konsole
- **Lösung**: 
  1. Stellen Sie sicher, dass der DOM vollständig geladen ist (`nextTick()`)
  2. Verwenden Sie Vue refs für den Kartenbehälter
  3. Erhöhen Sie die Wartezeit vor der Karten-Initialisierung

### GeoJSON Daten werden nicht angezeigt
- **Problem**: Karte ist sichtbar, aber keine Tour-Daten werden gerendert
- **Lösung**:
  1. Überprüfen Sie die GeoJSON-Endpunkte mit `curl http://localhost:8000/api/tours/geojson`
  2. Stellen Sie sicher, dass die Tour track_geojson-Daten enthält
  3. Prüfen Sie die Konsole auf Leaflet-bezogene Fehler

### Frontend-Container Neustart
- Bei Änderungen am Frontend-Code den Container neu starten:
  ```bash
  docker compose up -d --build frontend
  ```

## �🔧 Konfiguration

### Environment Variables
```bash
# Backend
JWT_SECRET_KEY=your-secret-key
DATABASE_PATH=/path/to/touren.db
PORT=8000

# Frontend  
VITE_API_BASE_URL=http://localhost:8000
VITE_BUILD_TIMESTAMP=${BUILD_TIMESTAMP}
VITE_GIT_SHA=${GIT_SHA}
```

### Docker Compose Override
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  tourm-backend:
    environment:
      - JWT_SECRET_KEY=your-secret-key
      - DATABASE_PATH=/app/scripts/touren.db
      - PORT=8000
  tourm-frontend:
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
      - VITE_BUILD_TIMESTAMP=${BUILD_TIMESTAMP}
      - VITE_GIT_SHA=${GIT_SHA}
```

## 📋 Roadmap

- [x] **Benutzer-Authentifizierung**
- [ ] **Tour-Upload Interface** 
- [ ] **Social Features** (Teilen, Bewertungen)
- [x] **Erweiterte Statistiken** (Build Info, Deploy Info)
- [x] **Dark/Light Mode**
- [x] **Verbesserte Karten-Darstellung** (Overlay aller Touren als GeoJSON)
- [ ] **Export-Funktionen** (GPX, PDF Reports)
- [ ] **CI/CD Pipeline Verbesserungen**
- [ ] **Test Coverage Erhöhung**

## 📚 API Referenz

### Karten-bezogene Endpunkte

#### GeoJSON für alle Touren
```
GET /api/tours/geojson
```
Liefert alle Touren als GeoJSON FeatureCollection für die Kartendarstellung.

**Parameter:**
- `tour_type` (optional): Filtert nach Tour-Typ (z.B. "Wanderung", "Fahrradtour")
- `date_from` (optional): Startdatum im Format YYYY-MM-DD
- `date_to` (optional): Enddatum im Format YYYY-MM-DD
- `limit` (optional): Maximale Anzahl zurückgelieferter Touren (Default: 999999)

#### Debug-Endpunkt für Tour-GeoJSON
```
GET /api/debug/tours/{tour_id}
```
Debug-Endpunkt zum Prüfen der GeoJSON-Daten einer spezifischen Tour.

**Parameter:**
- `tour_id`: ID der zu debuggenden Tour

## 🤝 Contributing

1. Fork das Repository
2. Feature Branch erstellen
3. Änderungen committen
4. Pull Request erstellen

## 📄 Lizenz

MIT License - siehe LICENSE Datei für Details
