import Card from "@/components/ui/Card";
import Checkbox from "@/components/ui/Checkbox";
import LessonProgress from "./LessonProgress";

function getProgressPercent(lessons) {
  if (!lessons || lessons.length === 0) return 0;
  const completed = lessons.filter(l => l.completed).length;
  return Math.round((completed / lessons.length) * 100);
}

export default function CourseSidebar({ courseOverview, lessons, setLessons, selectedLessonId, setSelectedLessonId, isDarkTheme }) {
  const percent = getProgressPercent(lessons);
  return (
    <div className={`w-80 min-h-screen p-6 border-l transition-colors duration-300 ${
      isDarkTheme ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
    }`}>
      <div className="h-screen overflow-y-auto pr-2 space-y-6">
        {/* Course Progress Bar */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-1">
            <span className={`text-xs uppercase tracking-wide ${isDarkTheme ? 'text-gray-400' : 'text-gray-500'}`}>Course Progress</span>
            <span className={`text-xs font-semibold ${isDarkTheme ? 'text-gray-300' : 'text-gray-700'}`}>{percent}%</span>
          </div>
          <div className={`w-full h-2 rounded bg-gray-700/70 relative`}>
            <div
              className="h-2 rounded bg-green-500 transition-all duration-300"
              style={{ width: `${percent}%` }}
            ></div>
          </div>
        </div>

        {/* Course Progress (Lesson List) */}
        <LessonProgress 
          lessons={lessons} 
          setLessons={setLessons}
          selectedLessonId={selectedLessonId}
          setSelectedLessonId={setSelectedLessonId}
          isDarkTheme={isDarkTheme} 
        />
      </div>
    </div>
  );
} 