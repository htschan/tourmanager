# User API Fixes

This directory contains scripts to fix issues with the user management API.

## Problem 1: User Role Enum Case Sensitivity

The backend encounters an error when fetching users:
```
LookupError: 'user' is not among the defined enum values. Enum name: userrole. Possible values: ADMIN, USER
```

This happens because there's a case mismatch between the enum values defined in the code (`ADMIN`, `USER`) and the values stored in the database (`admin`, `user`).

### Fix Options for Problem 1

#### Option 1: Direct Database Fix

The quickest fix is to directly update the database values:

```bash
# Using the shell script
docker-compose exec backend /scripts/fix_user_roles.sh

# Or using the Python script (more robust)
docker-compose exec backend python /scripts/fix_user_roles.py
```

#### Option 2: Apply Code Patch

A more comprehensive fix that addresses both the database and code:

```bash
docker-compose exec backend /scripts/apply_enum_fix.sh
```

This script:
1. Creates a patched version of the code with case-insensitive enum handling
2. Updates the database values to match the expected format
3. Restarts the application to apply the changes

## Problem 2: Response Validation Error

After fixing the enum issue, you might encounter a response validation error:
```
fastapi.exceptions.ResponseValidationError
```

This happens because the serialized user data doesn't match the expected UserResponse model schema.

### Fix Options for Problem 2

#### Option 1: Fix Response Serialization

Apply a fix that modifies the list_users endpoint to handle response serialization correctly:

```bash
# Using the shell script (more comprehensive)
docker-compose exec backend /scripts/fix_response_validation.sh

# Or using the Python script (more targeted)
docker-compose exec backend python /scripts/fix_response_validation.py
```

## Rebuilding for Permanent Fix

For a permanent fix, rebuild the container after the patches are applied:

```bash
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d
```

## Verification

After applying any of these fixes, you can verify the solution by:

1. Opening the admin dashboard in the frontend
2. Checking if users are displayed correctly
3. Looking at the logs for any errors:
   ```bash
   docker-compose logs backend | grep ERROR
   ```

## Troubleshooting

If issues persist:

1. Check the database values directly:
   ```bash
   docker-compose exec backend sqlite3 /app/data/tourmanager.db "SELECT username, role FROM users;"
   ```

2. Verify the enum definition:
   ```bash
   docker-compose exec backend cat /app/models/users.py | grep -A5 "UserRole"
   ```

3. Apply the fixes again and restart the container:
   ```bash
   docker-compose restart backend
   ```
