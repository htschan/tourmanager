# Docker Swarm Deployment Notes

## Map Rendering Issues and Fixes

The map rendering issues in Docker Swarm production environments have been fixed by implementing the following changes:

### 1. CSS Consistency

- Updated all CSS selectors to ensure consistency between template and style sections:
  - Changed `.map-wrapper` to `.tour-map-wrapper` to match the HTML template
  - Fixed responsive CSS rules for mobile views
  - Made sure all CSS selectors reference the correct element IDs

### 2. DOM Structure Improvements

- Fixed HTML structure issues:
  - Removed extra div closing tags
  - Simplified the DOM hierarchy for easier selection
  - Added explicit IDs to all important elements

### 3. Map Initialization Improvements

- Enhanced map element finding logic:
  - Added multiple fallback strategies for finding map elements
  - Implemented checks for DOM readiness before initializing Leaflet
  - Added timeout delays specifically for production environments
  - Created robust element creation for cases where the container isn't found

### 4. Error Handling and Recovery

- Added robust error handling:
  - Multiple retry attempts with exponential backoff
  - Fresh container creation if map initialization fails
  - Informative console messages to help with debugging
  - Environment-specific adjustments (production vs development)

### 5. Leaflet-Specific Optimizations

- Modified Leaflet configuration for better Docker Swarm compatibility:
  - Disabled animations that could cause rendering issues
  - Used `preferCanvas: true` for better performance in production
  - Added additional controls (zoom, scale) at improved positions
  - Improved layer and tile loading strategies

## Deployment Configuration

The included files provide a complete setup for Docker Swarm deployment:

- `portainer-stack.yml`: Main stack configuration for Portainer
- `nginx.conf`: NGINX reverse proxy configuration
- Frontend and Backend Docker image configurations

## Environment Variables

Make sure to set these environment variables in your Docker Swarm environment:

```
EMAIL_HOST=smtp.fastmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your_username
EMAIL_PASSWORD=your_password
EMAIL_FROM=noreply@example.com
CORS_ORIGIN=https://yourdomain.com
```

## Monitoring

After deployment, monitor the browser console for any warnings or errors related to map rendering. The code now includes extensive logging to help identify issues.

## Further Improvements

Consider these additional improvements if needed:

1. Add Vue error boundaries around the map component
2. Implement lazy loading of the Leaflet library
3. Add more detailed telemetry for production environments
4. Create a simplified fallback map view for environments where WebGL isn't available
