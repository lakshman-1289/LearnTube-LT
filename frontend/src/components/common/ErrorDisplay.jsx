export default function ErrorDisplay({ error, isDarkTheme }) {
  return (
    <div className={`font-inter transition-colors duration-300 ${isDarkTheme ? 'bg-gray-900 text-white' : 'bg-white text-gray-900'}`}>
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className={`text-2xl font-bold mb-2 ${isDarkTheme ? 'text-white' : 'text-gray-900'}`}>Error Loading Course</h2>
          <p className={`mb-4 ${isDarkTheme ? 'text-gray-300' : 'text-gray-600'}`}>{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
          >
            Try Again
          </button>
        </div>
      </div>
    </div>
  );
} 