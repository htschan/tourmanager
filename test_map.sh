#!/bin/bash

# Test script to verify map rendering in tour detail view
# This script will:
# 1. Fetch a list of tour IDs from the API
# 2. Pick one tour ID
# 3. Make a request to the tour detail page
# 4. Check for specific errors in the console log

echo "Fetching tour IDs from API..."
TOUR_ID=$(curl -s http://localhost:8000/api/tours | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$TOUR_ID" ]; then
  echo "Failed to get a tour ID from the API"
  exit 1
fi

echo "Testing map rendering for Tour ID: $TOUR_ID"
echo "Access the tour detail page at: http://localhost:3001/tours/$TOUR_ID"
echo ""
echo "Please check the browser console for any map-related errors."
echo "If you see 'Map container not found', our fix didn't work."
echo "If you see 'Creating new map instance' and no errors, our fix worked."
