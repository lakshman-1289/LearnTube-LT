import mongoose from 'mongoose';

async function testMongoDBConnection() {
  console.log('🔍 Testing MongoDB Connection...\n');
  
  // Check if MONGODB_URI is set
  console.log('1️⃣ Checking environment variables:');
  console.log('MONGODB_URI:', process.env.MONGODB_URI ? '✅ Set' : '❌ Not set');
  console.log('NEXTAUTH_SECRET:', process.env.NEXTAUTH_SECRET ? '✅ Set' : '❌ Not set');
  
  if (!process.env.MONGODB_URI) {
    console.log('\n💡 To fix this, create a .env.local file with:');
    console.log('MONGODB_URI=mongodb://localhost:27017/learntube');
    console.log('NEXTAUTH_SECRET=your-secret-key-here');
    console.log('OPENROUTER_API_KEY=your-openrouter-key-here');
    return;
  }
  
  try {
    console.log('\n2️⃣ Attempting to connect to MongoDB...');
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('✅ MongoDB connection successful!');
    
    // Test database operations
    console.log('\n3️⃣ Testing database operations...');
    
    // Test creating a simple document
    const TestSchema = new mongoose.Schema({
      test: String,
      timestamp: { type: Date, default: Date.now }
    });
    
    const TestModel = mongoose.model('Test', TestSchema);
    const testDoc = new TestModel({ test: 'connection-test' });
    await testDoc.save();
    console.log('✅ Document creation successful!');
    
    // Test reading
    const found = await TestModel.findOne({ test: 'connection-test' });
    console.log('✅ Document reading successful!');
    
    // Clean up
    await TestModel.deleteOne({ test: 'connection-test' });
    console.log('✅ Document deletion successful!');
    
    console.log('\n🎉 All MongoDB operations working correctly!');
    
  } catch (error) {
    console.log('❌ MongoDB connection failed:', error.message);
    console.log('\n💡 Possible solutions:');
    console.log('1. Make sure MongoDB is running locally');
    console.log('2. Check your MONGODB_URI in .env.local');
    console.log('3. If using MongoDB Atlas, ensure your IP is whitelisted');
  } finally {
    if (mongoose.connection.readyState === 1) {
      await mongoose.disconnect();
      console.log('🔌 MongoDB connection closed');
    }
  }
}

testMongoDBConnection(); 