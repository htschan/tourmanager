FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create scripts directory and set permissions
RUN mkdir -p /app/scripts && chown -R nobody:nogroup /app/scripts

# App code
COPY . .

# Set permissions for the app directory
RUN chown -R nobody:nogroup /app

# Switch to non-root user
USER nobody

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
