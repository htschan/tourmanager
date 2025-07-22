#!/bin/bash

# Fresh setup script for Tour Manager

echo "🚀 Setting up a fresh Tour Manager application..."
echo "================================================"

# Make sure we're in the project root
cd "$(dirname "$0")"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker is not running! Please start Docker and try again."
  exit 1
fi

# Create necessary directories
echo "📁 Creating data directory..."
mkdir -p data

# Set up environment variables
echo "🔧 Setting up environment variables..."

if [ ! -f backend/.env ]; then
  echo "Creating backend/.env file..."
  cat > backend/.env << EOF
# Backend configuration
JWT_SECRET_KEY=change-this-in-production
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password
MAIL_FROM=your-email@example.com
MAIL_PORT=587
MAIL_SERVER=smtp.example.com
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
FRONTEND_URL=http://localhost:3001
EOF
fi

# Build and start the application
echo "🏗️ Building and starting the application..."
docker-compose up --build -d

echo "✅ Setup complete!"
echo ""
echo "🌐 Access the application at:"
echo "- Frontend: http://localhost:3001"
echo "- Backend API: http://localhost:8000"
echo "- API Documentation: http://localhost:8000/docs"
echo ""
echo "🔑 Default admin credentials:"
echo "- Username: admin"
echo "- Password: admin"
echo ""
echo "To check logs: docker-compose logs -f"
echo "To stop the application: docker-compose down"
