# Email Verification and User Approval Documentation

## Overview

This document explains the email verification and user approval flow in the komoot application.

## User Registration Flow

1. **User Registration**: When a new user registers, they are created with:
   - `email_verified = False` (email not verified)
   - `status = UserStatus.PENDING` (awaiting admin approval)
   - A unique verification token is generated for the email

2. **Email Verification**: User receives an email with a verification link
   - User clicks on the link to verify their email address
   - System marks their account as `email_verified = True`
   - User status remains `PENDING` until admin approval

3. **Admin Approval**: An administrator must approve the new user
   - Admin can view pending users at `/api/admin/pending-users`
   - Admin approves user at `/api/admin/approve-user/{username}`
   - System sets user status to `ACTIVE`
   - User receives email notification about account approval

4. **User Login**: User can now log in to the application
   - System validates that:
     - Email is verified
     - Status is ACTIVE
   - Token is issued for authenticated user

## Special Case: Admin User

The predefined admin user (`admin` by default) is exempt from email verification:

- Created with `email_verified = True` automatically
- Created with `status = UserStatus.ACTIVE` automatically
- Can log in immediately without verification or approval
- Admin username is configurable via `ADMIN_USERNAME` environment variable

## Environment Variables

- `ADMIN_USERNAME`: Default is "admin"
- `ADMIN_PASSWORD`: Default is "admin123" (change this in production)
- `ADMIN_EMAIL`: Default is "admin@example.com"

## Security Considerations

- Default admin credentials should be changed immediately in production
- Email verification prevents unauthorized users from registering with someone else's email
- Admin approval provides an additional layer of security for controlling access
- Admin user exception allows for initial setup without email verification infrastructure
