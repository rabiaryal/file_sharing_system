# 🚢 Deployment Guide

A complete guide to deploy the PDF Sharing Platform to production.

## 📋 Pre-Deployment Checklist

### Security
- [ ] Set `DEBUG=False`
- [ ] Use strong `SECRET_KEY` (minimum 50 characters, random)
- [ ] Configure SSL/TLS certificate
- [ ] Set `ALLOWED_HOSTS` to production domains only
- [ ] Enable HTTPS only in browser
- [ ] Set secure CORS origins

### Database
- [ ] Create Supabase project with automated backups
- [ ] Enable SSL for database connections
- [ ] Create read-only replica for backups
- [ ] Set up monitoring and alerts
- [ ] Test disaster recovery procedures

### Storage
- [ ] Verify Supabase bucket is **PRIVATE**
- [ ] Set up lifecycle rules to auto-delete old files
- [ ] Configure bucket backups
- [ ] Enable versioning (optional)

### Performance
- [ ] Set up CDN for static assets
- [ ] Configure Redis for caching
- [ ] Set up Celery beat for periodic tasks
- [ ] Configure log aggregation
- [ ] Set up monitoring dashboards

### Infrastructure
- [ ] Use managed database (Supabase recommended)
- [ ] Use managed Redis (or self-hosted with backup)
- [ ] Set up load balancer (if scaling)
- [ ] Configure auto-scaling
- [ ] Set up health checks

---

## 🐳 Docker Deployment

### Option 1: Single Server (Docker Compose)

#### Prerequisites

- Server with Docker & Docker Compose
- Minimum: 2GB RAM, 20GB storage
- Recommended: 4GB RAM, 50GB storage

#### Steps

1. **Clone and configure**

```bash
git clone <repo-url>
cd file_sharing_system

# Copy and configure .env
cp .env.example .env
# Edit .env with production values
```

2. **Update environment**

```env
DEBUG=0
SECRET_KEY=generate-a-50-character-random-string
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
GOOGLE_CLIENT_ID=your_production_client_id
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

3. **Setup SSL**

```bash
# Using Let's Encrypt with Certbot
sudo apt-get install certbot python3-certbot-nginx

sudo certbot certonly --standalone \
  -d yourdomain.com \
  -d www.yourdomain.com
```

4. **Create Nginx config**

```nginx
upstream django {
    server web:8000;
}

upstream frontend {
    server frontend:3000;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    client_max_body_size 100M;
    
    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files
    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
    }
}

# HTTP redirect to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

5. **Start services**

```bash
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec web \
  python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec web \
  python manage.py createsuperuser

# Collect static files
docker-compose -f docker-compose.prod.yml exec web \
  python manage.py collectstatic --noinput
```

---

### Option 2: Kubernetes Deployment

#### Prerequisites

- Kubernetes cluster (EKS, GKE, AKS, or self-hosted)
- kubectl configured
- Helm (optional, but recommended)

#### Architecture

```
┌─────────────────────────────────────────┐
│        Kubernetes Cluster               │
├─────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────────┐ │
│  │  Ingress     │  │  Service         │ │
│  │ (TLS, Load   │  │  (Backend API)   │ │
│  │  Balancer)   │  └──────────────────┘ │
│  └──────────────┘          │            │
│       │                    ▼            │
│       ├──────────────┬──────────────┐  │
│       │              │              │  │
│       ▼              ▼              ▼  │
│   ┌────────┐  ┌──────────┐  ┌────────┐ │
│   │Frontend│  │  Django  │  │ Celery │ │
│   │   Pod  │  │   Pod    │  │  Pod   │ │
│   │(x2)    │  │  (x3)    │  │  (x1)  │ │
│   └────────┘  └──────────┘  └────────┘ │
│                     │                   │
│       ┌─────────────┼──────────────┐   │
│       ▼             ▼              ▼   │
│   ┌──────────┐  ┌──────────┐ ┌─────────┐
│   │ Redis    │  │PostgreSQL│ │Supabase │
│   │  Cache   │  │   Pod    │ │ Storage │
│   └──────────┘  └──────────┘ └─────────┘
│                                         │
└─────────────────────────────────────────┘
```

#### Steps

1. **Create Kubernetes manifests**

```yaml
# deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: django-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: django-backend
  template:
    metadata:
      labels:
        app: django-backend
    spec:
      containers:
      - name: django
        image: your-registry/django-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DEBUG
          value: "0"
        - name: GOOGLE_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: google-client-id
        - name: SUPABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: supabase-password
        # ... more env vars
        livenessProbe:
          httpGet:
            path: /api/health/
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

2. **Create secrets**

```bash
kubectl create secret generic app-secrets \
  --from-literal=google-client-id=YOUR_CLIENT_ID \
  --from-literal=supabase-password=YOUR_PASSWORD \
  --from-literal=secret-key=YOUR_SECRET_KEY
```

3. **Deploy**

```bash
kubectl apply -f deployment.yml
kubectl apply -f service.yml
kubectl apply -f ingress.yml

# Monitor
kubectl logs -f deployment/django-backend
kubectl get pods
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test_db
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: python manage.py test
    
    - name: Lint
      run: flake8 .

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v1
    
    - name: Login to Registry
      uses: docker/login-action@v1
      with:
        username: ${{ secrets.REGISTRY_USERNAME }}
        password: ${{ secrets.REGISTRY_PASSWORD }}
    
    - name: Build and push
      uses: docker/build-push-action@v2
      with:
        context: .
        push: true
        tags: |
          ${{ secrets.REGISTRY }}/django-backend:${{ github.sha }}
          ${{ secrets.REGISTRY }}/django-backend:latest

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to production
      run: |
        # Add your deployment script here
        # e.g., SSH to server and run docker-compose pull && docker-compose up
```

---

## 📊 Monitoring & Logging

### Setup Monitoring

```bash
# Install Prometheus
docker pull prom/prometheus

# Install Grafana
docker pull grafana/grafana

# Setup logging with ELK
docker pull docker.elastic.co/elasticsearch/elasticsearch:8.0.0
docker pull docker.elastic.co/kibana/kibana:8.0.0
docker pull docker.elastic.co/beats/filebeat:8.0.0
```

### Health Checks

```python
# core/urls.py
from django.http import JsonResponse

urlpatterns = [
    # ...
    path('api/health/', lambda r: JsonResponse({'status': 'ok'})),
]
```

---

## 🔐 Production Security Checklist

- [ ] Enable 2FA on cloud accounts
- [ ] Use SSH keys (no passwords)
- [ ] Enable audit logging
- [ ] Set up intrusion detection
- [ ] Regular security updates
- [ ] Backup verification procedures
- [ ] Incident response plan
- [ ] DDoS protection (CloudFlare, AWS Shield)
- [ ] Web Application Firewall (WAF)
- [ ] Regular penetration testing

---

## 🚨 Troubleshooting Production Issues

### High Memory Usage

```bash
# Check container memory
docker stats

# Optimize Celery
CELERYD_PREFETCH_MULTIPLIER=2
CELERYD_MAX_TASKS_PER_CHILD=1000
```

### Database Connection Errors

```bash
# Check connection pool
psql -h pooler.supabase.co -U postgres -d postgres

# View active connections
SELECT count(*) FROM pg_stat_activity;

# Restart pool connections
# (In Supabase: Settings → Database → Connection Pooling → Restart)
```

### File Upload Failures

```bash
# Check Supabase bucket permissions
# Check storage bucket size limits
# Verify Celery worker is running

docker-compose logs celery_worker
```

---

## 📈 Scaling Strategies

### Horizontal Scaling

1. **Add load balancer** - nginx, HAProxy, or cloud LB
2. **Multiple web workers** - Run 3-5 Django instances
3. **Celery scaling** - Add more worker nodes
4. **Database read replicas** - Supabase handles this

### Vertical Scaling

1. **Increase server specs** - More CPU/RAM
2. **Optimize queries** - Database indexing
3. **Cache optimization** - Redis tuning
4. **Connection pooling** - pgBouncer settings

---

## 📝 Rollback Procedures

### Database Rollback

```bash
# Check migration history
python manage.py showmigrations

# Rollback to previous version
python manage.py migrate users 0002  # or any version
```

### Code Rollback

```bash
# If using docker-compose
git revert <commit-hash>
docker-compose up --build
```

---

## 📞 Support

For deployment issues:
1. Check logs: `docker-compose logs <service>`
2. Review Supabase status page
3. Check GitHub Issues
4. Contact support

---

**Successfully deployed! 🎉**
