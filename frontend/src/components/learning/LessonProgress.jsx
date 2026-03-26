import Checkbox from "@/components/ui/Checkbox";

export default function LessonProgress({ lessons, setLessons, selectedLessonId, setSelectedLessonId, isDarkTheme }) {
  const handleLessonToggle = (lessonId) => {
    setLessons(prevLessons => 
      prevLessons.map(lesson => 
        lesson.id === lessonId 
          ? { ...lesson, completed: !lesson.completed }
          : lesson
      )
    );
  };

  const handleLessonClick = (lessonId) => {
    setSelectedLessonId(lessonId);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className={`text-lg font-semibold ${isDarkTheme ? 'text-white' : 'text-gray-900'}`}>Course Progress</h3>
        <svg className={`w-5 h-5 ${isDarkTheme ? 'text-gray-400' : 'text-gray-500'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
      <div className="space-y-3">
        {lessons.map((lesson) => (
          <div 
            key={lesson.id} 
            className={`flex items-start space-x-3 p-3 rounded-lg cursor-pointer transition-all duration-200 ${
              selectedLessonId === lesson.id
                ? isDarkTheme 
                  ? 'bg-blue-600/20 border border-blue-500/30' 
                  : 'bg-blue-50 border border-blue-200'
                : isDarkTheme
                  ? 'hover:bg-gray-700/50'
                  : 'hover:bg-gray-50'
            }`}
            onClick={() => handleLessonClick(lesson.id)}
          >
            <Checkbox 
              checked={lesson.completed}
              onChange={(e) => {
                e.stopPropagation(); // Prevent lesson selection when clicking checkbox
                handleLessonToggle(lesson.id);
              }}
              isDarkTheme={isDarkTheme}
            />
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                <span className={`text-sm font-medium ${
                  selectedLessonId === lesson.id
                    ? isDarkTheme ? 'text-blue-300' : 'text-blue-700'
                    : isDarkTheme ? 'text-white' : 'text-gray-900'
                }`}>
                  {lesson.id}. {lesson.title}
                </span>
              </div>
              <p className={`text-xs mt-1 ${
                selectedLessonId === lesson.id
                  ? isDarkTheme ? 'text-blue-200' : 'text-blue-600'
                  : isDarkTheme ? 'text-gray-400' : 'text-gray-500'
              }`}>
                {lesson.subtitle || "Lesson description"}
              </p>
              <div className="flex items-center space-x-1 mt-1">
                <svg className={`w-3 h-3 ${
                  selectedLessonId === lesson.id
                    ? isDarkTheme ? 'text-blue-300' : 'text-blue-600'
                    : isDarkTheme ? 'text-gray-500' : 'text-gray-400'
                }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className={`text-xs ${
                  selectedLessonId === lesson.id
                    ? isDarkTheme ? 'text-blue-300' : 'text-blue-600'
                    : isDarkTheme ? 'text-gray-500' : 'text-gray-400'
                }`}>{lesson.duration}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
} 