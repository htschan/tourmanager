# Email Configuration Guide

## Email Configuration Requirements

The komoot application uses SMTP for sending verification emails and password reset notifications. This guide explains how to configure the email settings.

## Required Environment Variables

The application expects the following environment variables to be set:

```
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USERNAME=your_username
EMAIL_PASSWORD=your_password
EMAIL_FROM=noreply@yourdomain.com
```

## Email Provider Configuration

1. Choose an email service provider that supports SMTP
2. Configure your account for application access
   - Many providers require generating an app-specific password
   - Follow your provider's security guidelines
   - Use the generated password for the EMAIL_PASSWORD environment variable

## Development Setup

For local development, create a `.env` file in the `backend` directory:

```
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USERNAME=your_username
EMAIL_PASSWORD=your_password
EMAIL_FROM=noreply@yourdomain.com
```

## Production Setup

For production deployment:

1. In your container orchestration platform (Docker Swarm, Kubernetes, etc.)
2. Add the environment variables to your service configuration
3. For sensitive information like passwords, use secrets management
4. Ensure the configuration is consistent across all service replicas

## Testing Email Configuration

You can test the email configuration using the script:

```python
from email_utils import send_email

# Test email sending
send_email(
    recipient_email="test@example.com",
    subject="Test Email",
    body="This is a test email from the komoot app."
)
```

## Troubleshooting

If emails are not being sent:

1. Check the application logs for SMTP errors
2. Verify that the environment variables are correctly set
3. Ensure your email provider allows sending from the EMAIL_FROM address
4. Check if your password or app-specific password is still valid
5. Verify that the specified port is not blocked by any firewall

## Rate Limits

Most email providers have rate limits on sending emails. For high-volume sending, consider:

1. Monitoring your email sending rates
2. Implementing a queue system for email delivery
3. Checking with your provider about rate limits for your account type
4. Using a dedicated transactional email service for higher volumes
