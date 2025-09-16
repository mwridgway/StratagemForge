'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface ServiceHealth {
  status: string;
  service: string;
  version?: string;
  uptime?: number;
}

interface HealthData {
  bff: ServiceHealth;
  services: {
    userService: ServiceHealth;
    ingestionService: ServiceHealth;
    analysisService: ServiceHealth;
  };
}

export default function HomePage() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        // Call our internal API route which will proxy to the BFF service
        const response = await fetch('/api/system-status');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setHealth(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch health data');
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
  }, []);

  const formatUptime = (uptime?: number): string => {
    if (!uptime) return 'Unknown';
    const seconds = Math.floor(uptime / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'unhealthy': return 'text-red-600';
      default: return 'text-yellow-600';
    }
  };

  const getStatusIcon = (status: string): string => {
    switch (status) {
      case 'healthy': return '✅';
      case 'unhealthy': return '❌';
      default: return '⚠️';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900">StratagemForge</h1>
            <nav className="space-x-4">
              <Link href="/" className="text-primary-600 hover:text-primary-800">
                Home
              </Link>
              <Link href="/upload" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors">
                Upload Demo
              </Link>
              <Link href="/demos" className="text-gray-600 hover:text-gray-800">
                Demos
              </Link>
              <Link href="/analysis" className="text-gray-600 hover:text-gray-800">
                Analysis
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-extrabold text-gray-900 mb-4">
            Counterstrike 2 Demo Analysis Platform
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Upload, analyze, and gain insights from your Counterstrike 2 demo files. 
            Track performance, study strategies, and improve your gameplay with advanced analytics.
          </p>
          <div className="mt-8">
            <Link 
              href="/upload" 
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              Upload Your First Demo
            </Link>
          </div>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
          <Link href="/upload" className="card hover:shadow-lg transition-shadow cursor-pointer">
            <div className="card-body text-center">
              <div className="text-4xl mb-4">📁</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Demo Upload</h3>
              <p className="text-gray-600">
                Upload Counterstrike 2 demo files (.dem) for processing and analysis
              </p>
            </div>
          </Link>

          <div className="card">
            <div className="card-body text-center">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Advanced Analytics</h3>
              <p className="text-gray-600">
                Get detailed statistics, heatmaps, and performance metrics
              </p>
            </div>
          </div>

          <div className="card">
            <div className="card-body text-center">
              <div className="text-4xl mb-4">🎯</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Strategy Planning</h3>
              <p className="text-gray-600">
                Develop strategies based on data-driven insights and trends
              </p>
            </div>
          </div>
        </div>

        {/* System Status */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">System Status</h3>
          </div>
          <div className="card-body">
            {loading && (
              <div className="text-center py-4">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                <p className="mt-2 text-gray-600">Loading system status...</p>
              </div>
            )}

            {error && (
              <div className="text-center py-4">
                <p className="text-red-600">Error: {error}</p>
              </div>
            )}

            {health && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* BFF Service */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-900">BFF Service</h4>
                    <span className={getStatusColor(health.bff.status)}>
                      {getStatusIcon(health.bff.status)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">
                    Uptime: {formatUptime(health.bff.uptime)}
                  </p>
                  <p className="text-sm text-gray-600">
                    Version: {health.bff.version || 'Unknown'}
                  </p>
                </div>

                {/* User Service */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-900">User Service</h4>
                    <span className={getStatusColor(health.services.userService.status)}>
                      {getStatusIcon(health.services.userService.status)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">Authentication & Users</p>
                </div>

                {/* Ingestion Service */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-900">Ingestion Service</h4>
                    <span className={getStatusColor(health.services.ingestionService.status)}>
                      {getStatusIcon(health.services.ingestionService.status)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">Demo File Processing</p>
                </div>

                {/* Analysis Service */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-900">Analysis Service</h4>
                    <span className={getStatusColor(health.services.analysisService.status)}>
                      {getStatusIcon(health.services.analysisService.status)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">Data Analysis & Insights</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="text-center mt-12">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">Get Started</h3>
          <div className="space-x-4">
            <Link href="/demos" className="btn-primary">
              Upload Demo
            </Link>
            <Link href="/analysis" className="btn-secondary">
              View Analytics
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="text-center text-gray-600">
            <p>&copy; 2025 StratagemForge. Built with Next.js and microservices architecture.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}