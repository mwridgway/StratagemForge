import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const bffServiceUrl = 'http://bff:8080';
    console.log('Fetching health from:', bffServiceUrl);
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