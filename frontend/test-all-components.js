import fetch from 'node-fetch';

async function testAllComponents() {
  console.log('🧪 Testing All Components...\n');

  // Test 1: Environment Variables
  console.log('1️⃣ Environment Variables:');
  console.log('MONGODB_URI:', process.env.MONGODB_URI ? '✅ Set' : '❌ Not set');
  console.log('NEXTAUTH_SECRET:', process.env.NEXTAUTH_SECRET ? '✅ Set' : '❌ Not set');
  console.log('OPENROUTER_API_KEY:', process.env.OPENROUTER_API_KEY ? '✅ Set' : '❌ Not set');

  // Test 2: FastAPI Server
  console.log('\n2️⃣ FastAPI Server (Port 8000):');
  try {
    const healthResponse = await fetch('http://localhost:8000/health');
    const healthData = await healthResponse.json();
    console.log('✅ FastAPI server is running:', healthData);
  } catch (error) {
    console.log('❌ FastAPI server is not running:', error.message);
    console.log('💡 Start it with: cd your-project-root/src && python test_api_mock.py');
  }

  // Test 3: Next.js Server
  console.log('\n3️⃣ Next.js Server (Port 3000):');
  try {
    const nextResponse = await fetch('http://localhost:3000/api/generate-learning-content', {
      method: 'GET'
    });
    console.log('✅ Next.js server is running (Status:', nextResponse.status, ')');
  } catch (error) {
    console.log('❌ Next.js server is not running:', error.message);
    console.log('💡 Start it with: npm run dev');
  }

  // Test 4: Course Generation API
  console.log('\n4️⃣ Course Generation API:');
  try {
    const sampleTranscript = {
      content: "Welcome to this comprehensive Python programming course. In this tutorial, we'll start with the basics of Python programming."
    };

    const response = await fetch('http://localhost:8000/generate-course', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(sampleTranscript)
    });

    const result = await response.json();
    
    if (result.success) {
      console.log('✅ Course generation working!');
      console.log('📊 Processing stats:', result.processing_stats);
      console.log('📚 Course info:', result.course_data?.courseInfo?.title);
    } else {
      console.log('❌ Course generation failed:', result.error);
    }
  } catch (error) {
    console.log('❌ Course generation API error:', error.message);
  }

  // Test 5: Full Integration Test
  console.log('\n5️⃣ Full Integration Test:');
  try {
    const integrationResponse = await fetch('http://localhost:3000/api/generate-learning-content', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
      })
    });

    const integrationResult = await integrationResponse.json();
    
    if (integrationResult.success) {
      console.log('✅ Full integration working!');
      console.log('📊 Cached:', integrationResult.cached);
      console.log('📚 Course data:', !!integrationResult.course_data);
      console.log('💾 Database save:', !!integrationResult.data);
    } else {
      console.log('❌ Integration failed:', integrationResult.error);
    }
  } catch (error) {
    console.log('❌ Integration test error:', error.message);
  }

  // Summary
  console.log('\n📋 SUMMARY:');
  console.log('To fix the "Failed to save course data to database" error:');
  console.log('1. Create .env.local file with MongoDB URI');
  console.log('2. Make sure MongoDB is running');
  console.log('3. Ensure both servers are running (FastAPI + Next.js)');
  console.log('4. Check that the course generation API is working');
}

testAllComponents(); 