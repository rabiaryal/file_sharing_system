# PDF Sharing Platform - Complete Setup Guide

A complete, production-ready file-sharing platform with React frontend, Django backend, Google OAuth, QR code generation, and Supabase integration.

## 🎯 Features

### Backend (Django)
- ✅ Email-only authentication system
- ✅ Google OAuth 2.0 integration
- ✅ JWT token-based authentication with refresh rotation
- ✅ PDF file upload with presigned URLs (Supabase Storage)
- ✅ Async PDF compression with Celery
- ✅ Private shareable links with expiration and download limits
- ✅ Rate limiting for public share links
- ✅ OpenAPI/Swagger documentation
- ✅ Redis caching and Celery message queue
- ✅ PostgreSQL via Supabase

### Frontend (React)
- ✅ Modern React 18 with TypeScript
- ✅ Google OAuth login with @react-oauth/google
- ✅ Drag-and-drop PDF file upload
- ✅ Presigned URL upload directly to Supabase
- ✅ Real-time file processing status
- ✅ QR code generation for share links
- ✅ Social media sharing (Twitter, WhatsApp, Email)
- ✅ Tailwind CSS styling
- ✅ Responsive design

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 16+ (for local development)
- Google OAuth 2.0 credentials
- Supabase account with PostgreSQL database

### Step 1: Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project: "PDF Sharing Platform"
3. Enable the "Google+ API"
4. Navigate to "Credentials" → Create OAuth 2.0 credentials (Web application)
5. Add authorized origins:
   - `http://localhost:3000`
   - `http://localhost:8000`
  - `https://share-file.rabi-aryal.com.np`  
    Use your deployed frontend origin here. For the popup-based `@react-oauth/google` flow, this exact frontend origin must be listed in Authorized JavaScript origins. If you deploy to Vercel preview URLs, those preview origins must also be added or the login will fail with origin mismatch.
6. Add authorized redirect URIs:
   - `http://localhost:3000`
   - `http://localhost:8000/api/auth/google/`
  - `https://share-file.rabi-aryal.com.np`
7. Copy your **Client ID** (looks like: `xxxxx.apps.googleusercontent.com`)

### Step 2: Configure Environment Variables

Update `.env` file:

```env
# Backend
GOOGLE_CLIENT_ID=your_google_client_id_here
SUPABASE_HOST=your-project.supabase.co
SUPABASE_PORT=5432
SUPABASE_DATABASE=postgres
SUPABASE_USER=postgres.xxxxx
SUPABASE_PASSWORD=your_supabase_password
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key
SUPABASE_BUCKET=pdfs
```

Update `frontend/.env` file:

```env
VITE_GOOGLE_CLIENT_ID=your_google_client_id_here
VITE_API_URL=http://localhost:8000
```

For the Vercel production deployment, set `VITE_API_URL` to your Render backend domain, such as `https://file-sharing-api-latest-r939.onrender.com`, then trigger a new frontend deployment.

### Step 3: Start the Application

```bash
# Using Docker Compose (Recommended)
docker-compose up --build

# Or manually:
# Terminal 1 - Backend
python manage.py migrate
python manage.py runserver

# Terminal 2 - Frontend
cd frontend && npm install && npm run dev

# Terminal 3 - Celery Worker
celery -A core worker --loglevel=info
```

### Step 4: Access the Platform

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/
- **API Documentation**: http://localhost:8000/api/docs/
- **Admin Panel**: http://localhost:8000/admin/

## 📋 System Architecture

```
┌─────────────────────────────────────────────┐
│         React Frontend (Port 3000)          │
│  ├─ Google OAuth Login                      │
│  ├─ File Upload with Drag & Drop            │
│  ├─ QR Code Generation                      │
│  └─ Share Link Management                   │
└────────────────┬────────────────────────────┘
                 │ HTTP/REST API
                 ↓
┌─────────────────────────────────────────────┐
│       Django REST Backend (Port 8000)       │
│  ├─ JWT Authentication                      │
│  ├─ Google OAuth Validation                 │
│  ├─ File Processing Orchestration           │
│  └─ Share Link Management                   │
└────────────────┬────────────────────────────┘
        ┌────────┼────────┐
        ↓        ↓        ↓
   ┌────────┐ ┌──────┐ ┌──────────────────┐
   │ Redis  │ │  DB  │ │ Supabase Storage │
   │ 6379   │ │ 5432 │ │ (Private Bucket) │
   └────────┘ └──────┘ └──────────────────┘
        ↑        ↑             ↑
    Cache    PostgreSQL    PDF Files
    Queue
        │
        ↓
   ┌──────────────────────┐
   │  Celery Worker       │
   │  ├─ PDF Compression  │
   │  ├─ Cleanup Tasks    │
   │  └─ Sync Operations  │
   └──────────────────────┘
```

## 📁 Project Structure

```
file_sharing_system/
├── backend/
│   ├── core/
│   │   ├── settings.py          # Django configuration
│   │   ├── urls.py              # Root URL routing
│   │   ├── celery.py            # Celery configuration
│   │   └── wsgi.py
│   ├── users/
│   │   ├── models.py            # CustomUser model
│   │   ├── views.py             # Auth views (Google OAuth)
│   │   ├── serializers.py       # Serializers
│   │   ├── urls.py              # Auth endpoints
│   │   └── middleware.py        # JWT middleware
│   ├── files/
│   │   ├── models.py            # PDF & ShareLink models
│   │   ├── views.py             # Upload & download views
│   │   ├── services.py          # Supabase integration
│   │   ├── tasks.py             # Celery tasks
│   │   ├── urls.py
│   │   └── serializers.py
│   ├── manage.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Login.tsx              # Google login
│   │   │   ├── Dashboard.tsx          # Main app
│   │   │   ├── FileUpload.tsx         # Upload form
│   │   │   └── ShareLinkModal.tsx     # QR & share
│   │   ├── api.ts                     # API client
│   │   ├── AuthContext.tsx            # Auth state
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── Dockerfile
│   └── .env
├── docker-compose.yml
├── .env
└── README.md
```

## 🔑 Key Endpoints

### Authentication
- `POST /api/auth/register/` - Register with email/password
- `POST /api/auth/login/` - Login with email/password
- `POST /api/auth/google/` - Google OAuth login
- `POST /api/auth/logout/` - Logout
- `GET /api/auth/me/` - Get current user

### Files
- `POST /api/files/upload-intent/` - Get presigned upload URL
- `POST /api/files/process/` - Initialize file processing
- `GET /share/<uuid>/` - Download with share link (public)

### Documentation
- `GET /api/schema/` - OpenAPI schema
- `GET /api/docs/` - Swagger UI
- `GET /api/redoc/` - ReDoc documentation

## 🔒 Security Features

- **Private Supabase Bucket**: All files are stored in a private bucket
- **Presigned URLs**: Time-limited (60s) signed download URLs
- **Rate Limiting**: Public share links throttled at 5 requests/minute
- **Download Limits**: Each share link has configurable max downloads
- **Email Verification**: Google OAuth auto-verifies emails
- **JWT Tokens**: Secure token-based authentication with refresh rotation
- **CORS Protection**: Configured origins only

## 🛠️ Development Workflow

### Backend Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver

# Run Celery worker
celery -A core worker --loglevel=info

# Run tests
python manage.py test
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (hot reload)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 📊 Database Schema

### Users
```sql
CustomUser:
  - id (PK)
  - email (UNIQUE)
  - password (hashed)
  - first_name, last_name
  - is_email_verified
  - created_at, updated_at
```

### Files
```sql
CompressedPDF:
  - id (PK)
  - user_id (FK)
  - original_name, original_size
  - compressed_size
  - storage_path
  - status (PROCESSING/COMPLETED/FAILED)
  - created_at

ShareLink:
  - id (PK)
  - token (UUID, UNIQUE)
  - pdf_id (FK)
  - expires_at
  - max_downloads, current_downloads
  - created_at
```

## 🧪 Testing

### Backend Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test users
python manage.py test files

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Frontend Testing

```bash
# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

## 📝 API Examples

### Google OAuth Login

```bash
curl -X POST http://localhost:8000/api/auth/google/ \
  -H "Content-Type: application/json" \
  -d '{"token":"google_id_token_here"}'
```

Response:
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

### Upload File

```bash
# 1. Get upload intent
curl -X POST http://localhost:8000/api/files/upload-intent/ \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename":"document.pdf","size":1024000}'

# 2. Upload file to presigned URL
curl -X PUT <presigned_url> \
  --data-binary @document.pdf \
  -H "Content-Type: application/pdf"

# 3. Process file
curl -X POST http://localhost:8000/api/files/process/ \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "storage_path":"raw/1/timestamp_document.pdf",
    "original_name":"document.pdf",
    "original_size":1024000,
    "expires_in_seconds":3600
  }'
```

## 🚨 Troubleshooting

### Port Already in Use

```bash
# Kill process on port
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

### Database Connection Issues

```bash
# Check Supabase connection
docker-compose exec web python manage.py dbshell

# Run migrations
docker-compose exec web python manage.py migrate
```

### Google OAuth Not Working

1. Verify Client ID is correct in `.env`
2. Check redirect URIs in Google Cloud Console
3. Verify CORS is properly configured
4. Check browser console for errors

### File Upload Failing

1. Verify Supabase credentials
2. Check bucket exists and is private
3. Verify presigned URLs are being generated
4. Check Celery worker is running

## 📚 Documentation

- [Django Documentation](https://docs.djangoproject.com/)
- [React Documentation](https://react.dev/)
- [Supabase Documentation](https://supabase.com/docs)
- [Google OAuth Documentation](https://developers.google.com/identity)
- [Celery Documentation](https://docs.celeryproject.org/)

## 📝 License

MIT

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📞 Support

For issues and questions, please open an issue on the project repository.

---

**Happy Sharing! 🎉**
