# Email Configuration Guide

## Email Configuration Requirements

The komoot application uses FastMail for sending verification emails and password reset notifications. This guide explains how to configure the email settings.

## Required Environment Variables

The application expects the following environment variables to be set:

```
EMAIL_HOST=smtp.fastmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your_username
EMAIL_PASSWORD=your_app_password
EMAIL_FROM=noreply@yourdomain.com
```

## FastMail Configuration

1. Create a FastMail account if you don't have one already
2. Generate an App Password (don't use your main FastMail password)
   - Log into FastMail
   - Go to Settings > Password & Security
   - Under "App Passwords", create a new password for this application
   - Use this password for the EMAIL_PASSWORD environment variable

## Development Setup

For local development, create a `.env` file in the `backend` directory:

```
EMAIL_HOST=smtp.fastmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your_username
EMAIL_PASSWORD=your_app_password
EMAIL_FROM=noreply@yourdomain.com
```

## Production Setup

For Docker Swarm production deployment:

1. In Portainer, navigate to your stack
2. Add the environment variables under "Environment variables"
3. Or use secrets for sensitive information like passwords

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
3. Ensure your FastMail account allows sending from the EMAIL_FROM address
4. Check if the app password is still valid
5. Verify that port 587 is not blocked by any firewall

## Rate Limits

FastMail has rate limits on sending emails. For high-volume sending, consider:

1. Monitoring your email sending rates
2. Implementing a queue system for email delivery
3. Contacting FastMail support for rate limit increases if needed
