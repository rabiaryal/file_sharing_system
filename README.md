# 📄 PDF Sharing Platform

A modern, production-ready file-sharing platform built with **React**, **Django**, **PostgreSQL**, and **Supabase**. Share PDFs securely with encrypted links, QR codes, and download limits.

## 🌟 Key Features

### 🔐 Security & Authentication
- **Google OAuth 2.0 Login** - Secure authentication with Google accounts
- **JWT Tokens** - Stateless authentication with refresh rotation
- **Private Supabase Bucket** - All files encrypted at rest
- **Presigned URLs** - 60-second time-limited download links
- **Rate Limiting** - Protection against abuse (5 requests/min per link)

### 📤 File Upload & Sharing
- **Drag-and-Drop Upload** - Intuitive file upload interface
- **Presigned Upload URLs** - Direct upload to Supabase Storage (no backend overhead)
- **Shareable Links** - Generate unique, expiring share links
- **QR Codes** - One-click QR generation for mobile sharing
- **Social Sharing** - Built-in Twitter, WhatsApp, and Email sharing

### 📊 Advanced Features
- **Download Limits** - Set max downloads per link (1-1000)
- **Link Expiration** - Configurable expiry times (1 hour to 7 days)
- **Async Processing** - Celery tasks for file compression
- **Storage Quota** - Per-user 1GB storage limit
- **API Documentation** - OpenAPI/Swagger UI at `/api/docs/`

## 🏗️ Architecture

### Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Frontend | React + TypeScript | 18.2 |
| Build Tool | Vite | 5.0 |
| Styling | Tailwind CSS | 3.4 |
| Backend | Django | 5.2 |
| Database | PostgreSQL | 16 (via Supabase) |
| Queue | Celery + Redis | 5.6 + 7 |
| Storage | Supabase Storage | - |
| Auth | JWT + Google OAuth | - |

### System Diagram

```
┌─────────────────────────────────────────┐
│      React Frontend (Port 3000)         │
│  • Google OAuth Login                   │
│  • Drag-drop File Upload                │
│  • QR Code Generation                   │
│  • Real-time Share Management           │
└────────────────┬────────────────────────┘
                 │ HTTPS/REST API
                 ▼
┌─────────────────────────────────────────┐
│    Django REST Backend (Port 8000)      │
│  • JWT Authentication                   │
│  • Google OAuth Verification            │
│  • File Processing Orchestration        │
│  • Download Gateway (60s signed URLs)   │
└────────┬────────┬────────┬──────────────┘
         │        │        │
         ▼        ▼        ▼
    ┌────────┐ ┌──────┐ ┌──────────────┐
    │ Redis  │ │  DB  │ │ Supabase     │
    │ 6379   │ │ 5432 │ │ Storage      │
    └────────┘ └──────┘ └──────────────┘
         │
         ▼
   ┌──────────────────┐
   │ Celery Worker    │
   │ • PDF Compress   │
   │ • Cleanup Tasks  │
   └──────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** - For containerized deployment
- **Google Cloud Account** - For OAuth 2.0 credentials
- **Supabase Account** - For PostgreSQL and Storage
- **Node.js 16+** - For local frontend development (optional)

### 1️⃣ Get Google OAuth Credentials

1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable "Google+ API"
4. Create OAuth 2.0 credentials (Web application)
5. Add authorized origins: `http://localhost:3000`, `http://localhost:8000`
6. Copy your **Client ID**

### 2️⃣ Configure Environment

**Backend (.env)**:
```env
GOOGLE_CLIENT_ID=your_google_client_id_here
SUPABASE_HOST=your-project.supabase.co
SUPABASE_USER=postgres.xxxxx
SUPABASE_PASSWORD=your_password
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key
```

**Frontend (frontend/.env)**:
```env
VITE_GOOGLE_CLIENT_ID=your_google_client_id_here
VITE_API_URL=http://localhost:8000
```

### 3️⃣ Deploy with Docker

```bash
# Start all services
docker-compose up --build

# Run migrations (if needed)
docker-compose exec web python manage.py migrate
```

### 4️⃣ Access the Platform

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/
- **API Docs**: http://localhost:8000/api/docs/
- **Admin**: http://localhost:8000/admin/

## 📚 Documentation

- **[Complete Setup Guide](./SETUP.md)** - Detailed installation and configuration
- **[Frontend README](./frontend/README.md)** - React app documentation
- **[API Reference](#api-reference)** - REST API endpoints
- **[Troubleshooting](#troubleshooting)** - Common issues and solutions

## 🔌 API Reference

### Authentication Endpoints

```http
# Google OAuth Login
POST /api/auth/google/
Content-Type: application/json

{
  "token": "google_id_token"
}

# Response
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John"
  }
}
```

### File Upload Endpoints

```http
# 1. Request upload intent
POST /api/files/upload-intent/
Authorization: Bearer {ACCESS_TOKEN}
Content-Type: application/json

{
  "filename": "document.pdf",
  "size": 1024000
}

# Response
{
  "upload_url": "https://supabase.co/...",
  "storage_path": "raw/1/1234567890_document.pdf"
}

# 2. Upload file (to presigned URL)
PUT {upload_url}
Content-Type: application/pdf

[Binary PDF content]

# 3. Process file
POST /api/files/process/
Authorization: Bearer {ACCESS_TOKEN}
Content-Type: application/json

{
  "storage_path": "raw/1/1234567890_document.pdf",
  "original_name": "document.pdf",
  "original_size": 1024000,
  "expires_in_seconds": 3600,
  "max_downloads": 10
}

# Response
{
  "token": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
  "share_url": "/share/a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6/",
  "expires_at": "2024-01-15T14:30:00Z"
}
```

### Download Endpoints

```http
# Public download (with rate limiting)
GET /share/{token}/

# Response: Redirect to 60-second signed URL
HTTP/1.1 302 Found
Location: https://supabase.co/...?expires_in=60

# Access to expired/invalid links
HTTP/1.1 404 Not Found
Content-Type: text/html

<!-- Expired link error page -->
```

### User Endpoints

```http
# Get current user
GET /api/auth/me/
Authorization: Bearer {ACCESS_TOKEN}

# Response
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe"
}

# Logout
POST /api/auth/logout/
Authorization: Bearer {ACCESS_TOKEN}
```

## 🛠️ Development

### Backend Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver

# Start Celery worker (in another terminal)
celery -A core worker --loglevel=info

# Run tests
python manage.py test
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test users
python manage.py test files

# Run with coverage
coverage run --source='.' manage.py test
coverage report --include=users/*,files/*
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

## 📁 Project Structure

```
file_sharing_system/
├── frontend/                    # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── FileUpload.tsx
│   │   │   └── ShareLinkModal.tsx
│   │   ├── api.ts
│   │   ├── AuthContext.tsx
│   │   └── App.tsx
│   ├── package.json
│   ├── Dockerfile
│   └── .env
│
├── core/                        # Django config
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
│
├── users/                       # Auth app
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   └── middleware.py
│
├── files/                       # File sharing app
│   ├── models.py
│   ├── views.py
│   ├── services.py
│   ├── tasks.py
│   ├── serializers.py
│   └── urls.py
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── manage.py
├── .env
├── .env.example
├── SETUP.md
└── README.md
```

## 🔒 Security Considerations

### Implemented Protections

✅ **Private Supabase Bucket** - Only accessible via backend-generated signed URLs  
✅ **60-Second Signed URLs** - Download links auto-expire, preventing link sharing  
✅ **Rate Limiting** - 5 requests/minute per public link  
✅ **Download Limits** - Each link has configurable max downloads  
✅ **JWT Authentication** - Stateless token-based auth  
✅ **CORS Protection** - Origin-based access control  
✅ **Input Validation** - All user inputs validated and sanitized  
✅ **HTTPS Ready** - Supports SSL/TLS in production  

### Production Checklist

- [ ] Set `DEBUG=0` in production
- [ ] Use strong `SECRET_KEY`
- [ ] Enable HTTPS/SSL
- [ ] Configure `ALLOWED_HOSTS` properly
- [ ] Set up proper database backups
- [ ] Enable Redis persistence
- [ ] Configure file upload size limits
- [ ] Set up log aggregation
- [ ] Enable rate limiting
- [ ] Regular security audits

## 🐛 Troubleshooting

### Issue: Port Already in Use

```bash
# macOS/Linux
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Issue: Database Connection Failed

```bash
# Check Supabase credentials
docker-compose exec web python manage.py dbshell

# Verify pooler connection
psql "postgresql://user:password@host:port/database"

# Run migrations
docker-compose exec web python manage.py migrate
```

### Issue: Google OAuth Not Working

1. Verify Client ID in `.env` matches Google Cloud Console
2. Check redirect URIs include `http://localhost:3000`
3. Verify CORS is properly configured
4. Check browser console for error messages

### Issue: File Upload Fails

1. Verify Supabase credentials are correct
2. Check bucket exists and is **PRIVATE**
3. Verify service role key has storage permissions
4. Check Celery worker is running
5. View logs: `docker-compose logs celery_worker`

## 📊 Database Schema

### Users Table

```sql
users_customuser:
  - id (BigAutoField, PK)
  - email (EmailField, UNIQUE)
  - password (CharField, hashed)
  - first_name, last_name (CharField)
  - phone (CharField, nullable)
  - profile_picture (ImageField, nullable)
  - is_email_verified (BooleanField, default=False)
  - created_at, updated_at (DateTimeField)
```

### Files Table

```sql
files_compressedpdf:
  - id (BigAutoField, PK)
  - user_id (ForeignKey→CustomUser)
  - original_name (CharField)
  - original_size (BigIntegerField)
  - compressed_size (BigIntegerField, nullable)
  - storage_path (CharField)
  - status (CharField: PROCESSING/COMPLETED/FAILED)
  - created_at (DateTimeField)

files_sharelink:
  - id (BigAutoField, PK)
  - token (UUIDField, UNIQUE)
  - pdf_id (ForeignKey→CompressedPDF)
  - expires_at (DateTimeField)
  - max_downloads (IntegerField, default=10)
  - current_downloads (IntegerField, default=0)
  - created_at (DateTimeField)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Django REST Framework](https://www.django-rest-framework.org/)
- [React](https://react.dev/)
- [Supabase](https://supabase.com/)
- [Google OAuth](https://developers.google.com/identity)
- [Tailwind CSS](https://tailwindcss.com/)

## 📞 Support

For issues and questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review [Complete Setup Guide](./SETUP.md)
3. Check [GitHub Issues](https://github.com/yourusername/pdf-sharing/issues)
4. Create a new issue with detailed information

---

**Made with ❤️ for secure file sharing**

[⬆ Back to top](#-pdf-sharing-platform)
