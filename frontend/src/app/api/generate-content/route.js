import dbConnect from '../../../lib/mongodb.js';
import AdminData from '../../../models/AdminData.js';
import { validateGenerateBody, methodOnly } from '../../../utils/validation.js';
import { normaliseYouTubeUrl } from '../../../utils/youtube.js';

export async function POST(req) {
  let videoId, url, language;
  try {
    methodOnly('POST');
    const body = await req.json();
    ({ url, videoId, language } = validateGenerateBody(body));

    console.log(`🎯 Processing transcript request for: ${videoId}`);

    await dbConnect();
    const cached = await AdminData.findOne({ videoId, language });
    if (cached) {
      console.log(`✅ Cache hit for: ${videoId}`);
      return Response.json({ success: true, cached: true, data: cached });
    }

    console.log(`🔄 Cache miss, fetching transcript for: ${videoId}`);

    // --- PYTHON WHISPER EXTRACTION (now main method) ---
    try {
      console.log(`🐍 Using Python Whisper script for: ${videoId}`);
      const { spawn } = await import('child_process');
      // Use USERPROFILE for portability
      const pythonPath = `${process.env.USERPROFILE}\\AppData\\Local\\Programs\\Python\\Python311\\python.exe`;
      const py = spawn(pythonPath, ['scripts/get_youtube_transcript.py', url]);
      let output = '';
      let error = '';
      for await (const data of py.stdout) {
        output += data.toString();
      }
      for await (const data of py.stderr) {
        error += data.toString();
      }
      const code = await new Promise((resolve) => py.on('close', resolve));
      if (code === 0 && output.trim().length > 0) {
        console.log(`🐍 Python output length: ${output.length} characters`);
        console.log(`🐍 Python output preview: ${output.substring(0, 200)}...`);
        
        // First, try to parse the entire output as JSON (in case it's pretty-printed)
        let parsed = null;
        try {
          parsed = JSON.parse(output.trim());
          console.log(`✅ Successfully parsed entire output as JSON`);
        } catch (e) {
          console.log(`⚠️ Failed to parse entire output, trying line-by-line...`);
          // If that fails, try line-by-line parsing
          const lines = output.split('\n');
          for (const line of lines) {
            try {
              parsed = JSON.parse(line);
              console.log(`✅ Successfully parsed line as JSON`);
              break; // Found valid JSON, stop searching
            } catch (e) {
              // Not JSON, continue to next line
            }
          }
        }
        
        if (parsed) {
          console.log(`✅ Python script returned data:`, { 
            hasError: !!parsed.error, 
            hasText: !!parsed.text, 
            source: parsed.source,
            textLength: parsed.text?.length || 0,
            dataSize: JSON.stringify(parsed).length + ' bytes'
          });
          
          // Check if it's an error response from Python
          if (parsed.error) {
            return Response.json({
              success: false,
              error: parsed.error,
              videoId,
              language,
              url
            }, { status: 500 });
          }
          
          // Convert Python output format to match expected Node.js format
          // Only store clean text and essential metadata, not raw timing data
          const transcriptData = {
            cleanText: parsed.text || '',
            source: parsed.source || 'python-fallback',
            language: parsed.language || language,
            isGenerated: parsed.is_generated || false
            // Removed rawData to reduce file size - only keeping clean text
          };
          
          // Create a record similar to the successful case
          const record = await AdminData.create({
            videoId,
            language,
            url: normaliseYouTubeUrl(url),
            transcript: transcriptData,
            extractionMethod: 'python-whisper',
            fetchedAt: new Date()
          });
          
          return Response.json({
            success: true,
            cached: false,
            data: record,
            meta: {
              extractionMethod: 'python-whisper',
              transcriptLength: transcriptData.cleanText.length,
              source: parsed.source
            }
          });
        } else {
          return Response.json({
            success: false,
            error: 'Failed to parse Python output as JSON',
            raw: output.substring(0, 500) + '...', // Truncate for readability
            videoId,
            language,
            url
          }, { status: 500 });
        }
      } else {
        throw new Error(error || 'Python transcript extraction failed');
      }
    } catch (pythonError) {
      // Final error response
      return Response.json({
        success: false,
        error: pythonError.message,
        videoId,
        suggestion: 'Transcript extraction failed. Try a different video.'
      }, { status: 500 });
    }
    // --- END PYTHON WHISPER EXTRACTION ---
  } catch (err) {
    console.error(`❌ Error processing ${videoId}:`, err.message);
    return Response.json({
      success: false,
      error: err.message,
      videoId,
      suggestion: 'Transcript extraction failed. Try a different video.'
    }, { status: 500 });
  }
}

export async function GET() {
  return Response.json({ 
    error: 'Method not allowed. Use POST instead.',
    usage: {
      method: 'POST',
      body: { url: 'https://youtube.com/watch?v=VIDEO_ID', language: 'en' }
    }
  }, { status: 405 });
}
