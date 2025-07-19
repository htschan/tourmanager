#!/bin/bash
# Map testing script for komoot tour manager
# This script helps test map functionality by providing test commands

echo "=== Komoot Tour Manager Map Testing ==="
echo "This script will help you test the map functionality"

# Get a sample tour ID for testing
SAMPLE_TOUR=$(curl -s http://localhost:8000/api/tours | jq '.[0].id' 2>/dev/null)

if [ -z "$SAMPLE_TOUR" ]; then
  echo "❌ Error: Could not fetch sample tour. Make sure the backend is running."
  echo "  Try: docker compose up -d backend"
  exit 1
fi

echo "✅ Found tour with ID: $SAMPLE_TOUR"
echo 
echo "=== Test Commands ==="
echo "1. Test single tour map display:"
echo "   curl http://localhost:8000/api/tours/$SAMPLE_TOUR"
echo
echo "2. Test GeoJSON endpoint for all tours:"
echo "   curl http://localhost:8000/api/tours/geojson | jq"
echo
echo "3. Open in browser to verify map rendering:"
echo "   http://localhost:3000/tours/$SAMPLE_TOUR"
echo
echo "=== Troubleshooting Tips ==="
echo "• If map doesn't appear, check browser console for errors"
echo "• Verify DOM container 'tour-map' exists before map initialization"
echo "• Ensure both backend and frontend containers are running"
echo

# Make the test requests
echo "=== Running Basic API Tests ==="
echo "Testing tour endpoint..."
curl -s "http://localhost:8000/api/tours/$SAMPLE_TOUR" | jq '.name' 2>/dev/null
echo

echo "Testing GeoJSON endpoint..."
curl -s "http://localhost:8000/api/tours/geojson" | jq '.features | length' 2>/dev/null
echo " GeoJSON features found"
echo 
echo "=== Done ==="
echo "Open http://localhost:3000/tours/$SAMPLE_TOUR in your browser to complete testing"
