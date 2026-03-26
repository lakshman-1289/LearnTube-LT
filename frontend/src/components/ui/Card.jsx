export default function Card({ 
  children, 
  className = "", 
  isDarkTheme = false,
  padding = "p-6"
}) {
  const baseClasses = `rounded-lg border transition-colors duration-300 ${padding}`;
  const themeClasses = isDarkTheme 
    ? 'bg-gray-800 border-gray-700' 
    : 'bg-white border-gray-200';
  
  return (
    <div className={`${baseClasses} ${themeClasses} ${className}`}>
      {children}
    </div>
  );
} 