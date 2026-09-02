#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting QRNation Entrypoint..."

# Apply database migrations
echo "Applying database migrations..."
flask db upgrade

# Start the application
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 4 --threads 2 --timeout 60 wsgi:app
