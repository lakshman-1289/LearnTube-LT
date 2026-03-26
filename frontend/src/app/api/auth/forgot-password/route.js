import { NextResponse } from 'next/server';
import nodemailer from 'nodemailer';
import connectMongo from '@/lib/mongodb';
import User from '@/models/User';
import crypto from 'crypto';

export async function POST(req) {
  const { email } = await req.json();
  await connectMongo();

  const user = await User.findOne({ email });
  if (!user) {
    return NextResponse.json({ message: 'User not found' }, { status: 404 });
  }

  const token = crypto.randomBytes(32).toString('hex');
  user.resetToken = token;
  user.resetTokenExpiry = Date.now() + 3600000; // 1 hour
  await user.save();

  const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
      user: process.env.EMAIL_USER,
      pass: process.env.EMAIL_PASS,
    },
  });

  const resetLink = `${process.env.NEXTAUTH_URL}/reset-password?token=${token}`;

  await transporter.sendMail({
    to: email,
    from: process.env.EMAIL_USER,
    subject: 'Password Reset Request',
    html: `<p>Click the link below to reset your password:</p><a href="${resetLink}">${resetLink}</a>`,
  });

  return NextResponse.json({ message: 'Reset link sent to your email' });
}
