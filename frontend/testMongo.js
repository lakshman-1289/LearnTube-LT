import dotenv from 'dotenv';
import connectMongo from './src/lib/mongodb.js'; // Updated path

// Load environment variables from .env.local
dotenv.config({ path: './.env.local' });
console.log('MONGODB_URI:', process.env.MONGODB_URI); // Debug log

async function testConnection() {
  await connectMongo();
  console.log('Test completed');
}

testConnection();