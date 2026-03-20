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
docker compose up --build
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
docker compose -f docker-compose.prod.yml up -d
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
docker compose up -d
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
docker compose logs -f
```

To view logs for a specific service:

```bash
docker compose logs -f backend
# or
docker compose logs -f frontend
```

## Synology DS718+ Reverse Proxy (DSM 7.2)

The built-in reverse proxy in DSM lets you expose the frontend and backend through the Synology
without opening individual ports externally. The steps below assume the containers are either
running on the Synology itself (via Container Manager) or on another host in the same network.

### 1. Decide on hostnames

Pick one or two hostnames you will use, e.g.:

| Service  | Suggested hostname         | Target                              |
|----------|---------------------------|-------------------------------------|
| Frontend | `tours.yourdomain.com`     | `localhost:3001` (or `<host-ip>:3001`) |
| Backend  | `tours-api.yourdomain.com` | `localhost:8000` (or `<host-ip>:8000`) |

If you prefer a single hostname with path-based routing, see the alternative at the end of this section.

### 2. Open the Reverse Proxy manager

1. Log in to DSM.
2. Go to **Control Panel → Login Portal → Advanced** tab.
3. Click **Reverse Proxy**.

### 3. Add a rule for the frontend

Click **Create** and fill in:

| Field              | Value                                    |
|--------------------|------------------------------------------|
| Description        | `Tour Manager – Frontend`                |
| Source – Protocol  | `HTTPS` (or `HTTP` for LAN-only)         |
| Source – Hostname  | `tours.yourdomain.com`                   |
| Source – Port      | `443` (or `80`)                          |
| Destination – Protocol | `HTTP`                               |
| Destination – Hostname | `localhost` (or the Docker host IP)  |
| Destination – Port | `3001`                                   |

Switch to the **Custom Header** tab and click **Create → WebSocket** — DSM inserts the required
`Upgrade` and `Connection` headers automatically.

Click **Save**.

### 4. Add a rule for the backend API

Click **Create** again:

| Field              | Value                                    |
|--------------------|------------------------------------------|
| Description        | `Tour Manager – Backend API`             |
| Source – Protocol  | `HTTPS` (or `HTTP` for LAN-only)         |
| Source – Hostname  | `tours-api.yourdomain.com`               |
| Source – Port      | `443` (or `80`)                          |
| Destination – Protocol | `HTTP`                               |
| Destination – Hostname | `localhost` (or the Docker host IP)  |
| Destination – Port | `8000`                                   |

Add the WebSocket headers on the **Custom Header** tab as above, then click **Save**.

### 5. Update the application environment

Edit your `.env` so the frontend and backend know their public URLs:

```bash
# URL the backend uses when building verification email links etc.
FRONTEND_URL=https://tours.yourdomain.com

# URL the frontend uses to reach the API (set in docker-compose.yml or .env)
VITE_API_BASE_URL=https://tours-api.yourdomain.com
```

Recreate the containers to pick up the new values:

```bash
docker compose up -d --force-recreate
```

### 6. Firewall / port-forwarding

- **LAN access only**: no extra firewall rules needed — just make sure DSM can reach the Docker
  host ports (`3001`, `8000`).
- **External access**: forward port `443` (and/or `80`) on your router to the Synology's LAN IP.
  DSM's built-in Let's Encrypt integration (**Control Panel → Security → Certificate**) can
  issue a free TLS certificate for your domain automatically.

### Alternative: single hostname with path prefix

If you only have one (sub)domain available, create a single reverse proxy rule pointing to the
frontend (`localhost:3001`) and add a second rule with the **same hostname** but with source path
`/api` pointing to the backend (`localhost:8000`). Set `VITE_API_BASE_URL` to
`https://tours.yourdomain.com/api` and make sure the backend receives the correct path — the
path-rewriting is then handled by the proxy.
