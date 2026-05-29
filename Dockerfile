FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=core.settings

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . /app

# Create directories for static and media files
RUN mkdir -p /app/staticfiles /app/media

# Collect static files safely (ignores errors if env vars are missing during compilation)
RUN python manage.py collectstatic --noinput --clear || true

# NOTE: REMOVED "EXPOSE 8000" because Render assigns its own internal ports dynamically.

# Health check dynamically looks at Render's internal system port variable
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run gunicorn (Changed to shell script form to parse the dynamic $PORT variable)
# Also reduced workers to 2 to protect Render's 512MB RAM free limit
CMD gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --worker-class sync --timeout 120 --access-logfile - --error-logfile -