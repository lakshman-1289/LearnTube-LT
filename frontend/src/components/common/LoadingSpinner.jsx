export default function LoadingSpinner({ isDarkTheme }) {
  return (
    <div className={`font-inter transition-colors duration-300 ${isDarkTheme ? 'bg-gray-900 text-white' : 'bg-white text-gray-900'}`}>
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className={`text-lg ${isDarkTheme ? 'text-gray-300' : 'text-gray-600'}`}>Loading course content...</p>
        </div>
      </div>
    </div>
  );
} 