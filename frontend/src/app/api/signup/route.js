import connectMongo from '../../../lib/mongodb.js';
  import User from '../../../models/User.js';
  import bcrypt from 'bcryptjs';

  export async function POST(req) {
    try {
      await connectMongo();
      const { email, password } = await req.json();

      if (!email || !password) {
        return new Response(JSON.stringify({ error: 'Email and password are required' }), {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        });
      }

      const existingUser = await User.findOne({ email });
      if (existingUser) {
        return new Response(JSON.stringify({ error: 'User already exists' }), {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        });
      }

      const hashedPassword = await bcrypt.hash(password, 10);
      const user = new User({
        email,
        password: hashedPassword,
        role: 'user',
      });
      await user.save();

      return new Response(JSON.stringify({ message: 'User created successfully' }), {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
        });
    } catch (error) {
      console.error('Signup error:', error);
      return new Response(JSON.stringify({ error: 'Internal server error' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      });
    }
  }