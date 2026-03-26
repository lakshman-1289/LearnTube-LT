export default function NavigationButtons({ isDarkTheme }) {
  return (
    <div className="flex items-center justify-between">
      <button className={`flex items-center space-x-2 px-6 py-3 rounded-lg transition-colors duration-200 border ${
        isDarkTheme 
          ? 'bg-gray-800 text-white border-gray-700 hover:bg-gray-700' 
          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
      }`}>
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        <span>Previous lesson</span>
      </button>
      <button className="flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
        <span>Next lesson</span>
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </div>
  );
} 