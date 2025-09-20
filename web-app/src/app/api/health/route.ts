import { NextResponse } from 'next/server';

export async function GET(): Promise<NextResponse> {
  try {
    const bffServiceUrl = process.env.BFF_SERVICE_URL || 'http://localhost:8090';
    console.log('Fetching health from:', bffServiceUrl);

    // During build time, return mock health data
    if (process.env.NODE_ENV === 'production' && !process.env.BFF_SERVICE_URL) {
      return NextResponse.json({
        status: 'healthy',
        service: 'bff',
        version: '1.0.0',
        uptime: 0,
        timestamp: new Date().toISOString()
      });
    }

    const response = await fetch(`${bffServiceUrl}/health`);

    if (!response.ok) {
      console.error('BFF health response not ok:', response.status, response.statusText);
      return NextResponse.json(
        { error: 'Health check failed' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching health:', error);
    return NextResponse.json(
      { error: 'Health check failed' },
      { status: 500 }
    );
  }
}
