import mongoose from 'mongoose';

const AdminSchema = new mongoose.Schema({
  videoId:   { type: String, required: true, index: true },
  language:  { type: String, default: 'en' },
  url:       { type: String, required: true },
  title:     { type: String },
  duration:  { type: String },
  transcript:{ cleanText: String, chunks: Array },
  source:    { type: String, default: 'youtube-timedtext' },
  fetchedAt: { type: Date,   default: Date.now },
  // Course data fields
  courseData: {
    courseInfo: {
      title: String,
      description: String,
      totalLessons: Number,
      estimatedDuration: String,
      difficulty: String
    },
    lessons: [{
      id: String,
      title: String,
      content: String,
      duration: String,
      timestamp: String,
      quizzes: [{
        question: String,
        options: [String],
        correctAnswer: String,
        explanation: String
      }]
    }],
    finalExam: [{
      question: String,
      options: [String],
      correctAnswer: String,
      explanation: String
    }]
  },
  processingStats: {
    processingTimeSeconds: Number,
    inputTokens: Number,
    outputSizeKb: Number,
    lessonsGenerated: Number,
    totalQuizzes: Number
  },
  courseGeneratedAt: { type: Date, default: Date.now }
});

export default mongoose.models.AdminData
  || mongoose.model('AdminData', AdminSchema);
