#!/usr/bin/env bash
# Exit immediately if any command fails
set -o errexit

# Install packages
pip install -r requirements.txt

# Run migrations on your database
python manage.py migrate --noinput

# Collect static asset files
python manage.py collectstatic --noinput
