export default function VideoPlayer({ selectedLesson, isDarkTheme, videoSource }) {
  // Use course-level videoSource.url
  const videoUrl = videoSource?.url || "https://www.youtube.com/watch?v=W6NZfCO5SIk";

  // Extract video ID from YouTube URL
  const getVideoId = (url) => {
    if (!url) return "W6NZfCO5SIk";
    const match = url.match(/(?:youtube\.com\/embed\/|youtu\.be\/|youtube\.com\/watch\?v=)([^&\n?#]+)/);
    return match ? match[1] : "W6NZfCO5SIk";
  };

  // Convert HH:MM:SS to seconds
  const timeToSeconds = (t) => {
    if (!t) return 0;
    const parts = t.split(":").map(Number);
    if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
    if (parts.length === 2) return parts[0] * 60 + parts[1];
    return Number(parts[0]) || 0;
  };

  const videoId = getVideoId(videoUrl);
  let embedUrl = `https://www.youtube.com/embed/${videoId}?rel=0&modestbranding=1&enablejsapi=1`;

  // Add start/end if present in lesson.videoMeta
  if (selectedLesson?.videoMeta) {
    const start = timeToSeconds(selectedLesson.videoMeta.start);
    const end = timeToSeconds(selectedLesson.videoMeta.end);
    if (start) embedUrl += `&start=${start}`;
    if (end) embedUrl += `&end=${end}`;
  }

  return (
    <div>
      <div className={`aspect-video rounded-lg mb-6 overflow-hidden ${
        isDarkTheme ? 'bg-gray-700' : 'bg-gray-100'
      }`}>
        <iframe
          src={embedUrl}
          title={selectedLesson?.title || "Video Lesson"}
          className="w-full h-full"
          frameBorder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowFullScreen
          loading="lazy"
        ></iframe>
      </div>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className={`text-lg font-semibold ${isDarkTheme ? 'text-white' : 'text-gray-900'}`}>
            {selectedLesson?.title || "Video Lesson"}
          </h3>
          <span className={`text-sm ${isDarkTheme ? 'text-gray-400' : 'text-gray-600'}`}>
            {selectedLesson?.duration || "10 min"}
          </span>
        </div>
        <p className={`text-sm leading-relaxed ${isDarkTheme ? 'text-gray-300' : 'text-gray-700'}`}>
          {selectedLesson?.subtitle || "Follow along with this video lesson to learn the concepts step by step."}
        </p>
        <div className={`p-4 rounded-lg ${isDarkTheme ? 'bg-gray-700' : 'bg-gray-50'}`}>
          <h4 className={`font-medium mb-2 ${isDarkTheme ? 'text-white' : 'text-gray-900'}`}>Video Summary</h4>
          <ul className={`text-sm space-y-1 ${isDarkTheme ? 'text-gray-300' : 'text-gray-700'}`}>
            <li>• Watch the complete video segment to understand the concepts</li>
            <li>• Take notes on important points</li>
            <li>• Practice the examples shown in the video</li>
            <li>• Complete the quiz after watching</li>
          </ul>
        </div>
        <div className={`text-center p-3 rounded-lg ${isDarkTheme ? 'bg-gray-800' : 'bg-gray-100'}`}>
          <p className={`text-sm ${isDarkTheme ? 'text-gray-400' : 'text-gray-600'}`}>
            If the video doesn't load, you can watch it on 
            <a 
              href={`https://www.youtube.com/watch?v=${videoId}`} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-500 hover:text-blue-600 ml-1 underline"
            >
              YouTube
            </a>
          </p>
        </div>
      </div>
    </div>
  );
} 