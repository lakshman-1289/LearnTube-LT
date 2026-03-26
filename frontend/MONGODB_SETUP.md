# MongoDB Setup Guide for LearnTube

## 🎯 **MongoDB is MANDATORY for Course Storage**

The course generation system requires MongoDB to store generated courses. Follow this guide to set up MongoDB.

## 📋 **Option 1: Local MongoDB Installation**

### **Step 1: Install MongoDB Community Edition**

#### **Windows:**
1. Download MongoDB Community Server from: https://www.mongodb.com/try/download/community
2. Run the installer and follow the setup wizard
3. Install MongoDB Compass (GUI tool) when prompted

#### **macOS:**
```bash
brew tap mongodb/brew
brew install mongodb-community
```

#### **Linux (Ubuntu):**
```bash
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
```

### **Step 2: Start MongoDB Service**

#### **Windows:**
```powershell
# Start MongoDB service
net start MongoDB

# Or start manually
"C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" --dbpath="C:\data\db"
```

#### **macOS/Linux:**
```bash
# Start MongoDB service
sudo systemctl start mongod

# Enable MongoDB to start on boot
sudo systemctl enable mongod

# Check status
sudo systemctl status mongod
```

### **Step 3: Verify MongoDB is Running**

```bash
# Connect to MongoDB
mongosh

# Or check if port 27017 is listening
netstat -an | grep 27017
```

## 📋 **Option 2: MongoDB Atlas (Cloud)**

### **Step 1: Create MongoDB Atlas Account**
1. Go to https://www.mongodb.com/atlas
2. Sign up for a free account
3. Create a new cluster (free tier available)

### **Step 2: Get Connection String**
1. Click "Connect" on your cluster
2. Choose "Connect your application"
3. Copy the connection string
4. Replace `<password>` with your database password

## 🔧 **Step 3: Configure Environment Variables**

### **Create .env.local file in your project root:**

```bash
# For Local MongoDB
MONGODB_URI=mongodb://localhost:27017/learntube

# For MongoDB Atlas (replace with your connection string)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/learntube?retryWrites=true&w=majority

# Other required variables
NEXTAUTH_SECRET=your-secret-key-here
OPENROUTER_API_KEY=your-openrouter-key-here
```

## 🧪 **Step 4: Test MongoDB Connection**

### **Run the test script:**
```bash
node test-mongodb-connection.js
```

### **Expected Output:**
```
🔍 Testing MongoDB Connection...

1️⃣ Checking environment variables:
MONGODB_URI: ✅ Set
NEXTAUTH_SECRET: ✅ Set

2️⃣ Attempting to connect to MongoDB...
✅ MongoDB connection successful!

3️⃣ Testing database operations...
✅ Document creation successful!
✅ Document reading successful!
✅ Document deletion successful!

🎉 All MongoDB operations working correctly!
```

## 🚀 **Step 5: Test Course Generation**

### **Start the servers:**
```bash
# Terminal 1: Start FastAPI server
cd your-project-root/src
python test_api_mock.py

# Terminal 2: Start Next.js server
npm run dev
```

### **Test course generation:**
```bash
# Test the API
curl -X POST http://localhost:3000/api/generate-learning-content \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

## 🔍 **Troubleshooting**

### **Common Issues:**

1. **"MONGODB_URI not set"**
   - Create `.env.local` file with MongoDB URI
   - Restart your Next.js server

2. **"Connection refused"**
   - Make sure MongoDB service is running
   - Check if port 27017 is available

3. **"Authentication failed"**
   - Check your MongoDB Atlas credentials
   - Ensure your IP is whitelisted (for Atlas)

4. **"Database not found"**
   - MongoDB will create the database automatically
   - No manual database creation needed

### **Verify MongoDB is Running:**

#### **Windows:**
```powershell
# Check if MongoDB service is running
Get-Service MongoDB

# Check if port 27017 is listening
netstat -an | findstr 27017
```

#### **macOS/Linux:**
```bash
# Check MongoDB service status
sudo systemctl status mongod

# Check if port 27017 is listening
lsof -i :27017
```

## ✅ **Success Indicators**

When everything is working correctly, you should see:

1. ✅ MongoDB connection successful
2. ✅ Course generation working
3. ✅ Course data saved to database
4. ✅ No "Failed to save course data to database" errors

## 📊 **Database Structure**

The system will create these collections:
- `admindatas` - Stores course data and transcripts
- `users` - User authentication data
- `videocontents` - Video metadata

## 🎯 **Next Steps**

Once MongoDB is set up:
1. Test course generation with a YouTube URL
2. Check that courses are saved in MongoDB
3. Use the `/api/get-stored-courses` endpoint to retrieve saved courses 