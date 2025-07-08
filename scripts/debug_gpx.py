import gpxpy
import os

# Test with one GPX file to debug link structure
gpx_file = '../touren/Andelfingen Altikon Fahrradtour 16.08.2020 0956-239946769.gpx'

with open(gpx_file, 'r', encoding='utf-8') as f:
    gpx = gpxpy.parse(f)

print("GPX attributes:")
print(f"  Has link attribute: {hasattr(gpx, 'link')}")
print(f"  Has links attribute: {hasattr(gpx, 'links')}")
print(f"  Has metadata: {hasattr(gpx, 'metadata')}")

if hasattr(gpx, 'metadata') and gpx.metadata:
    print(f"  Metadata has links: {hasattr(gpx.metadata, 'links')}")
    if hasattr(gpx.metadata, 'links'):
        print("GPX metadata links:")
        for link in gpx.metadata.links:
            print(f"  Link href: {link.href}")
            print(f"  Link text: {link.text}")

print("\nTracks:")
for i, track in enumerate(gpx.tracks):
    print(f"Track {i}:")
    print(f"  Name: {track.name}")
    print(f"  Has link attribute: {hasattr(track, 'link')}")
    print(f"  Has links attribute: {hasattr(track, 'links')}")
    
    if hasattr(track, 'link') and track.link:
        print(f"  track.link type: {type(track.link)}")
        print(f"  track.link value: {track.link}")
    
    if hasattr(track, 'links'):
        print(f"  track.links count: {len(track.links)}")
        for j, link in enumerate(track.links):
            print(f"    Link {j}:")
            print(f"      href: {link.href}")
            print(f"      text: {link.text}")
    
    # Let's check all attributes
    print(f"  All track attributes: {[attr for attr in dir(track) if not attr.startswith('_')]}")
    
    # Check for extensions which might contain additional data
    if hasattr(track, 'extensions') and track.extensions:
        print(f"  Track extensions: {track.extensions}")
    break  # Just check first track
