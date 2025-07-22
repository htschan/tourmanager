FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create data directory
RUN mkdir -p /app/data

# Copy application code
COPY . .

# Apply the ResponseValidationError fix - Create user bypass module
RUN echo 'from fastapi.responses import JSONResponse' > /app/fixed_users.py && \
    echo 'from fastapi import Depends, HTTPException' >> /app/fixed_users.py && \
    echo 'from sqlalchemy.orm import Session' >> /app/fixed_users.py && \
    echo 'from typing import Dict, Any, List' >> /app/fixed_users.py && \
    echo '' >> /app/fixed_users.py && \
    echo 'def bypass_users(current_user, db, UserModel, UserRole):' >> /app/fixed_users.py && \
    echo '    """Completely bypassed users endpoint"""' >> /app/fixed_users.py && \
    echo '    if not hasattr(current_user, "role") or current_user.role != UserRole.ADMIN:' >> /app/fixed_users.py && \
    echo '        raise HTTPException(status_code=403, detail="Not authorized to view user list")' >> /app/fixed_users.py && \
    echo '' >> /app/fixed_users.py && \
    echo '    users = db.query(UserModel).all()' >> /app/fixed_users.py && \
    echo '' >> /app/fixed_users.py && \
    echo '    result = []' >> /app/fixed_users.py && \
    echo '    for user in users:' >> /app/fixed_users.py && \
    echo '        user_dict = {}' >> /app/fixed_users.py && \
    echo '        # Basic fields' >> /app/fixed_users.py && \
    echo '        for field in ["username", "email"]:' >> /app/fixed_users.py && \
    echo '            if hasattr(user, field):' >> /app/fixed_users.py && \
    echo '                user_dict[field] = getattr(user, field) or ""' >> /app/fixed_users.py && \
    echo '            else:' >> /app/fixed_users.py && \
    echo '                user_dict[field] = ""' >> /app/fixed_users.py && \
    echo '' >> /app/fixed_users.py && \
    echo '        # Handle role' >> /app/fixed_users.py && \
    echo '        if hasattr(user, "role"):' >> /app/fixed_users.py && \
    echo '            if hasattr(user.role, "name"):' >> /app/fixed_users.py && \
    echo '                user_dict["role"] = user.role.name' >> /app/fixed_users.py && \
    echo '            else:' >> /app/fixed_users.py && \
    echo '                role_str = str(user.role)' >> /app/fixed_users.py && \
    echo '                if "ADMIN" in role_str.upper():' >> /app/fixed_users.py && \
    echo '                    user_dict["role"] = "ADMIN"' >> /app/fixed_users.py && \
    echo '                else:' >> /app/fixed_users.py && \
    echo '                    user_dict["role"] = "USER"' >> /app/fixed_users.py && \
    echo '        else:' >> /app/fixed_users.py && \
    echo '            user_dict["role"] = "USER"' >> /app/fixed_users.py && \
    echo '' >> /app/fixed_users.py && \
    echo '        # Handle status' >> /app/fixed_users.py && \
    echo '        if hasattr(user, "status"):' >> /app/fixed_users.py && \
    echo '            if hasattr(user.status, "name"):' >> /app/fixed_users.py && \
    echo '                user_dict["status"] = user.status.name' >> /app/fixed_users.py && \
    echo '            else:' >> /app/fixed_users.py && \
    echo '                status_str = str(user.status)' >> /app/fixed_users.py && \
    echo '                if "PENDING" in status_str.upper():' >> /app/fixed_users.py && \
    echo '                    user_dict["status"] = "PENDING"' >> /app/fixed_users.py && \
    echo '                elif "DISABLED" in status_str.upper():' >> /app/fixed_users.py && \
    echo '                    user_dict["status"] = "DISABLED"' >> /app/fixed_users.py && \
    echo '                else:' >> /app/fixed_users.py && \
    echo '                    user_dict["status"] = "ACTIVE"' >> /app/fixed_users.py && \
    echo '        else:' >> /app/fixed_users.py && \
    echo '            user_dict["status"] = "ACTIVE"' >> /app/fixed_users.py && \
    echo '' >> /app/fixed_users.py && \
    echo '        # Handle dates' >> /app/fixed_users.py && \
    echo '        for date_field in ["created_at", "last_login"]:' >> /app/fixed_users.py && \
    echo '            user_dict[date_field] = None' >> /app/fixed_users.py && \
    echo '            if hasattr(user, date_field) and getattr(user, date_field):' >> /app/fixed_users.py && \
    echo '                try:' >> /app/fixed_users.py && \
    echo '                    user_dict[date_field] = getattr(user, date_field).isoformat()' >> /app/fixed_users.py && \
    echo '                except:' >> /app/fixed_users.py && \
    echo '                    user_dict[date_field] = str(getattr(user, date_field))' >> /app/fixed_users.py && \
    echo '' >> /app/fixed_users.py && \
    echo '        result.append(user_dict)' >> /app/fixed_users.py && \
    echo '' >> /app/fixed_users.py && \
    echo '    return JSONResponse(content=result)' >> /app/fixed_users.py

# Add fix to main.py - replace the users endpoint with our fixed version
RUN cp main.py main.py.original && \
    cat main.py | sed -E 's/(@app\.get\("\/api\/users".*?(response_model=[^,\)]+)?)/@app.get("\/api\/users")/g' > main.py.temp && \
    mv main.py.temp main.py && \
    cat main.py | sed -E 's/(def list_users[^:]+:.*?)(\n[[:space:]]+"""List all users[^"]+""".*?)(\n[[:space:]]+if.*?)$/\1\2\n    from fixed_users import bypass_users\n    return bypass_users(current_user, db, UserModel, UserRole)/g' > main.py.temp && \
    mv main.py.temp main.py

# Fix email configuration parameters
RUN if [ -f utils/email.py ]; then \
    sed -i 's/MAIL_TLS=True/MAIL_STARTTLS=True/g' utils/email.py && \
    sed -i 's/MAIL_SSL=False/MAIL_SSL_TLS=False/g' utils/email.py; \
    fi

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug", "--no-access-log"]
