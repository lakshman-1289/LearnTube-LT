import dotenv from 'dotenv';
  import mongoose from 'mongoose';
  import bcrypt from 'bcryptjs';
  import User from './src/models/User.js';

  dotenv.config({ path: './.env.local' });

  async function createUser() {
    await mongoose.connect(process.env.MONGODB_URI);
    const hashedPassword = await bcrypt.hash('testpassword', 10);
    const user = new User({
      email: 'test@example.com',
      password: hashedPassword,
      role: 'user',
    });
    await user.save();
    console.log('User created');
    mongoose.disconnect();
  }

  createUser();