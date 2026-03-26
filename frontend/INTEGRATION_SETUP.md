# 🚀 Course Generator Integration Setup

## Overview
This guide will help you integrate the new course generator with your Next.js frontend.

## 📋 Prerequisites

1. **Python Environment**: Make sure you have Python installed
2. **Environment Variables**: Set up your API keys
3. **Dependencies**: Install required packages

## 🔧 Setup Steps

### 1. Install Python Dependencies
```bash
cd your-project-root
pip install -r requirements.txt
```

### 2. Set Environment Variables
Create a `.env` file in your project root:
```bash
# .env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 3. Start the Python FastAPI Server
```bash
cd your-project-root
python run_test_server.py
```
This starts the server on `http://localhost:8000`

### 4. Start Your Next.js App
In a new terminal:
```bash
npm run dev
```
Your app will be available at `http://localhost:3000`

## 🧪 Testing the Integration

### Option 1: Use the Test Page
1. Go to `http://localhost:3000/test-course`
2. Enter a YouTube URL
3. Click "Generate Course"
4. View the results and click "View Course" to see it in the learning interface

### Option 2: Direct Learning Page Access
1. Go to `http://localhost:3000/learning?url=YOUR_YOUTUBE_URL`
2. Replace `YOUR_YOUTUBE_URL` with an actual YouTube URL
3. The page will automatically generate the course and display it

## 📊 Expected Flow

1. **User enters YouTube URL** → Frontend sends to `/api/generate-learning-content`
2. **API extracts transcript** → Uses Python script to get video transcript
3. **Course generation** → Sends transcript to FastAPI server
4. **AI analysis** → DeepSeek analyzes content and returns structured data
5. **Course conversion** → Converts analysis to proper course format
6. **Frontend display** → Transforms data and displays in learning interface

## 🎯 What You'll See

### Generated Course Structure
```json
{
  "courseInfo": {
    "title": "Course Title",
    "subtitle": "Course description",
    "duration": "1h 15min",
    "totalLessons": 5
  },
  "lessons": [
    {
      "id": 1,
      "title": "Lesson Title",
      "subtitle": "Lesson description",
      "videoMeta": {
        "start": "00:00:00",
        "end": "00:15:00"
      },
      "content": {
        "introduction": "Lesson introduction",
        "sections": [...],
        "conclusion": "Lesson conclusion"
      },
      "quizzes": [...]
    }
  ]
}
```

### Frontend Features
- ✅ **Video lessons** with timestamps
- ✅ **Written content** with sections and points
- ✅ **Interactive quizzes** with multiple choice questions
- ✅ **Progress tracking** through lessons
- ✅ **Dark/light theme** support
- ✅ **Responsive design** for all devices

## 🔍 Troubleshooting

### Common Issues

1. **"Failed to contact Python FastAPI server"**
   - Make sure the Python server is running on port 8000
   - Check if there are any Python errors in the terminal

2. **"Transcript extraction failed"**
   - Verify the YouTube URL is valid and accessible
   - Check if the video has captions/subtitles

3. **"Course generation failed"**
   - Verify your OpenRouter API key is correct
   - Check the Python server logs for errors

4. **Frontend not loading course data**
   - Check browser console for errors
   - Verify the API response format matches expectations

### Debug Steps

1. **Check Python server logs**:
   ```bash
   # Look for errors in the Python server terminal
   ```

2. **Check browser console**:
   ```bash
   # Open browser dev tools and check Network tab
   ```

3. **Test API directly**:
   ```bash
   curl -X POST http://localhost:8000/generate-course \
     -H "Content-Type: application/json" \
     -d '{"content": "Sample transcript content"}'
   ```

## 🎉 Success Indicators

When everything is working correctly, you should see:

1. **Python server**: "🚀 Starting Course Generator Test API..."
2. **Test page**: Course data with lessons and quizzes
3. **Learning page**: Interactive course interface with video/written content
4. **Console logs**: No errors in browser or server terminals

## 🔄 Next Steps

After successful integration:

1. **Customize the UI**: Modify the learning components to match your design
2. **Add features**: Implement additional functionality like progress saving
3. **Optimize performance**: Add caching and error handling
4. **Scale up**: Deploy to production with proper hosting

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the Python server logs
3. Test with a simple YouTube URL first
4. Verify all environment variables are set correctly 