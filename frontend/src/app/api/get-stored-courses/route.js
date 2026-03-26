import { NextResponse } from 'next/server';
import dbConnect from '../../../lib/mongodb.js';
import AdminData from '../../../models/AdminData.js';

export async function GET(req) {
  try {
    await dbConnect();
    
    // Get URL parameters
    const { searchParams } = new URL(req.url);
    const videoId = searchParams.get('videoId');
    const limit = parseInt(searchParams.get('limit')) || 10;
    const page = parseInt(searchParams.get('page')) || 1;
    
    let query = {};
    
    // If videoId is provided, get specific course
    if (videoId) {
      query.videoId = videoId;
    }
    
    // Only get records that have course data
    query.courseData = { $exists: true, $ne: null };
    
    const skip = (page - 1) * limit;
    
    const courses = await AdminData.find(query)
      .select('videoId url title courseData.courseInfo processingStats courseGeneratedAt')
      .sort({ courseGeneratedAt: -1 })
      .skip(skip)
      .limit(limit);
    
    const total = await AdminData.countDocuments(query);
    
    return NextResponse.json({
      success: true,
      data: courses,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit)
      }
    });
  } catch (error) {
    console.error('Error fetching stored courses:', error);
    return NextResponse.json({ 
      error: 'Failed to fetch courses', 
      details: error.message 
    }, { status: 500 });
  }
}

export async function POST(req) {
  return NextResponse.json({ 
    error: 'Method not allowed. Use GET instead.',
    usage: {
      method: 'GET',
      queryParams: {
        videoId: 'optional - specific video ID',
        limit: 'optional - number of results (default: 10)',
        page: 'optional - page number (default: 1)'
      }
    }
  }, { status: 405 });
} 