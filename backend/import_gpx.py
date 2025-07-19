import gpxpy
import gpxpy.gpx
import sqlite3
import os
import json
from sqlalchemy import create_engine, text

# --- Konfiguration ---
GPX_FOLDER = '../touren'  # <-- HIER DEINEN PFAD EINFÜGEN

# Set default database path based on environment
if os.getenv("DOCKER_ENV") == "true":
    DATABASE_FILE = "/app/data/tourmanager.db"
else:
    DATABASE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tourmanager.db')

# Allow override via environment variable
DATABASE_FILE = os.getenv("DATABASE_PATH", DATABASE_FILE)

engine = create_engine(f'sqlite:///{DATABASE_FILE}')

def parse_and_store_gpx(file_path):
    """Liest eine GPX-Datei, extrahiert die Daten und speichert sie in der DB."""
    print(f"Verarbeite: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    # Metadaten auslesen
    tour_name = gpx.name or os.path.splitext(os.path.basename(file_path))[0]
    
    # Name bereinigen: '(Completed)' entfernen
    if '(Completed)' in tour_name:
        tour_name = tour_name.replace('(Completed)', '').strip()
    
    # Tour-Typ basierend auf Name bestimmen
    tour_name_lower = tour_name.lower()
    if 'fahrradtour' in tour_name_lower:
        tour_type = 'Bike'
    elif 'wanderung' in tour_name_lower:
        tour_type = 'Hike'
    elif 'inline' in tour_name_lower:
        tour_type = 'Inline'
    elif 'mountainbike' in tour_name_lower:
        tour_type = 'Bike'
    elif 'e-bike' in tour_name_lower:
        tour_type = 'Bike'
    else:
        tour_type = 'Undefined'
    
    # E-Bike erkennen
    is_ebike = 'e-bike' in tour_name_lower or 'ebike' in tour_name_lower or 'husq' in tour_name_lower
    
    moving_data = gpx.get_moving_data()
    
    # Höhendaten berechnen
    uphill, downhill = gpx.get_uphill_downhill()
    elevation_up = uphill if uphill else 0.0
    elevation_down = downhill if downhill else 0.0
    
    # Geschwindigkeit berechnen (km/h)
    speed_kmh = 0.0
    if moving_data and moving_data.moving_time and moving_data.moving_time > 0:
        # Geschwindigkeit = Distanz (km) / Zeit (h)
        distance_km = moving_data.moving_distance / 1000
        time_hours = moving_data.moving_time / 3600
        speed_kmh = distance_km / time_hours
    
    # Tour-Typ korrigieren falls "Undefined" basierend auf Geschwindigkeit
    if tour_type == 'Undefined' and speed_kmh > 0:
        if speed_kmh < 8:
            tour_type = 'Hike'
        else:
            tour_type = 'Bike'
    
    # GeoJSON für die Karte erstellen und ersten Trackpunkt mit Timestamp finden
    # Gleichzeitig Komoot ID und href aus Track-Link-Element extrahieren
    points = []
    first_point_time = None
    komoot_id = None
    komoot_href = None
    import re
    
    for track in gpx.tracks:
        # Komoot ID und href aus Link-Element im Track extrahieren
        if komoot_id is None and hasattr(track, 'link') and track.link:
            if isinstance(track.link, str) and 'komoot' in track.link.lower():
                komoot_href = track.link  # Gesamte URL speichern
                # Extrahiere ID aus URLs wie https://www.komoot.de/tour/123456789
                match = re.search(r'/tour/(\d+)', track.link)
                if match:
                    komoot_id = match.group(1)
        
        for segment in track.segments:
            for point in segment.points:
                # Format: [Longitude, Latitude]
                points.append([point.longitude, point.latitude])
                
                # Timestamp vom ersten Trackpunkt verwenden
                if first_point_time is None and point.time:
                    first_point_time = point.time

    if not points:
        print(f"Warnung: Tour {tour_name} hat keine Trackpunkte und wird übersprungen.")
        return "skipped"

    # Prüfen ob Komoot ID bereits in der Datenbank existiert
    if komoot_id:
        with engine.connect() as connection:
            check_stmt = text("SELECT COUNT(*) FROM tours WHERE komootid = :komootid")
            result = connection.execute(check_stmt, {"komootid": komoot_id})
            exists = result.fetchone()[0] > 0
            
            if exists:
                print(f"Tour mit Komoot ID {komoot_id} existiert bereits - übersprungen")
                return "exists"

    # Tour-Datum: Verwende Timestamp vom ersten Trackpunkt, sonst Fallback
    tour_date = first_point_time.isoformat() if first_point_time else (gpx.time.isoformat() if gpx.time else '1970-01-01T00:00:00Z')
    
    start_lon, start_lat = points[0]
    
    track_geojson_str = json.dumps({
        "type": "LineString",
        "coordinates": points
    })
    
    # In die Datenbank schreiben
    with engine.begin() as connection:
        stmt = text("""
            INSERT INTO tours (name, type, date, distance_km, duration_s, start_lat, start_lon, track_geojson, komootid, komoothref, ebike, speed_kmh, elevation_up, elevation_down)
            VALUES (:name, :type, :date, :distance, :duration, :start_lat, :start_lon, :track_geojson, :komootid, :komoothref, :ebike, :speed_kmh, :elevation_up, :elevation_down)
        """)
        connection.execute(stmt, {
            "name": tour_name,
            "type": tour_type,
            "date": tour_date,
            "ebike": is_ebike,
            "speed_kmh": round(speed_kmh, 2),
            "distance": moving_data.moving_distance / 1000 if moving_data else 0,
            "duration": moving_data.moving_time if moving_data else 0,
            "start_lat": start_lat,
            "start_lon": start_lon,
            "track_geojson": track_geojson_str,
            "komootid": komoot_id,
            "komoothref": komoot_href,
            "elevation_up": round(elevation_up, 2),
            "elevation_down": round(elevation_down, 2)
        })
        # connection.commit() -- not needed with begin()
    
    return "imported"

if __name__ == '__main__':
    # Initialisiere die Datenbank-Tabelle, falls sie nicht existiert
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS tours (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                name TEXT NOT NULL, 
                type TEXT, 
                date TEXT NOT NULL,
                ebike BOOLEAN DEFAULT 0,
                speed_kmh REAL DEFAULT 0,
                distance_km REAL, 
                duration_s REAL, 
                elevation_up REAL DEFAULT 0,
                elevation_down REAL DEFAULT 0,
                start_lat REAL, 
                start_lon REAL, 
                komootid TEXT UNIQUE,
                komoothref TEXT,
                track_geojson TEXT NOT NULL
            );
        """))
        
        # Index auf komootid erstellen für bessere Performance
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_komootid ON tours(komootid);
        """))
        
        # connection.commit() -- not needed with begin()

    # Alle GPX-Dateien im Ordner verarbeiten
    imported_count = 0
    existing_count = 0
    skipped_count = 0
    
    for filename in os.listdir(GPX_FOLDER):
        if filename.lower().endswith('.gpx'):
            full_path = os.path.join(GPX_FOLDER, filename)
            result = parse_and_store_gpx(full_path)
            
            if result == "imported":
                imported_count += 1
            elif result == "exists":
                existing_count += 1
            elif result == "skipped":
                skipped_count += 1
    
    print(f"✅ Import abgeschlossen:")
    print(f"   {imported_count} Touren importiert")
    print(f"   {existing_count} Touren bereits vorhanden")
    if skipped_count > 0:
        print(f"   {skipped_count} Touren übersprungen (keine Trackpunkte)")