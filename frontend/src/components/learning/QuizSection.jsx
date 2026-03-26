import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";

export default function QuizSection({ quiz, index, showQuiz, setShowQuiz, isDarkTheme }) {
  return (
    <Card isDarkTheme={isDarkTheme} className="p-6">
      <h3 className={`text-xl font-bold mb-4 ${isDarkTheme ? 'text-white' : 'text-gray-900'}`}>
        🧑‍💻 Test yourself - Question {index + 1}
      </h3>
      <div className="mb-4">
        <p className={`mb-2 ${isDarkTheme ? 'text-gray-300' : 'text-gray-700'}`}>
          {index + 1}. 📕 {quiz.question}
        </p>
        {quiz.type === "multiple_choice" && quiz.options && (
          <div className="space-y-2 mt-4">
            {quiz.options.map((option, optionIndex) => (
              <div key={optionIndex} className="flex items-center space-x-2">
                <input
                  type="radio"
                  name={`quiz-${quiz.id}`}
                  id={`option-${quiz.id}-${optionIndex}`}
                  className="text-blue-600"
                />
                <label htmlFor={`option-${quiz.id}-${optionIndex}`} className={`text-sm ${isDarkTheme ? 'text-gray-300' : 'text-gray-700'}`}>
                  {option}
                </label>
              </div>
            ))}
          </div>
        )}
      </div>
      <Button 
        onClick={() => setShowQuiz(!showQuiz)}
        variant="primary"
        size="md"
      >
        {showQuiz ? "Hide Answer" : "Show Answer"}
      </Button>
      {showQuiz && (
        <div className={`mt-4 p-4 rounded-lg border ${
          isDarkTheme ? 'bg-gray-600 border-gray-500' : 'bg-white border-gray-200'
        }`}>
          <p className={isDarkTheme ? 'text-gray-300' : 'text-gray-700'}>
            {quiz.answer}
          </p>
          {quiz.explanation && (
            <p className={`mt-2 text-sm ${isDarkTheme ? 'text-gray-400' : 'text-gray-600'}`}>
              <strong>Explanation:</strong> {quiz.explanation}
            </p>
          )}
        </div>
      )}
    </Card>
  );
} 