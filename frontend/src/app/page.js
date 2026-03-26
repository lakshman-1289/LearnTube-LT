'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function HomePage() {
  const [url, setUrl] = useState('')
  const router = useRouter()

  const handleSubmit = (e) => {
    e.preventDefault()
    if (url) {
      router.push(`/learning?url=${encodeURIComponent(url)}`)
    }
  }

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Navbar */}
      <nav className="flex items-center justify-between px-6 py-4 bg-white shadow-md">
        <div className="text-xl font-bold text-blue-600">LearnTube</div>
      </nav>

      {/* Main Content */}
      <main className="flex-grow px-4 py-10 flex flex-col items-center">
        {/* Title Section */}
        <h1 className="text-4xl md:text-5xl font-extrabold text-center bg-gradient-to-r from-pink-500 to-blue-500 text-transparent bg-clip-text">
         Unlock Knowledge from Youtube videos
        </h1>

        <p className="text-center text-gray-600 mt-4 max-w-2xl">
          Paste a YouTube video link below and LearnTube will extract transcripts, summaries, and generate quizzes to test your understanding.
        </p>

        {/* Converter Card */}
        <div className="bg-white shadow-lg rounded-xl p-6 mt-10 w-full max-w-2xl border">
          {/* Title with icon */}
          <div className="flex items-center gap-2 text-gray-800 text-lg font-semibold mb-4">
            <span>⚙️</span>
            <span>LearnTube </span>
          </div>

          {/* Subtitle */}
          <h2 className="text-2xl font-bold text-gray-900 mb-1">Convert YouTube to Text </h2>
          <p className="text-gray-600 mb-6">
            Enter any YouTube URL to generate the content, quizzes, and mock tests.
          </p>

          {/* Download Settings */}
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2 text-gray-800 font-semibold text-md">
              <span>⬇️</span>
              <span>Generate Settings</span>
            </div>
            <p className="text-sm text-gray-600 mb-2">
              Enter a YouTube URL and click generate.
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
            className="mt-4 w-full bg-red-400 hover:bg-red-500 text-white font-semibold py-2 px-4 rounded-lg transition"
          >
           Generate
          </button>
        </div>
      </main>
    </div>
  )
}
