# PDF Sharing Platform - Frontend

A modern React frontend for the PDF Sharing Platform with Google OAuth authentication and QR code generation.

## Features

- 🔐 Google OAuth authentication
- 📤 Drag-and-drop PDF file upload
- 🔗 Shareable links with expiration
- 📱 QR code generation for easy sharing
- 📊 Social media sharing (Twitter, WhatsApp, Email)
- 🎨 Modern Tailwind CSS UI
- ⚡ Built with Vite for fast development

## Prerequisites

- Node.js 16+ and npm
- Google OAuth 2.0 credentials (Client ID)

## Setup

### 1. Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the "Google+ API"
4. Create OAuth 2.0 credentials (Web application)
5. Add `http://localhost:3000` to Authorized JavaScript origins
6. Add `http://localhost:3000` to Authorized redirect URIs
7. Add your production frontend origin, for example `https://share-file.rabi-aryal.com.np`, to Authorized JavaScript origins. This app uses the popup-based `@react-oauth/google` flow, so the browser origin of the frontend must match exactly.
8. Copy your **Client ID**

### 2. Environment Configuration

Create a `.env` file in the `frontend/` directory:

```env
VITE_GOOGLE_CLIENT_ID=your_google_client_id_here
VITE_API_URL=http://localhost:8000
```

For production on Vercel, set `VITE_API_URL` to your Render backend URL, for example `https://file-sharing-api-latest-r939.onrender.com`, and redeploy so Vite bakes the value into the client bundle.

### 3. Install Dependencies

```bash
cd frontend
npm install
```

### 4. Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 5. Build for Production

```bash
npm run build
```

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # React components
│   │   ├── Login.tsx           # Google login component
│   │   ├── Dashboard.tsx       # Main dashboard
│   │   ├── FileUpload.tsx      # File upload component
│   │   └── ShareLinkModal.tsx  # QR code & share link display
│   ├── api.ts           # API client configuration
│   ├── AuthContext.tsx  # Authentication context
│   ├── App.tsx          # Main app component
│   ├── main.tsx         # Application entry point
│   └── index.css        # Global styles with Tailwind
├── index.html           # HTML template
├── vite.config.ts       # Vite configuration
├── tailwind.config.js   # Tailwind CSS configuration
├── tsconfig.json        # TypeScript configuration
└── package.json         # Dependencies and scripts
```

## API Integration

The frontend communicates with the Django backend via REST API:

- `POST /api/auth/google/` - Google OAuth login
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/me/` - Get current user info
- `POST /api/files/upload-intent/` - Get presigned upload URL
- `POST /api/files/process/` - Initialize file processing
- `GET /share/<uuid>/` - Download with share link

## Docker Deployment

```bash
docker-compose up --build
```

This will:
- Build the React app with Vite
- Start the frontend on port 3000
- Connect to the Django backend on port 8000

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## License

MIT
