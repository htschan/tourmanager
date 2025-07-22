# Email Configuration Fix

## Problem

When trying to register a new user, the backend throws a validation error related to email configuration:

```
pydantic_core._pydantic_core.ValidationError: 4 validation errors for ConnectionConfig
MAIL_STARTTLS
  Field required [type=missing, input_value={'MAIL_USERNAME': '...', ...}, input_type=dict]
MAIL_SSL_TLS
  Field required [type=missing, input_value={'MAIL_USERNAME': '...', ...}, input_type=dict]
MAIL_TLS
  Extra inputs are not permitted [type=extra_forbidden, input_value=True, input_type=bool]
MAIL_SSL
  Extra inputs are not permitted [type=extra_forbidden, input_value=False, input_type=bool]
```

## Cause

This error occurs because the project is using newer versions of `fastapi-mail` (>=1.2.0), but the code is still using parameter names from an older version:

- Old parameter names: `MAIL_TLS`, `MAIL_SSL`
- New required parameter names: `MAIL_STARTTLS`, `MAIL_SSL_TLS`

## Solution

### 1. Fix for Development Environment

Run the provided script to fix the issue in the running Docker container:

```bash
cd scripts
./fix_email_config.sh
```

This script:
1. Finds the running backend container
2. Updates the `utils/email.py` file with the correct parameter names
3. Restarts the container to apply the changes

### 2. Fix for CI/CD Pipeline

The CI Dockerfile has been updated to automatically fix the issue during the build process by:

```dockerfile
# Fix email configuration parameters
RUN if [ -f utils/email.py ]; then \
    sed -i 's/MAIL_TLS=True/MAIL_STARTTLS=True/g' utils/email.py && \
    sed -i 's/MAIL_SSL=False/MAIL_SSL_TLS=False/g' utils/email.py; \
    fi
```

### 3. Manual Fix

If needed, you can manually update the `utils/email.py` file by changing:

```python
# From:
return ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True
)

# To:
return ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)
```

## Verification

After applying the fix:
1. Restart the backend container
2. Try to register a new user
3. The registration process should now complete without errors

## Additional Notes

- This fix is also documented in the project README.md under the Troubleshooting section
- For production deployments, consider updating the Docker image with the fixed code
