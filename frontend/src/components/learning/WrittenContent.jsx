import QuizSection from "./QuizSection";

export default function WrittenContent({ selectedLesson, showQuiz, setShowQuiz, isDarkTheme }) {
  return (
    <div className={`prose max-w-none ${isDarkTheme ? 'prose-invert' : 'prose-gray'}`}>
      {/* Introduction */}
      <div className="mb-8">
        <h2 className={`text-2xl font-bold mb-4 ${isDarkTheme ? 'text-white' : 'text-gray-900'}`}>Introduction</h2>
        <p className={`leading-relaxed ${isDarkTheme ? 'text-gray-300' : 'text-gray-700'}`}>{selectedLesson.content.introduction}</p>
      </div>

      {/* Content Sections */}
      {selectedLesson.content.sections.map((section, index) => (
        <div key={index} className="mb-8">
          <h2 className={`text-2xl font-bold mb-4 ${isDarkTheme ? 'text-white' : 'text-gray-900'}`}>{section.title}</h2>
          {section.points.map((point, pointIndex) => (
            <div key={pointIndex} className="mb-6">
              <h3 className={`text-lg font-semibold mb-2 ${isDarkTheme ? 'text-white' : 'text-gray-900'}`} dangerouslySetInnerHTML={{ __html: point.subtitle }}></h3>
              <p className={`leading-relaxed ${isDarkTheme ? 'text-gray-300' : 'text-gray-700'}`}>{point.content}</p>
            </div>
          ))}
        </div>
      ))}

      {/* Conclusion */}
      {selectedLesson.content.conclusion && (
        <div className="mb-8">
          <h2 className={`text-2xl font-bold mb-4 ${isDarkTheme ? 'text-white' : 'text-gray-900'}`}>Conclusion</h2>
          <p className={`leading-relaxed ${isDarkTheme ? 'text-gray-300' : 'text-gray-700'}`}>{selectedLesson.content.conclusion}</p>
        </div>
      )}

      {/* Quizzes */}
      {selectedLesson.quizzes && selectedLesson.quizzes.length > 0 && (
        <div className="space-y-6">
          {selectedLesson.quizzes.map((quiz, index) => (
            <QuizSection 
              key={quiz.id}
              quiz={quiz}
              index={index}
              showQuiz={showQuiz}
              setShowQuiz={setShowQuiz}
              isDarkTheme={isDarkTheme}
            />
          ))}
        </div>
      )}
    </div>
  );
} 