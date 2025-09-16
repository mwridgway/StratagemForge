import { NextRequest, NextResponse } from 'next/server';

const BFF_URL = process.env.BFF_SERVICE_URL || 'http://bff:8080';

export async function POST(request: NextRequest) {
  try {
    console.log('Upload route: Using BFF URL:', BFF_URL);
    // Get the form data from the request
    const formData = await request.formData();
    
    // Forward the request to the BFF service
    const response = await fetch(`${BFF_URL}/api/demos/upload`, {
      method: 'POST',
      body: formData,
      headers: {
        // Don't set Content-Type header - let fetch set it with boundary for multipart/form-data
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Upload proxy error:', error);
    return NextResponse.json(
      { 
        error: 'Failed to upload demo file',
        details: 'An unexpected error occurred'
      },
      { status: 500 }
    );
  }
}