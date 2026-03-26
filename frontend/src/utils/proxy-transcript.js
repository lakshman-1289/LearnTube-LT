import axios from 'axios';
import { HttpsProxyAgent } from 'https-proxy-agent';

export class ProxyTranscriptFetcher {
  constructor() {
    // List of free proxy services (rotate these)
    this.proxyList = [
      'https://cors-anywhere.herokuapp.com/',
      'https://api.allorigins.win/raw?url=',
      'https://corsproxy.io/?'
    ];
  }

  async fetchWithProxy(videoId, lang = 'en') {
    const originalUrl = `https://www.youtube.com/api/timedtext?v=${videoId}&lang=${lang}&fmt=json3`;
    
    for (const proxy of this.proxyList) {
      try {
        console.log(`🌐 Trying proxy: ${proxy}`);
        
        const proxyUrl = proxy + encodeURIComponent(originalUrl);
        const response = await axios.get(proxyUrl, {
          timeout: 15000,
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'X-Requested-With': 'XMLHttpRequest'
          }
        });

        if (response.data && response.data.events) {
          console.log(`✅ Proxy success with: ${proxy}`);
          return this.parseJson3(response.data);
        }
        
      } catch (error) {
        console.log(`❌ Proxy ${proxy} failed: ${error.message}`);
        continue;
      }
    }
    
    throw new Error('All proxy attempts failed');
  }

  parseJson3(json) {
    const chunks = json.events
      .filter(e => e.segs)
      .flatMap(e =>
        e.segs.map(s => ({
          start: +(e.tStartMs / 1000).toFixed(3),
          dur: +(e.dDurationMs / 1000).toFixed(3),
          text: s.utf8.trim()
        }))
      );

    return {
      cleanText: chunks.map(c => c.text).join(' ').replace(/\s+/g, ' ').trim(),
      chunks
    };
  }
}
