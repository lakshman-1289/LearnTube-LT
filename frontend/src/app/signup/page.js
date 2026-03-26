'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { FcGoogle } from 'react-icons/fc';
import { signIn } from 'next-auth/react';

export default function Signup() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();
      if (!res.ok) {
        setError(data.error || 'Something went wrong');
        return;
      }

      router.push('/login');
    } catch (err) {
      setError('Failed to sign up');
    }
  };

  const handleGoogleSignUp = async () => {
    await signIn('google', { callbackUrl: '/' });
  };

  return (
    <div className="min-h-screen bg-[#0d1117] flex items-center justify-center p-4">
      <div className="bg-[#161b22] text-white rounded-lg shadow-lg w-full max-w-md p-8">
        <div className="flex justify-center mb-6">
          <svg
            height="32"
            className="fill-white"
            viewBox="0 0 16 16"
            width="32"
            aria-hidden="true"
          >
            <path d="M8 0C3.58 0 0 3.58 0 8a8 8 0 005.47 7.59c.4.07.55-.17.55-.38 
            0-.19-.01-.82-.01-1.49-2 .37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13
            -.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 
            2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 
            0-.87.31-1.59.82-2.15-.08-.2-.36-1.01.08-2.11 0 0 .67-.21 
            2.2.82a7.54 7.54 0 012 0c1.53-1.03 2.2-.82 2.2-.82.44 
            1.1.16 1.91.08 2.11.51.56.82 1.27.82 2.15 
            0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 
            0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 
            8.01 0 0016 8c0-4.42-3.58-8-8-8z" />
          </svg>
        </div>
        <h2 className="text-2xl font-semibold text-center mb-4">Create your LearnTube account</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm text-gray-300">Email address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full p-3 bg-[#0d1117] border border-[#30363d] text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600"
              placeholder="you@example.com"
              required
            />
          </div>
          <div>
            <label className="text-sm text-gray-300">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full p-3 bg-[#0d1117] border border-[#30363d] text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600"
              placeholder="••••••••"
              required
            />
          </div>
          {error && <p className="text-red-500 text-sm text-center">{error}</p>}
          <button
            type="submit"
            className="w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded-md transition duration-300"
          >
            Sign Up
          </button>
        </form>

        <div className="my-4 flex items-center justify-center">
          <div className="border-t border-gray-600 w-full"></div>
          <span className="mx-3 text-sm text-gray-400">or</span>
          <div className="border-t border-gray-600 w-full"></div>
        </div>

        <button
          onClick={handleGoogleSignUp}
          className="w-full flex items-center justify-center gap-2 bg-white text-black py-2 rounded-md hover:bg-gray-100 transition"
        >
          <FcGoogle size={20} />
          Sign up with Google
        </button>

        <p className="mt-6 text-center text-sm text-gray-400">
          Already have an account?{' '}
          <Link href="/login" className="text-blue-500 hover:underline">
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}
