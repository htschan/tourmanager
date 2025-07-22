# Tour Manager Deployment Guide

This guide explains how to deploy the Tour Manager application in different environments.

## Local Development

For local development, you can use the provided setup script:

```bash
./setup.sh
```

This script will:
1. Create necessary directories
2. Set up environment variables
3. Build and start the application using Docker Compose

After running the setup script, you can access:
- Frontend: http://localhost:3001
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Manual Setup

If you prefer to set up the application manually:

1. Create a `.env` file in the backend directory:

```bash
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
```

2. Create a data directory:

```bash
mkdir -p data
```

3. Build and start the application:

```bash
docker-compose up --build
```

## Production Deployment

For production deployment:

1. Create a `.env` file with production settings:

```bash
JWT_SECRET_KEY=your-secure-secret-key
MAIL_USERNAME=your-production-email@example.com
MAIL_PASSWORD=your-production-email-password
MAIL_FROM=noreply@yourdomain.com
MAIL_PORT=587
MAIL_SERVER=smtp.yourdomain.com
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
FRONTEND_URL=https://your-domain.com
```

2. Use the production Docker Compose file:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Using GitHub Container Registry

The application can be deployed using pre-built images from GitHub Container Registry:

1. Edit the docker-compose.yml file and uncomment the image lines:

```yaml
services:
  backend:
    # build: ./backend
    image: ghcr.io/USERNAME/REPO/backend:latest
    # ...

  frontend:
    # build: ./frontend
    image: ghcr.io/USERNAME/REPO/frontend:latest
    # ...
```

2. Replace `USERNAME/REPO` with your GitHub username and repository name.

3. Start the application:

```bash
docker-compose up -d
```

## Environment Variables

### Backend

| Variable | Description | Default |
|----------|-------------|---------|
| JWT_SECRET_KEY | Secret key for JWT token generation | None |
| DATABASE_PATH | Path to the SQLite database file | /app/data/tourmanager.db |
| MAIL_USERNAME | SMTP username for sending emails | None |
| MAIL_PASSWORD | SMTP password for sending emails | None |
| MAIL_FROM | Email address to send from | None |
| MAIL_PORT | SMTP port | 587 |
| MAIL_SERVER | SMTP server address | smtp.gmail.com |
| MAIL_STARTTLS | Use STARTTLS | True |
| MAIL_SSL_TLS | Use SSL/TLS | False |
| FRONTEND_URL | URL of the frontend application | http://localhost:3001 |

### Frontend

| Variable | Description | Default |
|----------|-------------|---------|
| VITE_API_BASE_URL | URL of the backend API | http://localhost:8000 |

## Backup and Restore

To backup the database:

```bash
docker exec -it tourmanager-backend-1 sqlite3 /app/data/tourmanager.db .dump > backup.sql
```

To restore the database:

```bash
cat backup.sql | docker exec -i tourmanager-backend-1 sqlite3 /app/data/tourmanager.db
```

## Health Checks

The backend service includes a health check endpoint at `/health`. You can monitor this endpoint to ensure the application is running correctly:

```bash
curl http://localhost:8000/health
```

## Logs

View application logs:

```bash
docker-compose logs -f
```

To view logs for a specific service:

```bash
docker-compose logs -f backend
# or
docker-compose logs -f frontend
```
