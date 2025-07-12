FROM node:18-alpine

# Build arguments
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_BUILD_TIMESTAMP
ARG VITE_GIT_SHA

# Environment variables for runtime
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_BUILD_TIMESTAMP=$VITE_BUILD_TIMESTAMP
ENV VITE_GIT_SHA=$VITE_GIT_SHA

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies and tools
RUN apk add --no-cache imagemagick librsvg potrace
RUN npm install

# Copy source code
COPY . .

# Generate favicons from SVG
RUN mkdir -p /app/dist && \
    magick convert -background none -resize 16x16 public/favicon.svg dist/favicon-16x16.png && \
    magick convert -background none -resize 32x32 public/favicon.svg dist/favicon-32x32.png && \
    magick convert -background none -resize 180x180 public/favicon.svg dist/apple-touch-icon.png && \
    magick convert -background none -resize 192x192 public/favicon.svg dist/android-chrome-192x192.png && \
    magick convert -background none -resize 512x512 public/favicon.svg dist/android-chrome-512x512.png && \
    magick convert -background none -resize 150x150 public/favicon.svg dist/mstile-150x150.png && \
    cp public/favicon.svg dist/ && \
    cp public/favicon.svg dist/safari-pinned-tab.svg

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Copy and set up entrypoint script
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

# Use serve to host the static files
RUN npm install -g serve

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["serve", "-s", "dist", "-l", "3000"]
