import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { filesAPI, ShareLinkInfo } from '../api';
import QRCode from 'qrcode.react';

const SharePage: React.FC = () => {
    const { token } = useParams<{ token: string }>();
    const navigate = useNavigate();
    const [shareInfo, setShareInfo] = useState<ShareLinkInfo | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [downloading, setDownloading] = useState(false);

    useEffect(() => {
        const loadShareInfo = async () => {
            try {
                if (!token) {
                    setError('Invalid share link');
                    return;
                }
                const response = await filesAPI.getShareLinkInfo(token);
                setShareInfo(response.data);
            } catch (err: any) {
                if (err.response?.status === 404) {
                    setError('This share link does not exist.');
                } else if (err.response?.status === 410) {
                    setError('This share link has expired.');
                } else {
                    setError('Failed to load share link information.');
                }
                console.error('Error loading share info:', err);
            } finally {
                setLoading(false);
            }
        };

        loadShareInfo();
    }, [token]);

    const handleDownload = async () => {
        if (!token) return;
        try {
            setDownloading(true);
            // Get the API base URL and construct full download URL
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const downloadUrl = `${apiUrl}/api/files/share/${token}/`;
            window.location.href = downloadUrl;
        } catch (err) {
            setError('Failed to download file');
            console.error('Download error:', err);
            setDownloading(false);
        }
    };

    const handleShare = (platform: 'twitter' | 'whatsapp' | 'email' | 'copy') => {
        const url = window.location.href;
        const text = `Download "${shareInfo?.filename}" - ${window.location.origin}`;

        if (platform === 'twitter') {
            window.open(
                `https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`,
                '_blank'
            );
        } else if (platform === 'whatsapp') {
            window.open(
                `https://wa.me/?text=${encodeURIComponent(`${text} ${url}`)}`,
                '_blank'
            );
        } else if (platform === 'email') {
            window.location.href = `mailto:?subject=Check out this file&body=${encodeURIComponent(text + '\n\n' + url)}`;
        } else if (platform === 'copy') {
            navigator.clipboard.writeText(url);
            alert('Link copied to clipboard!');
        }
    };

    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-500 to-purple-600">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                    <p className="text-white">Loading share link...</p>
                </div>
            </div>
        );
    }

    if (error || !shareInfo) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-500 to-purple-600">
                <div className="bg-white rounded-lg shadow-2xl p-8 w-full max-w-md text-center">
                    <h1 className="text-2xl font-bold text-gray-800 mb-4">
                        🔗 Share Link Error
                    </h1>
                    <p className="text-gray-600 mb-6">{error || 'Unknown error occurred'}</p>
                    <button
                        onClick={() => navigate('/')}
                        className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg transition"
                    >
                        Go Back Home
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 p-4">
            <div className="max-w-2xl mx-auto">
                {/* Header */}
                <div className="text-center mb-8 pt-8">
                    <h1 className="text-4xl font-bold text-white mb-2">📄 File Shared!</h1>
                    <p className="text-blue-100">Download the file from the link below</p>
                </div>

                {/* Main Card */}
                <div className="bg-white rounded-lg shadow-2xl p-8 mb-6">
                    {/* File Info */}
                    <div className="mb-8">
                        <h2 className="text-2xl font-bold text-gray-800 mb-6">📥 File Information</h2>

                        <div className="space-y-4">
                            <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                                <span className="text-gray-600 font-medium">Filename:</span>
                                <span className="text-gray-800 font-semibold break-all max-w-xs text-right">
                                    {shareInfo.filename}
                                </span>
                            </div>

                            <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                                <span className="text-gray-600 font-medium">File Size:</span>
                                <span className="text-gray-800 font-semibold">
                                    {formatFileSize(shareInfo.size)}
                                </span>
                            </div>

                            <div className="flex justify-between items-center p-4 bg-green-50 rounded-lg border-2 border-green-200">
                                <span className="text-gray-600 font-medium">Status:</span>
                                <span className="text-lg font-bold text-green-600">
                                    ✓ Ready to Download
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Download Button */}
                    <div className="mb-8">
                        <button
                            onClick={handleDownload}
                            disabled={downloading}
                            className={`w-full py-3 px-6 rounded-lg font-bold text-white text-lg transition ${downloading
                                ? 'bg-gray-400 cursor-not-allowed'
                                : 'bg-green-500 hover:bg-green-600'
                                }`}
                        >
                            {downloading ? '⏳ Downloading...' : '⬇️ Download File'}
                        </button>
                        <div className="border-4 border-gray-200 p-4 rounded-lg bg-white">
                            <QRCode
                                value={window.location.href}
                                size={256}
                                level="H"
                                includeMargin={true}
                            />
                        </div>
                    </div>

                    {/* Share Options */}
                    <div className="border-t-2 border-gray-200 pt-8">
                        <h3 className="text-lg font-bold text-gray-800 mb-4">📤 Share This Link</h3>
                        <div className="grid grid-cols-2 gap-3">
                            <button
                                onClick={() => handleShare('twitter')}
                                className="flex items-center justify-center gap-2 p-3 bg-blue-400 text-white rounded-lg hover:bg-blue-500 transition font-semibold"
                            >
                                𝕏 Twitter
                            </button>
                            <button
                                onClick={() => handleShare('whatsapp')}
                                className="flex items-center justify-center gap-2 p-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition font-semibold"
                            >
                                💬 WhatsApp
                            </button>
                            <button
                                onClick={() => handleShare('email')}
                                className="flex items-center justify-center gap-2 p-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition font-semibold"
                            >
                                📧 Email
                            </button>
                            <button
                                onClick={() => handleShare('copy')}
                                className="flex items-center justify-center gap-2 p-3 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition font-semibold"
                            >
                                📋 Copy Link
                            </button>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="text-center text-blue-100 text-sm">
                    <p>Secure file sharing with expiring links</p>
                </div>
            </div>
        </div>
    );
};

export default SharePage;
