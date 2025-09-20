import { NextResponse } from 'next/server';

export async function GET(): Promise<NextResponse> {
  return NextResponse.json({
    message: 'Test API route is working',
    timestamp: new Date().toISOString()
  });
}
