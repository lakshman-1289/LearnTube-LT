export default function Checkbox({ 
  checked, 
  onChange, 
  isDarkTheme = false,
  className = ""
}) {
  const baseClasses = "mt-1 w-4 h-4 border-2 rounded flex-shrink-0 transition-colors duration-200";
  const themeClasses = checked
    ? 'bg-green-500 border-green-500'
    : isDarkTheme 
      ? 'border-gray-500 hover:border-gray-400' 
      : 'border-gray-400 hover:border-gray-500';
  
  return (
    <button
      onClick={onChange}
      className={`${baseClasses} ${themeClasses} ${className}`}
    >
      {checked && (
        <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
      )}
    </button>
  );
} 