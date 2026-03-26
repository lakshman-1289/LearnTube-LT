import { google } from 'googleapis';
import open from 'open';
import readline from 'readline/promises';
import fs from 'fs';

async function generateRefreshToken() {
  try {
    console.log('🔐 YouTube API OAuth 2.0 Token Generator');
    console.log('=' .repeat(50));
    
    // Check if client_secret.json exists
    const credentialsPath = './client_secret.json';
    if (!fs.existsSync(credentialsPath)) {
      console.error('❌ Error: client_secret.json file not found!');
      console.log('📥 Please download your OAuth client credentials from:');
      console.log('   Google Cloud Console → APIs & Services → Credentials');
      console.log('   And save it as "client_secret.json" in your project root');
      return;
    }

    // Load OAuth credentials
    const credentials = JSON.parse(fs.readFileSync(credentialsPath, 'utf8'));
    
    // Use 'installed' for desktop app or 'web' for web app
    const clientInfo = credentials.installed || credentials.web;
    
    if (!clientInfo) {
      console.error('❌ Error: Invalid client_secret.json format');
      return;
    }

    const oauth2Client = new google.auth.OAuth2(
      clientInfo.client_id,
      clientInfo.client_secret,
      'urn:ietf:wg:oauth:2.0:oob' // Out-of-band for CLI
    );

    // Define required scopes
    const scopes = [
      'https://www.googleapis.com/auth/youtube.readonly',
      'https://www.googleapis.com/auth/youtube.force-ssl'
    ];

    // Generate authorization URL
    const authUrl = oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: scopes,
      prompt: 'consent' // Force consent to get refresh token
    });

    console.log('🌐 Opening Google OAuth authorization...');
    console.log('📋 If browser doesn\'t open automatically, visit this URL:');
    console.log('\n' + authUrl + '\n');
    
    // Open browser automatically
    try {
      await open(authUrl);
      console.log('✅ Browser opened successfully');
    } catch (error) {
      console.log('⚠️  Could not open browser automatically');
    }

    // Get authorization code from user
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    console.log('📝 Steps to complete authorization:');
    console.log('   1. Sign in to your Google account');
    console.log('   2. Grant permissions to your application');
    console.log('   3. Copy the authorization code from the browser');
    console.log('   4. Paste it below\n');

    const code = await rl.question('🔑 Enter the authorization code: ');
    rl.close();

    if (!code || code.trim().length === 0) {
      console.error('❌ Error: No authorization code provided');
      return;
    }

    console.log('\n🔄 Exchanging authorization code for tokens...');

    // Exchange code for tokens
    const { tokens } = await oauth2Client.getToken(code.trim());

    if (!tokens.refresh_token) {
      console.error('❌ Error: No refresh token received');
      console.log('💡 Try running the script again and ensure you grant permissions');
      return;
    }

    console.log('\n🎉 SUCCESS! OAuth tokens generated successfully!');
    console.log('=' .repeat(50));
    console.log('📋 Add these environment variables to your .env.local file:');
    console.log('');
    console.log(`GOOGLE_CLIENT_ID=${clientInfo.client_id}`);
    console.log(`GOOGLE_CLIENT_SECRET=${clientInfo.client_secret}`);
    console.log(`GOOGLE_REFRESH_TOKEN=${tokens.refresh_token}`);
    console.log('');
    console.log('=' .repeat(50));

    // Test the tokens
    console.log('🧪 Testing token validity...');
    oauth2Client.setCredentials(tokens);
    const youtube = google.youtube({ version: 'v3', auth: oauth2Client });
    
    try {
      const testResponse = await youtube.videos.list({
        part: 'snippet',
        id: 'dQw4w9WgXcQ', // Rick Roll video for testing
        maxResults: 1
      });

      if (testResponse.data.items && testResponse.data.items.length > 0) {
        console.log('✅ Token test successful!');
        console.log(`📺 Test video found: ${testResponse.data.items[0].snippet.title}`);
      } else {
        console.log('⚠️  Token works but test video not found');
      }
    } catch (testError) {
      console.error('⚠️  Token generated but test failed:', testError.message);
      console.log('💡 This might be due to API quota or permissions');
    }

    console.log('\n✨ Setup complete! Your YouTube Learning Platform is ready.');
    console.log('🚀 You can now test your /api/generate-content endpoint');

  } catch (error) {
    console.error('❌ Error generating tokens:', error.message);
    
    if (error.message.includes('redirect_uri_mismatch')) {
      console.log('💡 Fix: Ensure your redirect URI matches Google Cloud Console settings');
    } else if (error.message.includes('invalid_client')) {
      console.log('💡 Fix: Check your client_secret.json file path and contents');
    } else if (error.message.includes('invalid_grant')) {
      console.log('💡 Fix: The authorization code may have expired. Try again.');
    } else {
      console.log('💡 Check your internet connection and try again');
    }
  }
}

// Run the token generation
generateRefreshToken();
