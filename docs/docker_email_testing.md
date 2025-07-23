# Instructions to Test Email Configuration with Docker

This document explains how to test your email configuration with Firestorm.ch using Docker.

## Option 1: Using Docker Compose Environment Variables

1. Create a `.env` file in your project root:

```
# Email configuration
MAIL_SERVER=smtp.firestorm.ch
MAIL_PORT=587
MAIL_USERNAME=your-actual-email@yourdomain.ch
MAIL_PASSWORD=your-actual-password
MAIL_FROM=your-actual-email@yourdomain.ch
```

2. Start your containers with Docker Compose:

```bash
docker compose up -d
```

3. Run the test script inside the backend container:

```bash
docker compose exec backend python /app/scripts/test_email.py your-test-email@example.com
```

## Option 2: Using Direct Environment Variables

If you prefer not to modify your `.env` file, you can pass the variables directly:

```bash
docker compose exec -e MAIL_SERVER=smtp.firestorm.ch \
                   -e MAIL_PORT=587 \
                   -e MAIL_USERNAME=your-actual-email@yourdomain.ch \
                   -e MAIL_PASSWORD=your-actual-password \
                   -e MAIL_FROM=your-actual-email@yourdomain.ch \
                   backend python /app/scripts/test_email.py your-test-email@example.com
```

## Option 3: Installing Required Packages in Container

If you encounter import errors, you may need to install the required packages:

```bash
# Enter the container
docker compose exec backend bash

# Install required packages
pip install python-dotenv fastapi-mail

# Run the test script
python /app/scripts/test_email.py your-test-email@example.com

# Exit container
exit
```

## Common Issues

### 1. Import Errors

If you see errors like `ModuleNotFoundError: No module named 'fastapi_mail'`, you need to install the missing packages:

```bash
docker compose exec backend pip install fastapi-mail python-dotenv
```

### 2. Connection Issues

If your email fails to send due to connection issues:

- Verify your MAIL_SERVER value is correct
- Try different port combinations:
  - Port 587 with MAIL_STARTTLS=True and MAIL_SSL_TLS=False
  - Port 465 with MAIL_STARTTLS=False and MAIL_SSL_TLS=True

### 3. Authentication Issues

For authentication failures:

- Double-check username and password
- Ensure you're using the full email address as the username
- Check if your Firestorm.ch account requires app-specific passwords
