FROM python:3.11-slim

# Create a non-root user with explicit UID/GID
RUN groupadd -r appgroup --gid=1000 && \
    useradd -r -g appgroup --uid=1000 -d /app appuser

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories and set ownership
RUN mkdir -p /app/scripts /app/data && \
    chown -R appuser:appgroup /app

# Switch to non-root user for subsequent commands
USER appuser

# Python dependencies - install as non-root user
COPY --chown=appuser:appgroup requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Add local user binary to PATH
ENV PATH=/app/.local/bin:$PATH

# Copy application code as non-root user
COPY --chown=appuser:appgroup . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
