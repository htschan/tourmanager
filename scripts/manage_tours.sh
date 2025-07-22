#!/bin/bash

# ====================================================
# Tour Manager - GPX Management Utility
# ====================================================
#
# A comprehensive utility script for managing Komoot tour GPX files
# 
# Features:
# - Import GPX files into the database
# - Analyze GPX statistics
# - Export tour data to various formats
# - Visualize tours on map
# - Batch operations on multiple files
#
# Usage:
#   ./scripts/manage_tours.sh [command] [options]
#
# Author: GitHub Copilot
# Version: 1.0
# ====================================================

# Color definitions for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Path configurations
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TOUREN_DIR="$PROJECT_ROOT/touren"
BACKEND_DIR="$PROJECT_ROOT/backend"
DB_FILE="$SCRIPT_DIR/touren.db"

# ====================================================
# Helper functions
# ====================================================

# Display script usage information
show_help() {
    echo -e "${BLUE}Tour Manager - GPX Management Utility${NC}"
    echo
    echo "Usage:"
    echo "  ./scripts/manage_tours.sh [command] [options]"
    echo
    echo "Commands:"
    echo "  import      Import GPX files into the database"
    echo "  stats       Display statistics about tours"
    echo "  export      Export tour data to various formats"
    echo "  visualize   Show tours on interactive map"
    echo "  cleanup     Clean up database or fix issues"
    echo "  help        Show this help message"
    echo
    echo "Options:"
    echo "  --file=<file>       Specify a single GPX file"
    echo "  --all               Process all GPX files in the touren directory"
    echo "  --force             Force operation without confirmation"
    echo "  --format=<format>   Specify export format (json, csv, geojson)"
    echo "  --output=<dir>      Specify output directory"
    echo
    echo "Examples:"
    echo "  ./scripts/manage_tours.sh import --all"
    echo "  ./scripts/manage_tours.sh stats"
    echo "  ./scripts/manage_tours.sh export --format=geojson --output=./exports"
    echo "  ./scripts/manage_tours.sh visualize --file=my_tour.gpx"
    echo
}

# Check if Python environment is properly set up
check_python_env() {
    echo -e "${BLUE}Checking Python environment...${NC}"
    
    # Check if python is installed
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is not installed.${NC}"
        exit 1
    fi
    
    # Check if required packages are installed
    if ! python3 -c "import gpxpy" &> /dev/null; then
        echo -e "${YELLOW}Installing required Python packages...${NC}"
        pip3 install gpxpy pandas matplotlib folium geojson sqlite3
    fi
    
    echo -e "${GREEN}Python environment is ready.${NC}"
}

# Count GPX files in the tours directory
count_gpx_files() {
    find "$TOUREN_DIR" -name "*.gpx" | wc -l
}

# ====================================================
# Core functionality
# ====================================================

# Import GPX files into database
import_gpx_files() {
    local file="$1"
    local force="$2"
    
    check_python_env
    
    echo -e "${BLUE}Importing GPX files to database...${NC}"
    
    if [[ -n "$file" ]]; then
        if [[ ! -f "$file" ]]; then
            echo -e "${RED}Error: File not found: $file${NC}"
            exit 1
        fi
        
        echo -e "${YELLOW}Importing single file: ${file}${NC}"
        python3 "$SCRIPT_DIR/import_gpx.py" "$file" "$DB_FILE"
        
    elif [[ "$force" == "true" ]]; then
        echo -e "${YELLOW}Importing all GPX files from ${TOUREN_DIR}${NC}"
        python3 "$SCRIPT_DIR/import_gpx.py" "$TOUREN_DIR" "$DB_FILE"
        
    else
        local file_count=$(count_gpx_files)
        echo -e "${YELLOW}Found $file_count GPX files in ${TOUREN_DIR}${NC}"
        read -p "Do you want to import all of these files? (y/n): " confirm
        
        if [[ "$confirm" == [Yy]* ]]; then
            python3 "$SCRIPT_DIR/import_gpx.py" "$TOUREN_DIR" "$DB_FILE"
        else
            echo -e "${YELLOW}Import cancelled.${NC}"
            return 1
        fi
    fi
    
    echo -e "${GREEN}Import complete.${NC}"
}

# Display statistics about tours
show_stats() {
    check_python_env
    
    echo -e "${BLUE}Generating tour statistics...${NC}"
    
    # Create temporary Python script for stats
    local tmp_script=$(mktemp)
    cat > "$tmp_script" <<EOF
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# Connect to database
conn = sqlite3.connect('$DB_FILE')
cursor = conn.cursor()

# Get tour stats
cursor.execute('''
    SELECT 
        COUNT(*) as total_tours,
        SUM(distance) as total_distance,
        SUM(duration) as total_duration,
        AVG(distance) as avg_distance,
        MAX(distance) as max_distance,
        MIN(distance) as min_distance
    FROM tours
''')

stats = cursor.fetchone()
print(f"\033[1mOverall Statistics:\033[0m")
print(f"Total tours: {stats[0]}")
print(f"Total distance: {stats[1]:.2f} km")
print(f"Total duration: {stats[2]:.2f} hours")
print(f"Average distance: {stats[3]:.2f} km")
print(f"Longest tour: {stats[4]:.2f} km")
print(f"Shortest tour: {stats[5]:.2f} km")

# Get tours by month
cursor.execute('''
    SELECT 
        strftime('%Y-%m', start_time) as month,
        COUNT(*) as tour_count,
        SUM(distance) as total_distance
    FROM tours
    GROUP BY month
    ORDER BY month
''')

monthly_data = cursor.fetchall()
months = [row[0] for row in monthly_data]
counts = [row[1] for row in monthly_data]
distances = [row[2] for row in monthly_data]

# Generate simple text-based bar chart
if months:
    print("\n\033[1mMonthly Activity:\033[0m")
    max_count = max(counts)
    for i, month in enumerate(months):
        bar = "█" * int(counts[i] / max_count * 20)
        print(f"{month}: {bar} ({counts[i]} tours, {distances[i]:.2f} km)")

conn.close()
EOF
    
    # Run the stats script
    python3 "$tmp_script"
    
    # Clean up
    rm "$tmp_script"
}

# Export tour data to various formats
export_tours() {
    local format="$1"
    local output_dir="$2"
    
    if [[ -z "$format" ]]; then
        format="geojson"
    fi
    
    if [[ -z "$output_dir" ]]; then
        output_dir="$PROJECT_ROOT/exports"
    fi
    
    # Create output directory if it doesn't exist
    mkdir -p "$output_dir"
    
    check_python_env
    
    echo -e "${BLUE}Exporting tour data to ${format}...${NC}"
    
    # Create temporary Python script for export
    local tmp_script=$(mktemp)
    cat > "$tmp_script" <<EOF
import sqlite3
import pandas as pd
import json
import os
import datetime

# Connect to database
conn = sqlite3.connect('$DB_FILE')

# Format-specific export
if '$format' == 'json':
    # Export to JSON
    df = pd.read_sql_query("SELECT * FROM tours", conn)
    # Convert datetime objects to strings for JSON serialization
    for col in df.select_dtypes(include=['datetime64']).columns:
        df[col] = df[col].astype(str)
    
    output_file = os.path.join('$output_dir', 'tours.json')
    df.to_json(output_file, orient='records', indent=2)
    print(f"Exported {len(df)} tours to {output_file}")
    
elif '$format' == 'csv':
    # Export to CSV
    df = pd.read_sql_query("SELECT * FROM tours", conn)
    output_file = os.path.join('$output_dir', 'tours.csv')
    df.to_csv(output_file, index=False)
    print(f"Exported {len(df)} tours to {output_file}")
    
elif '$format' == 'geojson':
    # Export to GeoJSON
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, start_time, end_time, distance, path_data FROM tours")
    tours = cursor.fetchall()
    
    features = []
    for tour in tours:
        id, name, start_time, end_time, distance, path_data = tour
        
        if path_data:
            path = json.loads(path_data)
            coordinates = [[point[1], point[0]] for point in path]  # GeoJSON uses [lon, lat] order
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coordinates
                },
                "properties": {
                    "id": id,
                    "name": name,
                    "start_time": start_time,
                    "end_time": end_time,
                    "distance": distance
                }
            }
            features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    output_file = os.path.join('$output_dir', 'tours.geojson')
    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"Exported {len(features)} tours to {output_file}")
    
else:
    print(f"Unknown format: $format")

conn.close()
EOF
    
    # Run the export script
    python3 "$tmp_script"
    
    # Clean up
    rm "$tmp_script"
    
    echo -e "${GREEN}Export complete. Files saved to ${output_dir}${NC}"
}

# Visualize tours on map
visualize_tours() {
    local file="$1"
    
    check_python_env
    
    echo -e "${BLUE}Generating interactive map visualization...${NC}"
    
    # Create temporary Python script for visualization
    local tmp_script=$(mktemp)
    cat > "$tmp_script" <<EOF
import sqlite3
import folium
import json
import random
import os
import sys
import webbrowser
from datetime import datetime

# Connect to database
conn = sqlite3.connect('$DB_FILE')
cursor = conn.cursor()

# Generate a colorful map
m = folium.Map(location=[47.3769, 8.5417], zoom_start=10)  # Default center on Zurich

if '$file':
    # Visualize a specific GPX file
    import gpxpy
    
    try:
        with open('$file', 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
            
        # Extract track points
        points = []
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    points.append((point.latitude, point.longitude))
        
        if points:
            # Create a polyline for the tour
            folium.PolyLine(
                points,
                color='blue',
                weight=5,
                opacity=0.8
            ).add_to(m)
            
            # Adjust map center to the first point of the tour
            m.location = points[0]
            
            # Add start and end markers
            folium.Marker(
                points[0],
                popup='Start',
                icon=folium.Icon(color='green', icon='play')
            ).add_to(m)
            
            folium.Marker(
                points[-1],
                popup='End',
                icon=folium.Icon(color='red', icon='stop')
            ).add_to(m)
            
            print(f"Visualizing tour from {os.path.basename('$file')}")
    
    except Exception as e:
        print(f"Error processing GPX file: {e}")
        sys.exit(1)
else:
    # Visualize all tours from database
    cursor.execute("SELECT id, name, path_data FROM tours")
    tours = cursor.fetchall()
    
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 
              'lightred', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 
              'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'beige']
    
    for tour_id, name, path_data in tours:
        if path_data:
            try:
                path = json.loads(path_data)
                points = [(point[0], point[1]) for point in path]
                
                # Random color for each tour
                color = random.choice(colors)
                
                # Create a polyline for the tour
                folium.PolyLine(
                    points,
                    color=color,
                    weight=3,
                    opacity=0.7,
                    popup=name
                ).add_to(m)
                
            except Exception as e:
                print(f"Error processing tour {tour_id}: {e}")
    
    print(f"Visualizing {len(tours)} tours from database")

# Save and open the map
output_file = os.path.join('$PROJECT_ROOT', 'tour_map.html')
m.save(output_file)
print(f"Map saved to {output_file}")

# Try to open in browser
try:
    webbrowser.open('file://' + os.path.abspath(output_file))
except:
    print(f"Please open the map manually: {output_file}")

conn.close()
EOF
    
    # Run the visualization script
    python3 "$tmp_script"
    
    # Clean up
    rm "$tmp_script"
}

# Clean up database or fix issues
cleanup_database() {
    echo -e "${BLUE}Performing database cleanup and maintenance...${NC}"
    
    # Check if database exists
    if [[ ! -f "$DB_FILE" ]]; then
        echo -e "${YELLOW}Database file not found. Creating new database...${NC}"
        
        # Create temporary Python script to initialize database
        local tmp_script=$(mktemp)
        cat > "$tmp_script" <<EOF
import sqlite3
import os

# Create database connection
conn = sqlite3.connect('$DB_FILE')
cursor = conn.cursor()

# Create tours table
cursor.execute('''
CREATE TABLE IF NOT EXISTS tours (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    komoot_id TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    distance REAL,
    duration REAL,
    ascent REAL,
    descent REAL,
    avg_speed REAL,
    max_speed REAL,
    path_data TEXT,
    gpx_file TEXT,
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()

print("Database initialized successfully.")
EOF
        
        # Run the initialization script
        python3 "$tmp_script"
        
        # Clean up
        rm "$tmp_script"
    else
        echo -e "${YELLOW}Performing maintenance on existing database...${NC}"
        
        # Create temporary Python script for database maintenance
        local tmp_script=$(mktemp)
        cat > "$tmp_script" <<EOF
import sqlite3
import os

# Connect to database
conn = sqlite3.connect('$DB_FILE')
cursor = conn.cursor()

# Check for and remove duplicate entries
cursor.execute('''
    SELECT komoot_id, COUNT(*) as count 
    FROM tours 
    GROUP BY komoot_id 
    HAVING count > 1 AND komoot_id IS NOT NULL
''')
duplicates = cursor.fetchall()

if duplicates:
    print(f"Found {len(duplicates)} tours with duplicate komoot_ids")
    
    for komoot_id, count in duplicates:
        print(f"  - Removing {count-1} duplicates for tour {komoot_id}")
        
        # Keep the most recent entry, delete others
        cursor.execute('''
            DELETE FROM tours 
            WHERE komoot_id = ? AND id NOT IN (
                SELECT MAX(id) FROM tours WHERE komoot_id = ?
            )
        ''', (komoot_id, komoot_id))
else:
    print("No duplicate tours found.")

# Check for orphaned entries (no GPX file)
cursor.execute('''
    SELECT id, name, gpx_file FROM tours 
    WHERE gpx_file IS NOT NULL
''')
tours = cursor.fetchall()

orphaned = 0
for tour_id, tour_name, gpx_file in tours:
    if not os.path.exists(gpx_file):
        print(f"  - Orphaned tour: {tour_name} (ID: {tour_id})")
        orphaned += 1

if orphaned:
    print(f"Found {orphaned} tours with missing GPX files")
    response = input("Do you want to remove these orphaned entries? (y/n): ")
    
    if response.lower() == 'y':
        cursor.execute('''
            DELETE FROM tours 
            WHERE gpx_file IS NOT NULL AND id IN (
                SELECT id FROM tours WHERE gpx_file NOT IN (
                    SELECT DISTINCT gpx_file FROM tours 
                    WHERE gpx_file IS NOT NULL
                )
            )
        ''')
        print(f"Removed {orphaned} orphaned tour entries")
else:
    print("No orphaned tour entries found.")

# Optimize database
print("Optimizing database...")
cursor.execute("VACUUM")

# Commit changes and close connection
conn.commit()
conn.close()

print("Database maintenance completed successfully.")
EOF
        
        # Run the maintenance script
        python3 "$tmp_script"
        
        # Clean up
        rm "$tmp_script"
    fi
    
    echo -e "${GREEN}Database cleanup complete.${NC}"
}

# ====================================================
# Main script execution
# ====================================================

# Process command line arguments
if [[ $# -eq 0 ]]; then
    show_help
    exit 0
fi

# Parse command
COMMAND="$1"
shift

# Parse options
FILE=""
FORMAT="geojson"
OUTPUT_DIR="$PROJECT_ROOT/exports"
FORCE="false"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --file=*)
            FILE="${1#*=}"
            shift
            ;;
        --format=*)
            FORMAT="${1#*=}"
            shift
            ;;
        --output=*)
            OUTPUT_DIR="${1#*=}"
            shift
            ;;
        --all)
            FORCE="true"
            shift
            ;;
        --force)
            FORCE="true"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Execute requested command
case "$COMMAND" in
    import)
        import_gpx_files "$FILE" "$FORCE"
        ;;
    stats)
        show_stats
        ;;
    export)
        export_tours "$FORMAT" "$OUTPUT_DIR"
        ;;
    visualize)
        visualize_tours "$FILE"
        ;;
    cleanup)
        cleanup_database
        ;;
    help)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        show_help
        exit 1
        ;;
esac

exit 0
