# 📄 PDF Sharing Platform


 

 A modern, production-ready file-sharing platform built with **React**, **Django REST Framework**, **Redis**, **Celery**, and **Supabase Storage**. Securely upload, manage, and share PDF files using expiring links, QR codes, and configurable download limits.

#### 🚀 Live Demo

* **Application:** https://share-file.rabiaryal.com.np


## 🌟 Key Features

### 🔐 Security & Authentication

* **Google OAuth 2.0 Login** - Secure authentication using Google accounts
* **JWT Authentication** - Access and refresh token-based authentication
* **Private Supabase Storage** - Files stored securely in a private bucket
* **Presigned Download URLs** - Time-limited secure file access
* **Rate Limiting** - Protection against abuse and excessive requests
* **Access Validation** - Enforces expiration and download restrictions

### 📤 File Upload & Sharing

* **Drag-and-Drop Upload** - Simple and intuitive file upload experience
* **Direct-to-Storage Uploads** - Upload files directly to Supabase using presigned URLs
* **Shareable Links** - Generate unique links for secure file sharing
* **QR Code Generation** - Instantly create QR codes for mobile access
* **Social Sharing** - Share files via Email, WhatsApp, and Twitter
* **Upload Progress Tracking** - Real-time upload status and feedback

### 📊 Advanced Features

* **Download Limits** - Configure maximum downloads per shared file
* **Link Expiration** - Set expiration periods from 1 hour to 7 days
* **Background Processing** - Celery-powered asynchronous task execution
* **Redis Integration** - Task queue and caching support
* **Storage Quota Management** - Per-user storage limits and usage tracking
* **Download Analytics** - Monitor file downloads and usage statistics

### ⚡ Performance & Scalability

* **Asynchronous Tasks** - Non-blocking background processing with Celery
* **Cloud Storage Integration** - Scalable file storage using Supabase
* **Presigned Uploads** - Reduced backend load through direct file uploads
* **Optimized API Design** - RESTful APIs built with Django REST Framework


## 🌟 Problem Occured during this prject and their solutions

* **Backend server Becomes Inactivate after few minutes** - used the github actions to ping the server every five minutes, but it might not work on the free tier.

* **Takes a lots of time to upload the file** -- this is due  the implementation fo compression, as initially it tries to compress, currently compression is completely removed, as modern pdf are already compressed 



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
## How major parts works 

### file uploading process
#### first  Implementation
I have used the s3 signed url of the supbase to upload the file  and currenttly it uploads the  up to 50MB at once and it is prety slow and compltelty dependent on the internet speed .
#### second implementation
File would be uploaded in the chunk, but it will not incresse the upload speed , it will make the system more reliabl.Will be using this protocol TUS( Resumable Upload Protocol),It uploads the file in parts. Server remembers progress. If it fails → continue from last saved point. And it is implemented on the frontend side only.

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

