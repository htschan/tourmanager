FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Create data directory
RUN mkdir -p /app/data

# Accept build arguments for package versions
ARG BCRYPT_VERSION=4.0.1
ARG PASSLIB_VERSION=1.7.4

# Install Python dependencies
COPY requirements.txt .
# Install specific versions of bcrypt and passlib first to ensure compatibility
RUN pip install --no-cache-dir bcrypt==${BCRYPT_VERSION} passlib[bcrypt]==${PASSLIB_VERSION}
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Set entrypoint to our script
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
