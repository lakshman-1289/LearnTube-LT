import fetch from 'node-fetch';

async function testCourseGeneration() {
  console.log('🧪 Testing Course Generation...\n');

  // Test 1: Check if FastAPI server is running
  console.log('1️⃣ Testing FastAPI server health...');
  try {
    const healthResponse = await fetch('http://localhost:8000/health');
    const healthData = await healthResponse.json();
    console.log('✅ FastAPI server is running:', healthData);
  } catch (error) {
    console.log('❌ FastAPI server is not running:', error.message);
    console.log('💡 Start the FastAPI server first:');
    console.log('   cd your-project-root/src');
    console.log('   python test_api.py');
    return;
  }

  // Test 2: Test course generation with sample data
  console.log('\n2️⃣ Testing course generation with sample transcript...');
  try {
    const sampleTranscript = {
      content: "Welcome to this comprehensive Python programming course. In this tutorial, we'll start with the basics of Python programming. Python is a high-level programming language that was created by Guido van Rossum and first released in 1991. Python is known for its simplicity and readability. Let's begin with variables. In Python, you can create variables by simply assigning a value to them. For example, name equals John, age equals 25. Python supports several data types including integers, floats, strings, and booleans."
    };

    const response = await fetch('http://localhost:8000/generate-course', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(sampleTranscript)
    });

    const result = await response.json();
    
    if (result.success) {
      console.log('✅ Course generation successful!');
      console.log('📊 Processing stats:', result.processing_stats);
      console.log('📚 Course info:', result.course_data?.courseInfo);
      console.log('📖 Number of lessons:', result.course_data?.lessons?.length);
    } else {
      console.log('❌ Course generation failed:', result.error);
      console.log('\n💡 To fix this:');
      console.log('1. Set OPENROUTER_API_KEY in your environment');
      console.log('2. Or modify the Python server to use a mock response');
    }
  } catch (error) {
    console.log('❌ Error testing course generation:', error.message);
  }

  // Test 3: Test the Next.js API endpoint
  console.log('\n3️⃣ Testing Next.js API endpoint...');
  try {
    const nextResponse = await fetch('http://localhost:3000/api/generate-learning-content', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' // Sample URL
      })
    });

    const nextResult = await nextResponse.json();
    
    if (nextResult.success) {
      console.log('✅ Next.js API successful!');
      console.log('📊 Cached:', nextResult.cached);
      console.log('📚 Course data available:', !!nextResult.course_data);
    } else {
      console.log('❌ Next.js API failed:', nextResult.error);
    }
  } catch (error) {
    console.log('❌ Error testing Next.js API:', error.message);
    console.log('💡 Make sure your Next.js server is running on port 3000');
  }
}

testCourseGeneration(); 