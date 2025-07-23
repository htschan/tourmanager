#!/bin/bash

# Script to run email test with environment variables from a specific .env file
# This ensures Docker properly receives all environment variables

# Set default values
ENV_FILE=".env"
TEST_EMAIL=""

# Display help
show_help() {
  echo "Usage: $0 [OPTIONS] [RECIPIENT_EMAIL]"
  echo ""
  echo "Options:"
  echo "  -e, --env FILE      Specify the .env file to use (default: .env)"
  echo "  -h, --help          Show this help message"
  echo ""
  echo "Examples:"
  echo "  $0 test@example.com         # Use default .env file"
  echo "  $0 -e backend/.env test@example.com  # Use backend/.env file"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -e|--env)
      ENV_FILE="$2"
      shift 2
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      TEST_EMAIL="$1"
      shift
      ;;
  esac
done

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
  echo "Error: Environment file '$ENV_FILE' not found!"
  echo "Please create this file or specify a different one with -e option."
  exit 1
fi

echo "=== Email Test Configuration ==="
echo "Using environment file: $ENV_FILE"
echo "Test recipient: $TEST_EMAIL"
echo ""

# Load environment variables from the .env file
set -a  # automatically export all variables
source "$ENV_FILE"
set +a

# Display settings (obscure password)
echo "Email settings from $ENV_FILE:"
echo "  MAIL_SERVER: $MAIL_SERVER"
echo "  MAIL_PORT: $MAIL_PORT"
echo "  MAIL_USERNAME: $MAIL_USERNAME"
echo "  MAIL_PASSWORD: ********"
echo "  MAIL_FROM: $MAIL_FROM"
echo "  MAIL_STARTTLS: $MAIL_STARTTLS"
echo "  MAIL_SSL_TLS: $MAIL_SSL_TLS"
echo "  USE_CREDENTIALS: $USE_CREDENTIALS"
echo ""

# Prepare the docker-compose exec command with all environment variables
CMD="docker compose exec"
CMD="$CMD -e MAIL_SERVER=$MAIL_SERVER"
CMD="$CMD -e MAIL_PORT=$MAIL_PORT" 
CMD="$CMD -e MAIL_USERNAME=$MAIL_USERNAME"
CMD="$CMD -e MAIL_PASSWORD=$MAIL_PASSWORD"
CMD="$CMD -e MAIL_FROM=$MAIL_FROM"
CMD="$CMD -e MAIL_STARTTLS=$MAIL_STARTTLS"
CMD="$CMD -e MAIL_SSL_TLS=$MAIL_SSL_TLS"
CMD="$CMD -e USE_CREDENTIALS=$USE_CREDENTIALS"
CMD="$CMD -e FRONTEND_URL=${FRONTEND_URL:-http://localhost:3001}"
CMD="$CMD backend python /app/scripts/test_email.py $TEST_EMAIL"

# Run the command
echo "Running email test..."
echo ""
eval $CMD
