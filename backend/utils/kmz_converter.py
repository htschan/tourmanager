import os
import zipfile
import tempfile
import logging
from .kml_converter import kml_to_gpx

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def kmz_to_gpx(kmz_file_path):
    """
    Convert a KMZ file to GPX format by:
    1. Extracting the KML file from the KMZ archive
    2. Converting the extracted KML file to GPX
    
    Args:
        kmz_file_path (str): Path to the KMZ file
        
    Returns:
        str: Path to the newly created GPX file, or None if conversion failed
    """
    logger.info(f"Converting KMZ file to GPX: {kmz_file_path}")
    
    temp_dir = None
    try:
        # Check if file exists and is not empty
        if not os.path.exists(kmz_file_path):
            logger.error(f"KMZ file does not exist: {kmz_file_path}")
            return None
            
        file_size = os.path.getsize(kmz_file_path)
        logger.debug(f"KMZ file size: {file_size} bytes")
        
        if file_size == 0:
            logger.error(f"KMZ file is empty: {kmz_file_path}")
            return None
        
        # Create a temporary directory to extract the KMZ contents
        temp_dir = tempfile.mkdtemp()
        logger.debug(f"Created temporary directory: {temp_dir}")
        
        # Extract the KMZ file (it's just a zip archive)
        try:
            with zipfile.ZipFile(kmz_file_path, 'r') as zip_ref:
                # List the contents of the zip file
                file_list = zip_ref.namelist()
                logger.debug(f"KMZ archive contains: {file_list}")
                
                # Look for a KML file (typically doc.kml but could be named differently)
                kml_files = [f for f in file_list if f.endswith('.kml')]
                
                if not kml_files:
                    logger.error("No KML file found in the KMZ archive")
                    return None
                
                # Use the first KML file found (usually there's only one)
                kml_file_in_zip = kml_files[0]
                logger.info(f"Found KML file in archive: {kml_file_in_zip}")
                
                # Extract the KML file
                zip_ref.extract(kml_file_in_zip, temp_dir)
                
                # Path to the extracted KML file
                extracted_kml_path = os.path.join(temp_dir, kml_file_in_zip)
                logger.debug(f"KML file extracted to: {extracted_kml_path}")
                
                # Convert the extracted KML file to GPX
                gpx_path = kml_to_gpx(extracted_kml_path)
                if not gpx_path:
                    logger.error("Failed to convert extracted KML to GPX")
                    return None
                
                logger.info(f"KMZ successfully converted to GPX: {gpx_path}")
                return gpx_path
                
        except zipfile.BadZipFile:
            logger.error(f"Invalid KMZ file (not a valid zip archive): {kmz_file_path}")
            return None
            
    except Exception as e:
        logger.error(f"Error converting KMZ file: {str(e)}")
        return None
        
    finally:
        # Clean up the temporary directory if it was created
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
            logger.debug(f"Cleaned up temporary directory: {temp_dir}")
