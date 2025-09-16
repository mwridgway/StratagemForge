'use client';

import { useState, useRef } from 'react';
import Link from 'next/link';

interface UploadResponse {
  id: string;
  filename: string;
  size: number;
  status: string;
  message: string;
}

export default function UploadPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      setError('No file selected');
      setSelectedFile(null);
      return;
    }
    // Check if it's a .dem file by extension and MIME type
    const isDemExtension = file.name.endsWith('.dem');
    const isDemMimeType = file.type === '' || file.type === 'application/octet-stream';
    if (isDemExtension && isDemMimeType) {
      setSelectedFile(file);
      setError(null);
    } else {
      setError('Please select a valid .dem file');
      setSelectedFile(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setError(null);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('demo', selectedFile);

      const response = await fetch('/api/demos/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Upload failed: ${response.status}`);
      }

      const result: UploadResponse = await response.json();
      setUploadResult(result);
      setSelectedFile(null);
      
      // Reset the file input using ref
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Link 
            href="/" 
            className="text-blue-600 hover:text-blue-800 font-medium mb-4 inline-block"
          >
            ← Back to Home
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">
            Upload CS2 Demo
          </h1>
          <p className="mt-2 text-gray-600">
            Select a CS2 demo file (.dem) to upload for analysis
          </p>
        </div>

        {/* Upload Form */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="space-y-6">
            {/* File Selection */}
            <div>
              <label htmlFor="demo-file" className="block text-sm font-medium text-gray-700 mb-2">
                Select Demo File
              </label>
              <input
                id="demo-file"
                ref={fileInputRef}
                type="file"
                accept=".dem"
                onChange={handleFileSelect}
                disabled={uploading}
                className="block w-full text-sm text-gray-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-md file:border-0
                  file:text-sm file:font-medium
                  file:bg-blue-50 file:text-blue-700
                  hover:file:bg-blue-100
                  disabled:opacity-50 disabled:cursor-not-allowed"
              />
            </div>

            {/* Selected File Info */}
            {selectedFile && (
              <div className="bg-gray-50 rounded-md p-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Selected File:</h3>
                <div className="text-sm text-gray-600">
                  <p><span className="font-medium">Name:</span> {selectedFile.name}</p>
                  <p><span className="font-medium">Size:</span> {formatFileSize(selectedFile.size)}</p>
                  <p><span className="font-medium">Type:</span> {selectedFile.type || 'application/octet-stream'}</p>
                </div>
              </div>
            )}

            {/* Upload Button */}
            <div>
              <button
                onClick={handleUpload}
                disabled={!selectedFile || uploading}
                className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
                  !selectedFile || uploading
                    ? 'bg-gray-300 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
                }`}
              >
                {uploading ? (
                  <div className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Uploading...
                  </div>
                ) : (
                  'Upload Demo'
                )}
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">Error</h3>
                    <div className="mt-2 text-sm text-red-700">
                      {error}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Success Message */}
            {uploadResult && (
              <div className="bg-green-50 border border-green-200 rounded-md p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-green-800">Upload Successful!</h3>
                    <div className="mt-2 text-sm text-green-700">
                      <p><span className="font-medium">Demo ID:</span> {uploadResult.id}</p>
                      <p><span className="font-medium">Filename:</span> {uploadResult.filename}</p>
                      <p><span className="font-medium">Size:</span> {formatFileSize(uploadResult.size)}</p>
                      <p><span className="font-medium">Status:</span> {uploadResult.status}</p>
                      <p className="mt-1">{uploadResult.message}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-md p-4">
          <h3 className="text-sm font-medium text-blue-800 mb-2">Instructions:</h3>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Only CS2 demo files (.dem) are accepted</li>
            <li>• Maximum file size is 1GB</li>
            <li>• Processing will begin automatically after upload</li>
            <li>• You can check the status through the main dashboard</li>
          </ul>
        </div>
      </div>
    </div>
  );
}