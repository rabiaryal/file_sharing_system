import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add token to requests if available
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export interface GoogleLoginPayload {
    token: string;
}

export interface AuthResponse {
    message: string;
    tokens: {
        access: string;
        refresh: string;
    };
    user: {
        id: number;
        email: string;
        first_name: string;
        last_name: string;
    };
}

export interface UploadIntentResponse {
    upload_url: string;
    storage_path: string;
    signed_url: string;
}

export interface ProcessPayload {
    storage_path: string;
    original_name: string;
    original_size: number;
    expires_in_seconds: number;
}

export interface ProcessResponse {
    token: string;
    share_url: string;
    expires_at: string;
}

export interface ShareLinkInfo {
    token: string;
    filename: string;
    size: number;
    expired: boolean;
}

export const authAPI = {
    googleLogin: (googleToken: string) =>
        api.post<AuthResponse>('/api/auth/google/', { token: googleToken }),

    logout: () =>
        api.post('/api/auth/logout/'),

    getCurrentUser: () =>
        api.get('/api/auth/me/'),
};

export const filesAPI = {
    getUploadIntent: (filename: string, size: number) =>
        api.post<UploadIntentResponse>('/api/files/upload-intent/', {
            filename,
            size,
        }),

    processFile: (payload: ProcessPayload) =>
        api.post<ProcessResponse>('/api/files/process/', payload),

    getShareLinkInfo: (token: string) =>
        api.get<ShareLinkInfo>(`/api/files/share/${token}/info/`),

    downloadFile: (token: string) =>
        api.get(`/api/files/share/${token}/`, {
            responseType: 'blob',
            maxRedirects: 5,
        }),
};
