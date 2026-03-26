/**
 * Extract a YouTube video ID from any valid YouTube URL.
 * Returns null if not found.
 */
export function extractVideoId(url) {
  if (typeof url !== 'string') return null;

  const rgxList = [
    /youtu\.be\/([A-Za-z0-9_-]{11})/,                 // youtu.be/VIDEO
    /youtube\.com\/shorts\/([A-Za-z0-9_-]{11})/,      // shorts
    /youtube\.com\/embed\/([A-Za-z0-9_-]{11})/,       // embed
    /[?&]v=([A-Za-z0-9_-]{11})/                       // watch?v=
  ];

  for (const rgx of rgxList) {
    const m = url.match(rgx);
    if (m) return m[1];
  }
  return null;
}

/** Normalise any YouTube URL → https://www.youtube.com/watch?v=ID */
export function normaliseYouTubeUrl(url) {
  const id = extractVideoId(url);
  return id ? `https://www.youtube.com/watch?v=${id}` : url;
}
