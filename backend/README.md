# Tour Manager Backend

Ein FastAPI-basiertes Backend für die Verwaltung und Visualisierung von GPX-Touren.

## Features

- 🚀 **FastAPI** mit automatischer API-Dokumentation
- 🗃️ **SQLite** Integration für Tour-Daten
- 🌍 **Geospatiale Suche** für Touren in der Nähe
- 📊 **Umfangreiche Filter** (Datum, Typ, Distanz, Höhe)
- 🗺️ **GeoJSON Export** für Kartendarstellung
- 📈 **Statistiken** und Zusammenfassungen

## API Endpoints

### Haupt-Endpoints
- `GET /` - Health Check
- `GET /api/tours` - Alle Touren mit Filtern
- `GET /api/tours/{id}` - Spezifische Tour mit Details
- `POST /api/tours/nearby` - Touren in der Nähe eines Standorts
- `GET /api/tours/summary` - Statistik-Übersicht
- `GET /api/tours/types` - Verfügbare Tour-Typen
- `GET /api/tours/geojson` - Touren als GeoJSON

### Filter-Parameter
- `tour_type`: Bike, Hike, Inline, etc.
- `date_from` / `date_to`: Datumsbereich
- `ebike_only`: Nur E-Bike Touren
- `min_distance` / `max_distance`: Distanzbereich
- `min_elevation`: Minimaler Höhenunterschied

## Installation

```bash
# Dependencies installieren
pip install -r requirements.txt

# Server starten
python main.py
```

## Docker

```bash
# Image bauen
docker build -t tour-manager-backend .

# Container starten
docker run -p 8000:8000 -v $(pwd)/../scripts:/app/scripts tour-manager-backend
```

## API Dokumentation

Nach dem Start verfügbar unter:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Konfiguration

- `DATABASE_FILE`: Pfad zur SQLite Datenbank (Standard: `../scripts/touren.db`)
- `PORT`: Server Port (Standard: 8000)
- `HOST`: Server Host (Standard: 0.0.0.0)

## Entwicklung

```bash
# Development Server mit Auto-Reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
