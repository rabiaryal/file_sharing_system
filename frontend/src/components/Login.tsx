import React from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { useAuth } from '../AuthContext';

const Login: React.FC = () => {
    const { login, isLoading } = useAuth();

    const handleGoogleSuccess = async (credentialResponse: any) => {
        try {
            await login(credentialResponse.credential);
        } catch (error) {
            console.error('Login failed:', error);
            alert('Login failed. Please try again.');
        }
    };

    const handleGoogleError = () => {
        console.log('Login Failed');
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-500 to-purple-600">
            <div className="bg-white rounded-lg shadow-2xl p-8 w-full max-w-md">
                <h1 className="text-3xl font-bold text-gray-800 mb-2 text-center">
                    PDF Sharing Platform
                </h1>
                <p className="text-gray-600 text-center mb-8">
                    Share your PDFs securely with shareable links
                </p>

                <div className="flex justify-center mb-6">
                    {isLoading ? (
                        <div className="text-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                            <p className="mt-2 text-gray-600">Loading...</p>
                        </div>
                    ) : (
                        <GoogleLogin
                            onSuccess={handleGoogleSuccess}
                            onError={handleGoogleError}
                        />
                    )}
                </div>

                <div className="mt-6 pt-6 border-t border-gray-200">
                    <p className="text-sm text-gray-500 text-center">
                        Sign in with your Google account to get started
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Login;
