#!/bin/bash

# NUCLEAR OPTION - Completely rebuild the application
# This script creates a temporary fix by bypassing FastAPI entirely

# Stop any running containers first
echo "🛑 Stopping existing containers..."
docker-compose down

# Create a temporary directory for our fix
TEMP_DIR=$(mktemp -d)
echo "📁 Created temporary directory: $TEMP_DIR"

# Create a new Dockerfile with a direct fix
cat > $TEMP_DIR/Dockerfile.fix << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create data directory
RUN mkdir -p /app/data

# Copy application code
COPY . .

# Apply the fix directly
RUN echo "from fastapi.responses import JSONResponse" > /app/fixed_users.py && \
    echo "from fastapi import Depends, HTTPException" >> /app/fixed_users.py && \
    echo "from sqlalchemy.orm import Session" >> /app/fixed_users.py && \
    echo "" >> /app/fixed_users.py && \
    echo "def bypass_users(current_user, db, UserModel, UserRole):" >> /app/fixed_users.py && \
    echo "    \"\"\"Completely bypassed users endpoint\"\"\"" >> /app/fixed_users.py && \
    echo "    if current_user.role != UserRole.ADMIN:" >> /app/fixed_users.py && \
    echo "        raise HTTPException(status_code=403, detail=\"Not authorized to view user list\")" >> /app/fixed_users.py && \
    echo "" >> /app/fixed_users.py && \
    echo "    users = db.query(UserModel).all()" >> /app/fixed_users.py && \
    echo "" >> /app/fixed_users.py && \
    echo "    result = []" >> /app/fixed_users.py && \
    echo "    for user in users:" >> /app/fixed_users.py && \
    echo "        user_dict = {}" >> /app/fixed_users.py && \
    echo "        # Basic fields" >> /app/fixed_users.py && \
    echo "        for field in ['username', 'email']:" >> /app/fixed_users.py && \
    echo "            user_dict[field] = getattr(user, field, '') or ''" >> /app/fixed_users.py && \
    echo "" >> /app/fixed_users.py && \
    echo "        # Handle role" >> /app/fixed_users.py && \
    echo "        if hasattr(user, 'role'):" >> /app/fixed_users.py && \
    echo "            if user.role == UserRole.ADMIN:" >> /app/fixed_users.py && \
    echo "                user_dict['role'] = 'ADMIN'" >> /app/fixed_users.py && \
    echo "            else:" >> /app/fixed_users.py && \
    echo "                user_dict['role'] = 'USER'" >> /app/fixed_users.py && \
    echo "        else:" >> /app/fixed_users.py && \
    echo "            user_dict['role'] = 'USER'" >> /app/fixed_users.py && \
    echo "" >> /app/fixed_users.py && \
    echo "        # Handle status" >> /app/fixed_users.py && \
    echo "        user_dict['status'] = 'ACTIVE'" >> /app/fixed_users.py && \
    echo "        if hasattr(user, 'status'):" >> /app/fixed_users.py && \
    echo "            status_str = str(user.status)" >> /app/fixed_users.py && \
    echo "            if 'PENDING' in status_str:" >> /app/fixed_users.py && \
    echo "                user_dict['status'] = 'PENDING'" >> /app/fixed_users.py && \
    echo "            elif 'DISABLED' in status_str:" >> /app/fixed_users.py && \
    echo "                user_dict['status'] = 'DISABLED'" >> /app/fixed_users.py && \
    echo "" >> /app/fixed_users.py && \
    echo "        # Handle dates" >> /app/fixed_users.py && \
    echo "        for date_field in ['created_at', 'last_login']:" >> /app/fixed_users.py && \
    echo "            user_dict[date_field] = None" >> /app/fixed_users.py && \
    echo "            if hasattr(user, date_field) and getattr(user, date_field):" >> /app/fixed_users.py && \
    echo "                try:" >> /app/fixed_users.py && \
    echo "                    user_dict[date_field] = getattr(user, date_field).isoformat()" >> /app/fixed_users.py && \
    echo "                except:" >> /app/fixed_users.py && \
    echo "                    user_dict[date_field] = str(getattr(user, date_field))" >> /app/fixed_users.py && \
    echo "" >> /app/fixed_users.py && \
    echo "        result.append(user_dict)" >> /app/fixed_users.py && \
    echo "" >> /app/fixed_users.py && \
    echo "    return JSONResponse(content=result)" >> /app/fixed_users.py

# Create the main.py fix
RUN sed -i 's/@app.get("\/api\/users".*/@app.get("\/api\/users")\ndef list_users(current_user = Depends(get_current_active_user), db: Session = Depends(get_db)):\n    """List all users (admin only)"""\n    from fixed_users import bypass_users\n    return bypass_users(current_user, db, UserModel, UserRole)/g' /app/main.py

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug", "--no-access-log"]
EOF

# Create a new docker-compose.yml that uses our fixed Dockerfile
cat > $TEMP_DIR/docker-compose.fix.yml << 'EOF'
services:
  backend:
    build:
      context: ./backend
      dockerfile: ../fix/Dockerfile.fix
    ports:
      - "8000:8000"
    volumes:
      - ./scripts:/app/scripts
      - ./scripts:/scripts
      - ./data:/app/data
      - ./backend/utils:/app/utils
    env_file:
      - ./backend/.env
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-your-local-development-key}
      - DOCKER_ENV=true
      - DATABASE_PATH=/app/data/tourmanager.db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health || exit 1"]
      interval: 5s
      timeout: 10s
      retries: 10
      start_period: 40s

  frontend:
    build: ./frontend
    ports:
      - "3001:3000"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped

networks:
  default:
    name: tour-manager
EOF

# Create a directory for our fix files
mkdir -p /home/hts/pj/komoot/fix
cp $TEMP_DIR/Dockerfile.fix /home/hts/pj/komoot/fix/Dockerfile.fix
cp $TEMP_DIR/docker-compose.fix.yml /home/hts/pj/komoot/docker-compose.fix.yml

# Clean up
rm -rf $TEMP_DIR
echo "🧹 Cleaned up temporary files"

echo ""
echo "✅ NUCLEAR OPTION FILES CREATED!"
echo ""
echo "To apply the fix, run:"
echo "cd /home/hts/pj/komoot"
echo "docker-compose -f docker-compose.fix.yml up -d --build"
echo ""
echo "This will completely rebuild the application with a direct fix."
