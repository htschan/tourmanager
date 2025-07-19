# Using Email Configuration with Portainer

This document describes how to set up the Tour Manager application with email functionality in a Portainer environment.

## Overview

The Tour Manager application uses email functionality for:
- User email verification
- Password reset functionality

Instead of hardcoding these values, we use environment variables in the stack configuration.

## Setting Up in Portainer

### Step 1: Import the Stack Configuration

1. Log in to your Portainer interface
2. Navigate to "Stacks" in the left sidebar
3. Click "Add stack"
4. Choose "Upload" from the "Build method" options
5. Upload the `portainer-stack.yml` file
6. Name your stack (e.g., "tour-manager")

### Step 2: Configure Environment Variables

In the Portainer interface, under "Environment variables", configure these values:

**Required Variables:**

- `MAIL_USERNAME`: Your email service username (e.g., `your-email@gmail.com`)
- `MAIL_PASSWORD`: Your email service password or app password
- `MAIL_FROM`: The email address to send from (typically the same as username)
- `SCRIPT_VOLUME_PATH`: Absolute path to your scripts directory
- `DATA_VOLUME_PATH`: Absolute path to your data directory

**Optional Variables:**

- `MAIL_SERVER`: SMTP server address (default: `smtp.gmail.com`)
- `MAIL_PORT`: SMTP port (default: `587`)
- `FRONTEND_URL`: URL where your frontend is accessible (e.g., `https://yourdomain.com`)
- `JWT_SECRET_KEY`: Secret key for JWT token encryption
- `API_BASE_URL`: URL where your API is accessible (for frontend)
- `BACKEND_IMAGE`: Custom backend image path if not using default
- `FRONTEND_IMAGE`: Custom frontend image path if not using default

### Step 3: Deploy the Stack

After configuring the variables, click "Deploy the stack" to launch the application.

## Gmail Configuration

If you're using Gmail:

1. Use an app password instead of your regular password
2. To create an app password:
   - Go to your Google Account: https://myaccount.google.com/
   - Go to "Security" > "2-Step Verification"
   - Scroll down to "App passwords" and create a new one

## Troubleshooting

If emails aren't being sent:

1. Check the backend logs in Portainer
2. Verify SMTP settings (especially if not using Gmail)
3. For Gmail users, ensure the app password is correct
4. Check that your email provider allows SMTP access

## Testing Email Functionality

Once configured, you can test the email functionality by:

1. Registering a new user
2. Clicking "Forgot Password" on the login screen
