"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function TestCoursePage() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('/api/generate-learning-content', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to generate course');
      }

      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleViewCourse = () => {
    if (url) {
      router.push(`/learning?url=${encodeURIComponent(url)}`);
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Navbar */}
      <nav className="flex items-center justify-between px-6 py-4 bg-white shadow-md">
        <div className="text-xl font-bold text-blue-600">LearnTube</div>
        <div className="space-x-4">
          <Link href="/login" className="text-sm font-medium text-gray-700 hover:text-blue-600">
            Sign In
          </Link>
          <Link href="/signup" className="text-sm font-medium text-white bg-blue-600 px-4 py-2 rounded hover:bg-blue-700">
            Sign Up
          </Link>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-grow px-4 py-10 flex flex-col items-center">
        {/* Title Section */}
        <h1 className="text-4xl md:text-5xl font-extrabold text-center bg-gradient-to-r from-pink-500 to-blue-500 text-transparent bg-clip-text">
          Course Generation Test
        </h1>

        <p className="text-center text-gray-600 mt-4 max-w-2xl">
          Test the course generation functionality by pasting a YouTube video link below. LearnTube will extract transcripts, summaries, and generate quizzes.
        </p>

        {/* Error Display */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mt-6 max-w-2xl w-full">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Success Display */}
        {result && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mt-6 max-w-2xl w-full">
            <strong>Success!</strong> Course generated successfully.
            <button
              onClick={handleViewCourse}
              className="ml-4 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
            >
              View Course
            </button>
          </div>
        )}

        {/* Converter Card */}
        <div className="bg-white shadow-lg rounded-xl p-6 mt-10 w-full max-w-2xl border">
          {/* Title with icon */}
          <div className="flex items-center gap-2 text-gray-800 text-lg font-semibold mb-4">
            <span>⚙️</span>
            <span>LearnTube Test</span>
          </div>

          {/* Subtitle */}
          <h2 className="text-2xl font-bold text-gray-900 mb-1">Generate Course from YouTube</h2>
          <p className="text-gray-600 mb-6">
            Enter any YouTube URL to test course generation with transcripts, quizzes, and mock tests.
          </p>

          {/* Generation Settings */}
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2 text-gray-800 font-semibold text-md">
              <span>⬇️</span>
              <span>Generation Settings</span>
            </div>
            <p className="text-sm text-gray-600 mb-2">
              Enter a YouTube URL and click generate to test the course creation process.
            </p>

            <label className="block text-sm font-medium text-gray-700 mb-1">
              YouTube URL
            </label>
            <input
              type="url"
              placeholder="https://www.youtube.com/watch?v=..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              required
            />
          </div>

          {/* Submit Button */}
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="mt-4 w-full bg-red-400 hover:bg-red-500 disabled:opacity-50 text-white font-semibold py-2 px-4 rounded-lg transition"
          >
            {loading ? "Generating..." : "Generate Course"}
          </button>
        </div>

        {/* Results Display */}
        {result && (
          <div className="bg-white shadow-lg rounded-xl p-6 mt-6 w-full max-w-4xl border">
            <h2 className="text-xl font-bold mb-4 text-gray-900">Generated Course Data:</h2>
            <div className="grid md:grid-cols-2 gap-4 mb-4">
              <div className="bg-gray-50 p-3 rounded">
                <strong className="text-gray-700">Course Title:</strong> 
                <p className="text-gray-900">{result.course_data?.courseInfo?.title}</p>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <strong className="text-gray-700">Total Lessons:</strong> 
                <p className="text-gray-900">{result.course_data?.courseInfo?.totalLessons}</p>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <strong className="text-gray-700">Duration:</strong> 
                <p className="text-gray-900">{result.course_data?.courseInfo?.duration}</p>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <strong className="text-gray-700">Processing Time:</strong> 
                <p className="text-gray-900">{result.processing_stats?.processing_time_seconds}s</p>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <strong className="text-gray-700">Lessons Generated:</strong> 
                <p className="text-gray-900">{result.processing_stats?.lessons_generated}</p>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <strong className="text-gray-700">Total Quizzes:</strong> 
                <p className="text-gray-900">{result.processing_stats?.total_quizzes}</p>
              </div>
            </div>
            
            <details className="mt-4">
              <summary className="cursor-pointer font-semibold text-gray-700 hover:text-gray-900">View Full JSON Response</summary>
              <pre className="mt-2 bg-gray-100 p-4 rounded text-sm overflow-auto max-h-96 text-gray-800">
                {JSON.stringify(result, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </main>
    </div>
  );
}