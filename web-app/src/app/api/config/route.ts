import { NextResponse } from 'next/server';

export async function GET(): Promise<NextResponse> {
  try {
    // Use environment variable or fallback for different environments
    const bffServiceUrl = process.env.BFF_SERVICE_URL || 'http://localhost:8090';
    console.log('Fetching config from:', bffServiceUrl);

    // During build time, return mock data instead of making actual requests
    if (process.env.NODE_ENV === 'production' && !process.env.BFF_SERVICE_URL) {
      return NextResponse.json({
        service: 'bff',
        version: '1.0.0',
        environment: 'build-time',
        uptime: 0,
        services: {
          userService: 'http://localhost:8091',
          ingestionService: 'http://localhost:8093',
          analysisService: 'http://localhost:8092'
        }
      });
    }

    const response = await fetch(`${bffServiceUrl}/config`);

    if (!response.ok) {
      console.error('BFF response not ok:', response.status, response.statusText);
      return NextResponse.json(
        { error: 'Failed to fetch configuration' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching config:', error);
    return NextResponse.json(
      { error: 'Failed to fetch configuration' },
      { status: 500 }
    );
  }
}
