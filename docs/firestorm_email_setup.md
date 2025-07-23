# Using Firestorm.ch as Your Email Provider

This guide explains how to configure your Tour Manager application to use Firestorm.ch as your email provider for sending verification emails, password resets, and other notifications.

## Prerequisites

- An active hosting account with Firestorm.ch
- Email accounts set up with Firestorm.ch
- Access to your Firestorm.ch control panel

## Step 1: Get Your SMTP Server Details from Firestorm.ch

1. Log in to your Firestorm.ch control panel
2. Navigate to the Email section
3. Look for SMTP settings or Email configuration
4. Note down the following details:
   - SMTP Server address (typically `smtp.firestorm.ch` or `mail.firestorm.ch`)
   - SMTP Port (typically 587 for TLS or 465 for SSL)
   - Your full email address (e.g., `your-email@yourdomain.ch`)
   - Your email password

## Step 2: Configure Your Application

Update your `.env` file with the following settings:

```
# Email server settings for Firestorm.ch
MAIL_SERVER=smtp.firestorm.ch
MAIL_PORT=587
MAIL_USERNAME=your-email@yourdomain.ch
MAIL_PASSWORD=your-password
MAIL_FROM=your-email@yourdomain.ch
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
USE_CREDENTIALS=True
```

## Step 3: Test Your Configuration

Run the provided test script:

```bash
cd /home/hts/pj/komoot
python scripts/test_firestorm_email.py your-test-email@example.com
```

This will attempt to send a test email using your Firestorm.ch configuration.

## Common Issues and Solutions

### Connection Refused

If you see an error like `Connection refused`, check:
- That your SMTP server address is correct
- That the port is not blocked by a firewall
- That your hosting plan includes SMTP access

### Authentication Failed

If you see authentication errors:
- Verify your username and password are correct
- Ensure you're using the full email address as the username
- Check if your Firestorm.ch account requires app passwords

### TLS/SSL Issues

If you encounter TLS/SSL errors:
- Try switching between `MAIL_STARTTLS=True` and `MAIL_SSL_TLS=True`
- If using port 465, set `MAIL_SSL_TLS=True` and `MAIL_STARTTLS=False`
- If using port 587, set `MAIL_STARTTLS=True` and `MAIL_SSL_TLS=False`

## Rate Limits and Best Practices

- Check with Firestorm.ch about any email sending rate limits
- Don't use your personal email for application notifications
- Create a dedicated email like `noreply@yourdomain.ch` for system emails
- Consider implementing email queuing for high-volume scenarios

## Production vs. Development

For development environments, you might want to disable actual email sending:
- Set `EMAIL_DEBUG=True` in your development `.env` file
- This will log email content rather than sending actual emails

For production environments:
- Ensure `EMAIL_DEBUG=False` or remove this variable
- Use a secure password in your `.env` file
- Consider using environment secrets management for better security

## Getting Help

If you continue to have issues with Firestorm.ch as your mail server:
- Contact Firestorm.ch support for specific SMTP configuration help
- Check their documentation for any special requirements
- Verify that your hosting plan includes the email features you need
