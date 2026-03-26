import ThemeToggle from "@/components/common/ThemeToggle";

export default function NavigationBar({ isDarkTheme, setIsDarkTheme }) {
  return (
    <nav className={`flex items-center justify-between px-8 py-4 border-b sticky top-0 z-50 transition-colors duration-300 ${
      isDarkTheme 
        ? 'bg-gray-800/80 backdrop-blur-sm border-gray-700 shadow-lg' 
        : 'bg-white border-gray-200 shadow-sm'
    }`}>
      <div className="flex items-center space-x-4">
        <div className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent select-none">
          LearnTube
        </div>
      </div>
      <div className="flex items-center space-x-4">
        <ThemeToggle isDarkTheme={isDarkTheme} setIsDarkTheme={setIsDarkTheme} />
      </div>
    </nav>
  );
} 