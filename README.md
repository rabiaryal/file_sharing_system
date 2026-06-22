# 📄 PDF Sharing Platform


 

 A modern, production-ready file-sharing platform built with **React**, **Django REST Framework**, **Redis**, **Celery**, and **Supabase Storage**. Securely upload, manage, and share PDF files using expiring links, QR codes, and configurable download limits.

#### 🚀 Live Demo

* **Application:** https://share-file.rabiaryal.com.np


## 🔑 Core Features

- **Google OAuth Authentication**  
  The frontend retrieves a Google ID token JWT using `@react-oauth/google` and sends it to the Django `/api/auth/google/` endpoint. The backend verifies the token using the `google-auth` library, creates/retrieves a `CustomUser` record, and returns a SimpleJWT access/refresh token pair.

- **File Upload System (Drag & Drop)**  
  Implemented using a React drag-and-drop file dropzone integrated with `tus-js-client`. Files are split and uploaded in 6MB chunks to Supabase Storage via the TUS resumable protocol, providing robust error-recovery, auto-retry, and real-time progress percentages.

- **Direct-to-Storage Uploads (Supabase)**  
  The backend uses the Python `supabase` SDK to call `create_signed_upload_url(path)`. The frontend extracts the signature token from the returned signed URL and passes it in the `x-signature` header of the TUS upload client, bypassing the Django server completely to save bandwidth.

- **Secure File Sharing (HMAC Links)**  
  Generates stateless, secure tokens formatted as `{file_id}-{expiry_timestamp}-{signature}`. The signature is computed using a symmetric HMAC-SHA256 signature generated over the file ID and expiry using Django's private `SECRET_KEY`.

- **Secure Download System**  
  A custom Django middleware (`SecureTokenMiddleware`) intercepts requests containing a token, recomputes the HMAC-SHA256 signature using `SECRET_KEY`, validates it with `hmac.compare_digest` to prevent timing attacks, and redirects authorized requests to a short-lived (60s) Supabase presigned download URL.

- **Link Expiration Control and Download Limits per File**  
  Link expiration is verified statelessly by the middleware checking the embedded expiration timestamp. Download limit counters are stored in the database (`ShareLink` model) and validated dynamically upon download, returning `410 Gone` if limits are exceeded.

---

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

### file Download process

The file download system uses a stateless, token-based secure access mechanism rather than requiring user session logins:

1. **Share Link Generation**: When a file is uploaded, the backend generates a cryptographically signed token containing the file ID, expiration timestamp, and an HMAC signature using the backend's secret key:
   `token = {file_id}-{expiry_timestamp}-{signature}`
2. **Client Requests File**: The user accesses the share link (e.g., `GET /share/{token}/`) or info endpoint without needing to log in.
3. **Middleware Authentication (Stateless)**: The `SecureTokenMiddleware` intercepts the request and verifies the token:
   - Recomputes the expected signature: `HMAC(file_id + expiry_time, SECRET_KEY)`
   - Safely compares the signatures using `compare_digest` to prevent timing attacks.
   - Checks if the token is still within its access window (`current_time < expiry_time`).
4. **Request Authorization**: If valid, the middleware attaches the verified file ID (`request.verified_file_id = file_id`) to the request context and passes it to the view.
5. **Secure File Delivery**: The view generates a temporary (60s) signed URL from the private Supabase Storage bucket and redirects the user, downloading the file directly:
   `Client` ➔ `Django (Verifies Token)` ➔ `Temporary Signed URL` ➔ `Supabase` ➔ `File Download`

### Rate limiting features implementaion

#### 🔐 Auth Endpoint (/auth/google)

Rate limiting is applied using **Nginx + IP-based Redis token bucket**.

- **Nginx Layer:** Limits global request spikes before reaching backend.
- **Redis Layer (IP Bucket):** Restricts login attempts per IP to prevent brute-force attacks.
- No user-based limiting is used since authentication happens here.

---

#### 📥 Download Endpoint (/download)

Uses **Nginx + HMAC validation + Redis rate limiting**.

- **Nginx Layer:** Prevents global traffic spikes.
- **HMAC Middleware:** Validates secure shareable link (expiry + signature).
- **Redis Layer:** Applies IP/User-based limits to prevent repeated downloads and link abuse.

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

## ⚙️ Additional Features

 **API-Driven Backend (Django REST Framework)**  
  Clean REST APIs for authentication, upload, download, and file management.

- **QR Code Generation**  
  Converts shareable links into QR codes for quick mobile access.

- **Social Sharing Support**  
  Share files directly via Email, WhatsApp, and Twitter.

- **Download Analytics System**  
  Tracks file access, downloads, and usage statistics for monitoring.

- **Background Processing (Celery)**  
  Handles heavy tasks like analytics, notifications, and async processing.

- **Redis Integration**  
  Used for caching, rate limiting, and background task queue management.

- **Rate Limiting System (Nginx + Redis)**  
  Protects APIs using global, IP-based, and user-based token bucket limits.

- **Storage Quota Management**  
  Enforces per-user storage limits and tracks total usage.

- **Presigned Download System (Supabase)**  
  Secure temporary URLs ensure private files are not directly exposed.



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

