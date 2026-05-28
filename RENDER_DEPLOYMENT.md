# Render Deployment Guide

## Files Created for Render Deployment

1. **build.sh** - Build script for Render
2. **requirements.txt** - Python dependencies
3. **render.yaml** - Render infrastructure configuration

## Step 1: Push to GitHub

```bash
git add build.sh requirements.txt render.yaml
git commit -m "Add Render deployment configuration"
git push origin main
```

## Step 2: Connect to Render

1. Go to [render.com](https://render.com)
2. Sign in with GitHub account
3. Click "New +" → "Blueprint"
4. Select your repository
5. Name your service
6. Click "Deploy"

Render will automatically:
- Read `render.yaml` configuration
- Create PostgreSQL database
- Create Redis cache
- Install dependencies from `requirements.txt`
- Run `build.sh` script (migrations, static files)
- Start Gunicorn server

## Step 3: Configure Environment Variables

After deployment, go to your service settings and update:

```
SECRET_KEY=your_generated_secret_key
DEBUG=false
ALLOWED_HOSTS=your-service.onrender.com,yourdomain.com
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
GOOGLE_CLIENT_ID=your_google_client_id
```

## Step 4: Update Frontend Environment

In your Vercel frontend settings, set:

```
VITE_API_URL=https://your-service.onrender.com
VITE_GOOGLE_CLIENT_ID=your_google_client_id
```

## Key Packages Included

- **Django 5.1.3** - Web framework
- **Gunicorn 22.0.0** - WSGI server
- **psycopg2-binary 2.9.9** - PostgreSQL adapter
- **djangorestframework 3.14.0** - REST API
- **Celery 5.3.4** - Background tasks
- **Redis 5.0.1** - Cache & message broker

## Troubleshooting

### Check Logs
In Render dashboard → Logs → View build logs

### Common Issues
- `ModuleNotFoundError`: Check requirements.txt
- `Database connection error`: Verify DATABASE_URL env var
- `Static files not loading`: build.sh collects them automatically

## Database

PostgreSQL 16 database is automatically created and accessible via `DATABASE_URL` environment variable.

Your Django settings should use:
```python
import dj_database_url
DATABASES = {
    'default': dj_database_url.config()
}
```

## Monitoring

- View logs: Render Dashboard → Logs
- Check metrics: Dashboard → Metrics
- Monitor PostgreSQL: Dashboard → Data Store

---

Your backend will be live at: `https://your-service.onrender.com`
