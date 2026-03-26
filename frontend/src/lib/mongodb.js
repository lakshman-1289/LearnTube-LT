import mongoose from 'mongoose';

const { MONGODB_URI } = process.env;

global._mongoose = global._mongoose || { conn: null, promise: null };

export default async function dbConnect() {
  if (!MONGODB_URI) {
    throw new Error('MONGODB_URI not set. Please add MONGODB_URI to your .env.local file');
  }
  
  if (global._mongoose.conn) return global._mongoose.conn;
  if (!global._mongoose.promise) {
    global._mongoose.promise = mongoose.connect(MONGODB_URI, {
      bufferCommands: false,
      connectTimeoutMS: 10000
    });
  }
  global._mongoose.conn = await global._mongoose.promise;
  return global._mongoose.conn;
}
