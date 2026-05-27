import React from 'react';
import { useAuth } from '../AuthContext';
import FileUpload from './FileUpload';

const Dashboard: React.FC = () => {
    const { user, logout, isLoading } = useAuth();

    const handleLogout = async () => {
        if (window.confirm('Are you sure you want to logout?')) {
            await logout();
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow">
                <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold text-blue-600">PDF Sharing</h1>
                        <p className="text-sm text-gray-500">Share PDFs securely</p>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="text-right">
                            <p className="text-sm font-medium text-gray-900">{user?.email}</p>
                            <p className="text-xs text-gray-500">
                                {user?.first_name || 'User'}
                            </p>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition"
                        >
                            Logout
                        </button>
                    </div>
                </nav>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="grid md:grid-cols-3 gap-6 mb-12">
                    <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                        <div className="flex items-center justify-center h-12 w-12 rounded-md bg-blue-500 text-white mb-3">
                            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8m0 0l-6 3m6-3l6 3" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-1">
                            Instant Upload
                        </h3>
                        <p className="text-sm text-gray-600">
                            Upload your PDF files instantly and get shareable links
                        </p>
                    </div>

                    <div className="bg-green-50 rounded-lg p-6 border border-green-200">
                        <div className="flex items-center justify-center h-12 w-12 rounded-md bg-green-500 text-white mb-3">
                            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 11c0 3.517-1.009 6.799-2.753 9.571m5.506 0A9.969 9.969 0 0121 12a9.969 9.969 0 01-15.757-4.414m11.251 5.856c.934 1.374 1.5 3.02 1.5 4.784 0 1.763-.566 3.41-1.5 4.784m2.495-7.466A5.001 5.001 0 0119 13m0 0h-4" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-1">
                            Share Securely
                        </h3>
                        <p className="text-sm text-gray-600">
                            Generate QR codes and links with expiration times and download limits
                        </p>
                    </div>

                    <div className="bg-purple-50 rounded-lg p-6 border border-purple-200">
                        <div className="flex items-center justify-center h-12 w-12 rounded-md bg-purple-500 text-white mb-3">
                            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-1">
                            Privacy First
                        </h3>
                        <p className="text-sm text-gray-600">
                            Your files are encrypted and stored securely in the cloud
                        </p>
                    </div>
                </div>

                {/* File Upload Section */}
                <FileUpload />
            </main>
        </div>
    );
};

export default Dashboard;
