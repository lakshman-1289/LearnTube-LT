"use client";
import { useSession } from "next-auth/react";

export default function ProfilePage() {
  const { data: session } = useSession();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded shadow-md w-full max-w-md">
        <h1 className="text-2xl font-bold mb-4">Profile</h1>
        {session ? (
          <div className="flex flex-col items-center">
            <img
              src={session.user.image || "/default-avatar.svg"}
              onError={e => { e.target.onerror = null; e.target.src = "/default-avatar.svg"; }}
              alt="Profile"
              className="w-20 h-20 rounded-full mb-4 border"
            />
            <div className="text-lg font-semibold mb-1">{session.user.name || "No Name"}</div>
            <div className="text-gray-600 mb-2">{session.user.email}</div>
            <div className="text-sm text-gray-400">User ID: {session.user.id}</div>
          </div>
        ) : (
          <div className="text-lg text-gray-600">You are not logged in.</div>
        )}
      </div>
    </div>
  );
} 