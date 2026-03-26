import connectMongo from '../../../lib/mongodb.js';
import VideoContent from '../../../models/VideoContent.js';
import { NextResponse } from 'next/server';

export async function GET() {
  await connectMongo();
  try {
    const content = new VideoContent({
      videoUrl: 'https://www.youtube.com/watch?v=test',
      title: 'Test Video',
      timestamps: [{ time: '0:00', topic: 'Test Topic' }],
      quizzes: [{ question: 'Test?', options: ['A', 'B'], correctAnswer: 'A', topic: 'Test Topic' }],
      finalExam: [{ question: 'Final?', options: ['X', 'Y'], correctAnswer: 'X' }],
    });
    await content.save();
    return NextResponse.json({ message: 'Data saved', content });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to save data' }, { status: 500 });
  }
}