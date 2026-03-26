import VideoPlayer from "./VideoPlayer";
import WrittenContent from "./WrittenContent";
import NavigationButtons from "./NavigationButtons";
import ProgressIndicator from "@/components/common/ProgressIndicator";

export default function LessonContent({ 
  courseInfo, 
  selectedLesson, 
  currentProgress,
  lessonType, 
  setLessonType, 
  showQuiz, 
  setShowQuiz, 
  isDarkTheme,
  videoSource
}) {
  if (!selectedLesson) {
    return (
      <div className="flex-1 p-8">
        <div className="text-center">
          <div className="text-gray-500 text-6xl mb-4">📚</div>
          <h2 className={`text-2xl font-bold mb-2 ${isDarkTheme ? 'text-white' : 'text-gray-900'}`}>Select a Lesson</h2>
          <p className={`${isDarkTheme ? 'text-gray-300' : 'text-gray-600'}`}>Choose a lesson from the sidebar to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-8">
      {/* Lesson Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className={`text-3xl font-bold mb-2 ${isDarkTheme ? 'text-white' : 'text-gray-900'}`}>
              {selectedLesson.title}
            </h1>
            <p className={`text-lg ${isDarkTheme ? 'text-gray-400' : 'text-gray-600'}`}>
              {selectedLesson.subtitle}
            </p>
          </div>
          <ProgressIndicator progress={currentProgress} isDarkTheme={isDarkTheme} />
        </div>

        {/* Video/Written Toggle */}
        <div className="flex space-x-2 mb-6">
          <button
            onClick={() => setLessonType("video")}
            className={`px-4 py-2 rounded-lg transition-all duration-200 ${
              lessonType === "video"
                ? "bg-blue-600 text-white font-medium"
                : isDarkTheme
                  ? "text-gray-300 hover:text-white hover:bg-gray-700"
                  : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            }`}
          >
            Video Lesson
          </button>
          <button
            onClick={() => setLessonType("written")}
            className={`px-4 py-2 rounded-lg transition-all duration-200 ${
              lessonType === "written"
                ? "bg-blue-600 text-white font-medium"
                : isDarkTheme
                  ? "text-gray-300 hover:text-white hover:bg-gray-700"
                  : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            }`}
          >
            Written Lesson
          </button>
        </div>
      </div>

      {/* Lesson Content */}
      <div className={`rounded-2xl p-8 border mb-8 shadow-sm transition-colors duration-300 ${
        isDarkTheme 
          ? 'bg-gray-800 border-gray-700' 
          : 'bg-white border-gray-200'
      }`}>
        {lessonType === "video" ? (
          <VideoPlayer 
            selectedLesson={selectedLesson} 
            isDarkTheme={isDarkTheme} 
            videoSource={videoSource}
          />
        ) : (
          <WrittenContent 
            selectedLesson={selectedLesson} 
            showQuiz={showQuiz}
            setShowQuiz={setShowQuiz}
            isDarkTheme={isDarkTheme}
          />
        )}
      </div>

      <NavigationButtons isDarkTheme={isDarkTheme} />
    </div>
  );
} 