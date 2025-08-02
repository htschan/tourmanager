import os
import tempfile
import traceback
import gpxpy
import gpxpy.gpx
import logging
from io import BytesIO
from defusedxml import ElementTree
from lxml import etree

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Optional: Try to import pykml for better KML parsing
try:
    from pykml import parser as kml_parser
    PYKML_AVAILABLE = True
except ImportError:
    logger.warning("pykml not available, using ElementTree for KML parsing")
    PYKML_AVAILABLE = False

def kml_to_gpx(kml_file_path):
    """
    Convert a KML file to GPX format.
    
    Args:
        kml_file_path (str): Path to the KML file
        
    Returns:
        str: Path to the newly created GPX file
    """
    logger.info(f"Converting KML file to GPX: {kml_file_path}")
    
    try:
        # Check file existence and size
        if not os.path.exists(kml_file_path):
            logger.error(f"KML file does not exist: {kml_file_path}")
            return None
            
        file_size = os.path.getsize(kml_file_path)
        logger.debug(f"KML file size: {file_size} bytes")
        
        if file_size == 0:
            logger.error(f"KML file is empty: {kml_file_path}")
            return None
            
        # Parse KML file
        namespaces = {
            'kml': 'http://www.opengis.net/kml/2.2',
            'gx': 'http://www.google.com/kml/ext/2.2'
        }
        
        logger.debug(f"Attempting to parse KML file: {kml_file_path}")
        
        # Use the most robust parsing method available
        if PYKML_AVAILABLE:
            try:
                with open(kml_file_path) as f:
                    doc = kml_parser.parse(f)
                    root = doc.getroot()
                    logger.debug(f"KML file successfully parsed with pykml, root: {root}")
            except Exception as e:
                logger.warning(f"pykml parsing failed, falling back to ElementTree: {str(e)}")
                tree = ElementTree.parse(kml_file_path)
                root = tree.getroot()
        else:
            tree = ElementTree.parse(kml_file_path)
            root = tree.getroot()
            
        logger.debug(f"KML file successfully parsed, root tag: {root.tag}")
        
        # Create new GPX file
        gpx = gpxpy.gpx.GPX()
        
        # Try to extract document name for the GPX name
        doc_name_elem = root.find(".//kml:Document/kml:name", namespaces)
        gpx_name = doc_name_elem.text if doc_name_elem is not None else os.path.splitext(os.path.basename(kml_file_path))[0]
        
        gpx.name = gpx_name
        
        # Extract track name from KML if available
        track_name = gpx_name
        track_name_elem = root.find(".//kml:Placemark/kml:name", namespaces)
        if track_name_elem is not None:
            track_name = track_name_elem.text
        
        # Create a track in our GPX
        gpx_track = gpxpy.gpx.GPXTrack(name=track_name)
        gpx.tracks.append(gpx_track)
        
        # Create a segment in our GPX track
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)
        
        # Find all placemarks with LineString or Track data
        placemarks = root.findall(".//kml:Placemark", namespaces)
        
        points_added = False
        
        logger.debug(f"Found {len(placemarks)} placemarks in KML file")
        
        for i, placemark in enumerate(placemarks):
            logger.debug(f"Processing placemark {i+1}/{len(placemarks)}")
            
            # Check for LineString coordinates
            coords = placemark.find(".//kml:LineString/kml:coordinates", namespaces)
            
            if coords is not None and coords.text:
                # Try to extract timestamp for this placemark
                time_elem = placemark.find(".//kml:TimeStamp/kml:when", namespaces)
                placemark_time = None
                if time_elem is not None and time_elem.text:
                    try:
                        from datetime import datetime
                        placemark_time = datetime.fromisoformat(time_elem.text.replace('Z', '+00:00'))
                    except Exception as e:
                        logger.warning(f"Could not parse LineString timestamp: {time_elem.text}, {str(e)}")
                
                # Split the coordinates text into individual point strings
                coord_text = coords.text.strip()
                coord_strings = coord_text.split()
                
                for coord_str in coord_strings:
                    # Each coordinate is comma-separated: longitude,latitude,altitude
                    parts = coord_str.split(',')
                    if len(parts) >= 2:
                        lon = float(parts[0])
                        lat = float(parts[1])
                        # Altitude is optional in KML
                        elevation = float(parts[2]) if len(parts) > 2 else None
                        
                        # Add point to the GPX segment - apply timestamp to all points in this LineString
                        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon, elevation=elevation, time=placemark_time))
                        points_added = True
            
            # Check for gx:Track data (newer KML format)
            gx_coords = placemark.findall(".//gx:Track/gx:coord", namespaces)
            gx_when = placemark.findall(".//gx:Track/kml:when", namespaces)
            
            if gx_coords:
                for i, coord in enumerate(gx_coords):
                    parts = coord.text.split()
                    if len(parts) >= 2:
                        lon = float(parts[0])
                        lat = float(parts[1])
                        elevation = float(parts[2]) if len(parts) > 2 else None
                        
                        # Try to extract timestamp if available
                        time = None
                        if gx_when and i < len(gx_when):
                            time_str = gx_when[i].text
                            try:
                                from datetime import datetime
                                time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                            except Exception as e:
                                logger.warning(f"Could not parse timestamp: {time_str}, {str(e)}")
                        
                        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon, elevation=elevation, time=time))
                        points_added = True
                        
            # Check for Point data (waypoints)
            point_coords = placemark.find(".//kml:Point/kml:coordinates", namespaces)
            
            if point_coords is not None and point_coords.text:
                parts = point_coords.text.strip().split(',')
                if len(parts) >= 2:
                    lon = float(parts[0])
                    lat = float(parts[1])
                    elevation = float(parts[2]) if len(parts) > 2 else None
                    
                    # For single points, create a waypoint
                    name = placemark.find("kml:name", namespaces)
                    waypoint_name = name.text if name is not None else "Waypoint"
                    
                    # Try to extract timestamp for waypoint
                    time_elem = placemark.find(".//kml:TimeStamp/kml:when", namespaces)
                    time = None
                    if time_elem is not None and time_elem.text:
                        try:
                            from datetime import datetime
                            time = datetime.fromisoformat(time_elem.text.replace('Z', '+00:00'))
                            logger.debug(f"Found timestamp for waypoint {waypoint_name}: {time}")
                        except Exception as e:
                            logger.warning(f"Could not parse waypoint timestamp: {time_elem.text}, {str(e)}")
                    
                    gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(lat, lon, elevation=elevation, name=waypoint_name, time=time))
                    points_added = True
        
        if not points_added:
            logger.warning(f"No valid track points found in KML file: {kml_file_path}")
            return None
        
        # Write GPX to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gpx', mode='w') as gpx_file:
            gpx_file.write(gpx.to_xml())
            gpx_path = gpx_file.name
            
        logger.info(f"KML successfully converted to GPX: {gpx_path}")
        return gpx_path
        
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error converting KML to GPX: {str(e)}")
        logger.error(f"Traceback: {error_trace}")
        logger.error(f"KML file path: {kml_file_path}")
        
        # Check if file exists and its size
        if os.path.exists(kml_file_path):
            logger.debug(f"KML file exists, size: {os.path.getsize(kml_file_path)} bytes")
            # Log first few bytes for debugging
            try:
                with open(kml_file_path, 'rb') as f:
                    content = f.read(200)
                    logger.debug(f"First 200 bytes: {content}")
            except Exception as read_error:
                logger.error(f"Error reading KML file: {str(read_error)}")
        else:
            logger.error(f"KML file does not exist at path: {kml_file_path}")
            
        return None
