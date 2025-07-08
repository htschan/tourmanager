from sqlalchemy import create_engine, text
import os

DATABASE_FILE = os.path.join(os.path.dirname(__file__), 'scripts', 'touren.db')
engine = create_engine(f'sqlite:///{DATABASE_FILE}')

query = """
    SELECT id, name, type, date, distance_km, duration_s, speed_kmh, 
           elevation_up, elevation_down, start_lat, start_lon, ebike, komootid, komoothref, track_geojson
    FROM tours 
    ORDER BY date DESC LIMIT 1
"""

try:
    with engine.connect() as connection:
        result = connection.execute(text(query))
        row = result.fetchone()
        print(f"Total columns: {len(row)}")
        for i, value in enumerate(row):
            print(f"Column {i}: {type(value)} - {str(value)[:100] if value else 'None'}")
        
        print(f"\ntrack_geojson (index 14): {type(row[14])}")
        print(f"track_geojson is None: {row[14] is None}")
        if row[14]:
            print(f"track_geojson length: {len(row[14])}")
            print(f"track_geojson first 100 chars: {row[14][:100]}")
        
except Exception as e:
    print(f"Error: {e}")
