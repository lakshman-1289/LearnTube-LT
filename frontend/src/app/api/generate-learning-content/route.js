import { NextResponse } from 'next/server';

export async function POST(req) {
  try {
    const body = await req.json();
    const { url } = body;
    if (!url) {
      return NextResponse.json({ error: 'Missing YouTube URL' }, { status: 400 });
    }

    const response = await fetch('http://localhost:8000/generate-course-from-youtube', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return NextResponse.json({ 
          error: errorData.detail || errorData.error || `Backend returned status ${response.status}` 
        }, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json({ error: 'Internal server error', details: err.message }, { status: 500 });
  }
}

export async function GET() {
  return NextResponse.json({ 
    error: 'Method not allowed. Use POST instead.',
    usage: {
      method: 'POST',
      body: { 
        url: 'https://youtube.com/watch?v=VIDEO_ID'
      }
    }
  }, { status: 405 });
} 