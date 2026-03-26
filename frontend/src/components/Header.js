"use client";
import { useSession, signOut } from "next-auth/react";

export default function Header() {
  const { data: session } = useSession();

  return (
    <header className="flex justify-between items-center p-4 border-b bg-white">
      <div className="text-xl font-bold">Learning Platform</div>
      <div>
        {session ? (
          <div className="relative group">
            <button className="rounded-full border p-1">
              <img
                src={session.user.image || "/default-avatar.svg"}
                onError={e => { e.target.onerror = null; e.target.src = "/default-avatar.svg"; }}
                alt="Profile"
                className="w-8 h-8 rounded-full"
              />
            </button>
            <div className="absolute right-0 mt-2 w-48 bg-white border rounded shadow-lg hidden group-hover:block z-10">
              <div className="p-4">
                <div className="font-semibold">{session.user.name}</div>
                <div className="text-sm text-gray-500">{session.user.email}</div>
              </div>
              <button
                className="w-full text-left px-4 py-2 hover:bg-gray-100"
                onClick={() => signOut()}
              >
                Sign out
              </button>
            </div>
          </div>
        ) : (
          <a href="/api/auth/signin" className="btn">Sign In</a>
        )}
      </div>
    </header>
  );
} 