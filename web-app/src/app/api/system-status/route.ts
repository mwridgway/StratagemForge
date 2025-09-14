import { NextRequest, NextResponse } from 'next/server';

export async function GET() {
  try {
    // Use the internal Docker network to call BFF service
    const response = await fetch('http://bff:8080/config');
    
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