import sqlite3

conn = sqlite3.connect('scripts/touren.db')
cursor = conn.cursor()

cursor.execute('''SELECT id, name, type, date, distance_km, duration_s, speed_kmh, 
                         elevation_up, elevation_down, start_lat, start_lon, ebike, 
                         komootid, komoothref, track_geojson 
                  FROM tours ORDER BY date DESC LIMIT 1''')

row = cursor.fetchone()
print(f'ID: {row[0]}')
print(f'Name: {row[1]}')
print(f'Track data is None: {row[14] is None}')
print(f'Track data type: {type(row[14])}')
if row[14]:
    print(f'Track data length: {len(row[14])}')
    print(f'Track first 100 chars: {row[14][:100]}')
else:
    print('Track data is None/NULL')

conn.close()
