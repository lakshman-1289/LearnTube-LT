import mongoose from 'mongoose';

const VideoContentSchema = new mongoose.Schema({
  videoUrl: { type: String, required: true },
  title: { type: String, required: true },
  timestamps: [{ time: String, topic: String }],
  quizzes: [{ question: String, options: [String], correctAnswer: String, topic: String }],
  finalExam: [{ question: String, options: [String], correctAnswer: String }],
  transcript: { type: String, default: '' }, // New field for transcript
  createdAt: { type: Date, default: Date.now },
});

export default mongoose.models.VideoContent || mongoose.model('VideoContent', VideoContentSchema);