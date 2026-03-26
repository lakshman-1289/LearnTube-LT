import axios from 'axios';

export async function fetchTimedText(videoId, lang = 'en') {
  console.log(`🔍 Attempting transcript fetch for: ${videoId}`);
  
  const endpointStrategies = [
    `https://www.youtube.com/api/timedtext?v=${videoId}&lang=${lang}&fmt=json3`,
    `https://www.youtube.com/api/timedtext?v=${videoId}&lang=${lang}&kind=asr&fmt=json3`,
    `https://www.youtube.com/api/timedtext?v=${videoId}&lang=${lang}&fmt=json3&xoaf=5&hl=en`,
    `https://www.youtube.com/api/timedtext?v=${videoId}&lang=en&fmt=json3`,
    `https://www.youtube.com/api/timedtext?v=${videoId}&lang=${lang}&fmt=vtt`,
  ];

  const headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.youtube.com/',
    'Origin': 'https://www.youtube.com'
  };

  for (const [index, url] of endpointStrategies.entries()) {
    try {
      console.log(`📡 Trying strategy ${index + 1}: ${url.substring(0, 80)}...`);
      
      const response = await axios.get(url, { 
        timeout: 10000,
        headers,
        validateStatus: (status) => status < 500
      });

      console.log(`📊 Response status: ${response.status}`);
      console.log(`📄 Response data type: ${typeof response.data}`);
      console.log(`📝 Response preview: ${JSON.stringify(response.data).substring(0, 200)}...`);

      if (response.status === 200 && response.data) {
        // Check for JSON3 format with detailed logging
        if (url.includes('fmt=json3')) {
          console.log(`🔍 JSON3 events length: ${response.data.events?.length || 0}`);
          
          if (response.data.events && response.data.events.length > 0) {
            const result = parseJson3(response.data);
            if (result.cleanText && result.cleanText.length > 10) {
              console.log(`✅ Strategy ${index + 1} SUCCESS: ${result.cleanText.length} characters`);
              return result;
            } else {
              console.log(`⚠️ JSON3 parsed but text too short: "${result.cleanText}"`);
            }
          } else {
            console.log(`❌ JSON3 response has no events array or empty events`);
          }
        }
        
        // Handle VTT format
        if (url.includes('fmt=vtt') && typeof response.data === 'string') {
          console.log(`📝 VTT content length: ${response.data.length}`);
          if (response.data.includes('WEBVTT')) {
            const result = parseVTT(response.data);
            if (result.cleanText && result.cleanText.length > 10) {
              console.log(`✅ Strategy ${index + 1} VTT SUCCESS: ${result.cleanText.length} characters`);
              return result;
            }
          }
        }
      }
      
      console.log(`❌ Strategy ${index + 1} failed: No usable content found`);
      
    } catch (error) {
      console.log(`❌ Strategy ${index + 1} error: ${error.message}`);
      continue;
    }
    
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  throw new Error(`No captions accessible for video ${videoId}. This may be due to regional restrictions or the video lacking proper captions.`);
}
