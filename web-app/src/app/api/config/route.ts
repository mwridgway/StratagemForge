import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const bffServiceUrl = 'http://bff:8080';
    console.log('Fetching config from:', bffServiceUrl);
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