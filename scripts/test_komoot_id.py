import gpxpy
import re

# Test with one GPX file
gpx_file = '../touren/Andelfingen Altikon Fahrradtour 16.08.2020 0956-239946769.gpx'

with open(gpx_file, 'r', encoding='utf-8') as f:
    gpx = gpxpy.parse(f)

komoot_id = None
for track in gpx.tracks:
    if komoot_id is None and hasattr(track, 'link') and track.link:
        print(f"Found track link: {track.link}")
        if isinstance(track.link, str) and 'komoot' in track.link.lower():
            match = re.search(r'/tour/(\d+)', track.link)
            if match:
                komoot_id = match.group(1)
                print(f"Extracted Komoot ID: {komoot_id}")
                break

if komoot_id:
    print(f"✅ Successfully extracted Komoot ID: {komoot_id}")
else:
    print("❌ No Komoot ID found")
