import dotenv from 'dotenv';
import dbConnect from './src/lib/mongodb.js';
import AdminData from './src/models/AdminData.js';

// Load environment variables from .env.local
dotenv.config({ path: './.env.local' });

async function testCourseStorage() {
  try {
    console.log('🔗 Connecting to MongoDB...');
    console.log('MONGODB_URI:', process.env.MONGODB_URI ? 'Set' : 'Not set');
    
    if (!process.env.MONGODB_URI) {
      console.error('❌ MONGODB_URI not set. Please create a .env.local file with your MongoDB connection string.');
      console.log('💡 Example .env.local content:');
      console.log('MONGODB_URI=mongodb://localhost:27017/learntube');
      process.exit(1);
    }
    
    await dbConnect();
    
    console.log('📊 Checking for stored courses...');
    
    // Find all records with course data
    const coursesWithData = await AdminData.find({
      courseData: { $exists: true, $ne: null }
    }).select('videoId url courseData.courseInfo.title processingStats courseGeneratedAt');
    
    console.log(`✅ Found ${coursesWithData.length} courses with data in MongoDB`);
    
    if (coursesWithData.length > 0) {
      console.log('\n📋 Sample courses:');
      coursesWithData.slice(0, 3).forEach((course, index) => {
        console.log(`${index + 1}. Video ID: ${course.videoId}`);
        console.log(`   Title: ${course.courseData?.courseInfo?.title || 'N/A'}`);
        console.log(`   URL: ${course.url}`);
        console.log(`   Generated: ${course.courseGeneratedAt}`);
        console.log(`   Processing Time: ${course.processingStats?.processingTimeSeconds || 'N/A'}s`);
        console.log('');
      });
    } else {
      console.log('❌ No courses found with course data');
    }
    
    // Check total records
    const totalRecords = await AdminData.countDocuments();
    console.log(`📈 Total records in AdminData collection: ${totalRecords}`);
    
    // Check records with transcripts only
    const transcriptOnly = await AdminData.countDocuments({
      courseData: { $exists: false }
    });
    console.log(`📝 Records with transcripts only: ${transcriptOnly}`);
    
    // Check records with both transcript and course
    const bothData = await AdminData.countDocuments({
      courseData: { $exists: true, $ne: null },
      transcript: { $exists: true }
    });
    console.log(`🎓 Records with both transcript and course: ${bothData}`);
    
  } catch (error) {
    console.error('❌ Error testing course storage:', error);
  } finally {
    process.exit(0);
  }
}

testCourseStorage(); 