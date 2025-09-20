import { NextResponse } from 'next/server';

export async function GET(): Promise<NextResponse> {
  try {
    // Use environment variable or fallback
    const bffServiceUrl = process.env.BFF_SERVICE_URL || 'http://localhost:8090';

    // During build time, return mock system status
    if (process.env.NODE_ENV === 'production' && !process.env.BFF_SERVICE_URL) {
      return NextResponse.json({
        bff: {
          status: 'healthy',
          service: 'bff',
          version: '1.0.0',
          uptime: 0
        },
        services: {
          userService: { status: 'healthy', service: 'user-service' },
          ingestionService: { status: 'healthy', service: 'ingestion-service' },
          analysisService: { status: 'healthy', service: 'analysis-service' }
        }
      });
    }

    const response = await fetch(`${bffServiceUrl}/config`);

    if (!response.ok) {
      console.error('BFF service returned error:', response.status, response.statusText);
      return NextResponse.json(
        { error: 'Failed to fetch configuration from BFF service' },
        { status: response.status }
      );
    }

    const configData = await response.json();

    // Transform the config data to match our health data structure
    const healthData = {
      bff: {
        status: 'healthy',
        service: configData.service || 'bff',
        version: configData.version,
        uptime: configData.uptime
      },
      services: {
        userService: {
          status: 'healthy',
          service: 'user-service'
        },
        ingestionService: {
          status: 'healthy',
          service: 'ingestion-service'
        },
        analysisService: {
          status: 'healthy',
          service: 'analysis-service'
        }
      }
    };

    return NextResponse.json(healthData);
  } catch (error) {
    console.error('Error fetching system status:', error);
    return NextResponse.json(
      { error: 'Failed to fetch system status' },
      { status: 500 }
    );
  }
}
