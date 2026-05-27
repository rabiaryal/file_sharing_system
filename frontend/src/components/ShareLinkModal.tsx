import React, { useState } from 'react';
import QRCode from 'qrcode.react';

interface ShareLinkModalProps {
    file: {
        token: string;
        share_url: string;
        expires_at: string;
        original_name: string;
    };
    onReset: () => void;
}

export const ShareLinkModal: React.FC<ShareLinkModalProps> = ({
    file,
    onReset,
}) => {
    const [copied, setCopied] = useState(false);

    const shareUrl = `${window.location.origin}/share/${file.token}`;

    const handleCopyLink = async () => {
        try {
            await navigator.clipboard.writeText(shareUrl);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    const handleDownloadQR = () => {
        const qrElement = document.getElementById('qr-code');
        if (qrElement) {
            const canvas = qrElement.querySelector('canvas');
            if (canvas) {
                const link = document.createElement('a');
                link.href = canvas.toDataURL('image/png');
                link.download = `${file.original_name}-qrcode.png`;
                link.click();
            }
        }
    };

    const expiresAt = new Date(file.expires_at);
    const expiresIn = Math.floor((expiresAt.getTime() - Date.now()) / 1000 / 60);

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-2xl p-8 max-w-md w-full">
                <div className="text-center">
                    <svg
                        className="mx-auto h-12 w-12 text-green-500 mb-4"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                    >
                        <path
                            fillRule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                            clipRule="evenodd"
                        />
                    </svg>
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">
                        Upload Successful!
                    </h3>
                    <p className="text-gray-600 mb-6">
                        Your file is ready to share
                    </p>
                </div>

                {/* File Info */}
                <div className="bg-gray-50 rounded-lg p-4 mb-6">
                    <p className="text-sm text-gray-600">
                        <span className="font-semibold">File:</span> {file.original_name}
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                        <span className="font-semibold">Expires in:</span> {expiresIn} minutes
                    </p>
                </div>

                {/* QR Code */}
                <div className="flex justify-center mb-6">
                    <div
                        id="qr-code"
                        className="border-4 border-gray-200 rounded-lg p-2 bg-white"
                    >
                        <QRCode
                            value={shareUrl}
                            size={256}
                            level="H"
                            includeMargin={true}
                        />
                    </div>
                </div>

                {/* Share Link */}
                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Share Link
                    </label>
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={shareUrl}
                            readOnly
                            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm"
                        />
                        <button
                            onClick={handleCopyLink}
                            className={`px-4 py-2 rounded-lg font-medium transition ${copied
                                ? 'bg-green-500 text-white'
                                : 'bg-blue-500 text-white hover:bg-blue-600'
                                }`}
                        >
                            {copied ? '✓ Copied' : 'Copy'}
                        </button>
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3">
                    <button
                        onClick={handleDownloadQR}
                        className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 font-medium transition"
                    >
                        Download QR
                    </button>
                    <button
                        onClick={onReset}
                        className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 font-medium transition"
                    >
                        Upload Another
                    </button>
                </div>

                {/* Social Share Buttons */}
                <div className="mt-6 pt-6 border-t border-gray-200">
                    <p className="text-xs text-gray-600 text-center mb-3">
                        Share via
                    </p>
                    <div className="flex gap-3 justify-center">
                        <button
                            onClick={() => {
                                const text = `Check out my file: ${shareUrl}`;
                                window.open(
                                    `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`,
                                    '_blank'
                                );
                            }}
                            className="px-3 py-2 bg-blue-400 text-white rounded hover:bg-blue-500 text-sm"
                        >
                            Twitter
                        </button>
                        <button
                            onClick={() => {
                                window.open(
                                    `https://wa.me/?text=${encodeURIComponent(shareUrl)}`,
                                    '_blank'
                                );
                            }}
                            className="px-3 py-2 bg-green-500 text-white rounded hover:bg-green-600 text-sm"
                        >
                            WhatsApp
                        </button>
                        <button
                            onClick={() => {
                                window.location.href = `mailto:?subject=PDF Share&body=${encodeURIComponent(shareUrl)}`;
                            }}
                            className="px-3 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm"
                        >
                            Email
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
