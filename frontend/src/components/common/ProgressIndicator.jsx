export default function ProgressIndicator({ progress, isDarkTheme }) {
  return (
    <div className="text-right">
      <div className="text-2xl font-bold text-blue-400">{progress}</div>
      <div className="text-sm text-gray-500">Progress</div>
    </div>
  );
} 