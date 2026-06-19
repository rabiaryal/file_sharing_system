import React, { useState } from 'react';
import * as tus from 'tus-js-client';
import { filesAPI } from '../api';
import { ShareLinkModal } from './ShareLinkModal';

interface UploadedFile {
    token: string;
    share_url: string;
    expires_at: string;
    original_name: string;
}

const FileUpload: React.FC = () => {
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [expiresInSeconds, setExpiresInSeconds] = useState(3600); // 1 hour default
    const [uploadProgress, setUploadProgress] = useState(0);

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const uploadFile = async (file: File) => {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            setError('Please upload a PDF file');
            return;
        }

        setIsUploading(true);
        setUploadProgress(0);
        setError(null);

        try {
            // Step 1: Get upload intent
            const intentRes = await filesAPI.getUploadIntent(file.name, file.size);
            const uploadUrl = intentRes.data.upload_url;
            const storagePath = intentRes.data.storage_path;

            const url = new URL(uploadUrl);
            const endpoint = `${url.protocol}//${url.host}/storage/v1/upload/resumable`;
            const token = url.searchParams.get('token');
            if (!token) {
                throw new Error('Failed to retrieve upload token from signed URL');
            }
            const pathParts = url.pathname.split('/');
            const bucketName = pathParts[6] || 'pdfs';

            // Step 2: Upload file to Supabase via TUS resumable protocol
            await new Promise<void>((resolve, reject) => {
                const upload = new tus.Upload(file, {
                    endpoint,
                    retryDelays: [0, 1000, 3000, 5000],
                    headers: {
                        'x-signature': token,
                    },
                    metadata: {
                        bucketName,
                        objectName: storagePath,
                        contentType: file.type || 'application/pdf',
                    },
                    chunkSize: 6 * 1024 * 1024,
                    uploadDataDuringCreation: true,
                    removeFingerprintOnSuccess: true,
                    onError: (error) => {
                        reject(error);
                    },
                    onProgress: (bytesUploaded, bytesTotal) => {
                        const percentage = (bytesUploaded / bytesTotal) * 100;
                        setUploadProgress(percentage);
                    },
                    onSuccess: () => {
                        resolve();
                    },
                });
                upload.start();
            });

            // Step 3: Process file on backend
            const processRes = await filesAPI.processFile({
                storage_path: storagePath,
                original_name: file.name,
                original_size: file.size,
                expires_in_seconds: expiresInSeconds,
            });

            setUploadedFile({
                token: processRes.data.token,
                share_url: processRes.data.share_url,
                expires_at: processRes.data.expires_at,
                original_name: file.name,
            });
        } catch (err) {
            console.error('Upload error:', err);
            setError('Failed to upload file. Please try again.');
        } finally {
            setIsUploading(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            uploadFile(files[0]);
        }
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.currentTarget.files;
        if (files && files.length > 0) {
            uploadFile(files[0]);
        }
    };

    if (uploadedFile) {
        return (
            <ShareLinkModal
                file={uploadedFile}
                onReset={() => setUploadedFile(null)}
            />
        );
    }

    return (
        <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-lg shadow-lg p-8">
                <h2 className="text-2xl font-bold text-gray-800 mb-6">Upload PDF</h2>

                {/* Settings */}
                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Link Expiry (seconds)
                    </label>
                    <input
                        type="number"
                        value={expiresInSeconds}
                        onChange={(e) => setExpiresInSeconds(parseInt(e.target.value))}
                        min={3600}
                        max={2592000} // 30 days
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <p className="text-gray-500 text-xs mt-1">Minimum 1 hour, Maximum 30 days</p>
                </div>

                {/* Upload Area */}
                <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition ${isDragging
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-300 bg-gray-50 hover:border-gray-400'
                        } ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                    {isUploading ? (
                        <div className="w-full max-w-md mx-auto py-4">
                            <div className="flex justify-between items-center mb-2">
                                <span className="text-sm font-semibold text-blue-600">
                                    Uploading PDF...
                                </span>
                                <span className="text-sm font-bold text-blue-600">
                                    {Math.round(uploadProgress)}%
                                </span>
                            </div>
                            <div className="w-full bg-blue-100 rounded-full h-3 overflow-hidden shadow-inner">
                                <div
                                    className="bg-blue-500 h-full rounded-full transition-all duration-300 ease-out"
                                    style={{ width: `${uploadProgress}%` }}
                                ></div>
                            </div>
                            <p className="text-xs text-gray-500 mt-2">
                                Resumable upload in progress. Do not close this window.
                            </p>
                        </div>
                    ) : (
                        <>
                            <svg
                                className="mx-auto h-12 w-12 text-gray-400"
                                stroke="currentColor"
                                fill="none"
                                viewBox="0 0 48 48"
                            >
                                <path
                                    d="M28 8H12a4 4 0 00-4 4v24a4 4 0 004 4h24a4 4 0 004-4V20m-6-12l-6-6m0 0l-6 6m6-6v24"
                                    strokeWidth="2"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                />
                            </svg>
                            <p className="mt-4 text-lg font-medium text-gray-900">
                                Drop your PDF here or click to upload
                            </p>
                            <p className="text-gray-500 text-sm mt-1">
                                Only PDF files are accepted
                            </p>
                            <input
                                type="file"
                                accept=".pdf"
                                onChange={handleFileSelect}
                                className="hidden"
                                id="file-input"
                                disabled={isUploading}
                            />
                            <label
                                htmlFor="file-input"
                                className="mt-4 inline-block px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Select PDF
                            </label>
                        </>
                    )}
                </div>

                {error && (
                    <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                        {error}
                    </div>
                )}
            </div>
        </div>
    );
};

export default FileUpload;
