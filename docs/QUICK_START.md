# Quick Start Guide

Get up and running with TikTok Video Ad Automation in 5 minutes!

## 🎯 What You'll Need

- **Google Gemini API Key** (Required) - [Get it here](https://makersuite.google.com/app/apikey)
- **RunPod Account** (For production) - [Sign up](https://www.runpod.io)
- **Docker** (Recommended) - [Install Docker](https://docs.docker.com/get-docker/)

## 🚀 Fastest Setup (Docker)

### 1. Clone and Configure (1 minute)

```bash
# Clone the repo
git clone https://github.com/harrythentrepreneur/dabu-studio.git
cd tiktok-video-ad-automation

# Set up your API keys
cd backend
cp .env.example .env
nano .env  # Add your GEMINI_API_KEY
```

### 2. Start Everything (2 minutes)

```bash
# Go back to root directory
cd ..

# Start all services with Docker Compose
docker-compose up
```

### 3. Test It! (2 minutes)

1. Open http://localhost:3000
2. Paste this sample script:
   ```
   Welcome to our amazing product!
   It will change your life.
   Here's how it works.
   Join thousands of happy customers.
   Get yours today!
   ```
3. Upload 2-3 video files (or use samples from `input_videos/`)
4. Set duration to 30 seconds
5. Click "Process Video"

## 💡 First Video Tutorial

### Step 1: Prepare Your Content

**Script Requirements:**
- 15-45 seconds of content
- 5-10 short lines work best
- Each line = one scene (3-8 seconds)

**Example Script:**
```
🔥 This gadget is revolutionary!
Watch how easy it is to use.
It saves you hours every day.
Perfect for busy professionals.
Order now with 50% off!
```

**Video Requirements:**
- MP4 format preferred
- Any resolution (will be optimized)
- 2-5 minutes total footage recommended
- Mix different scenes for variety

### Step 2: Process Your Video

1. **Open the App**: http://localhost:3000

2. **Enter Your Script**:
   - Paste or type your script
   - Character counter shows length
   - Aim for 150-300 characters

3. **Upload Videos**:
   - Drag & drop or click to browse
   - Upload 2-5 video files
   - Order doesn't matter (AI will arrange)

4. **Set Duration**:
   - Default: 30 seconds
   - Range: 15-45 seconds
   - AI will match to ±3 seconds

5. **Click Process**:
   - Watch real-time progress
   - Takes 2-5 minutes typically
   - Download when complete!

### Step 3: Using Voiceover (Optional)

Have a voiceover? Perfect sync is automatic:

1. Record your voiceover (MP3/WAV)
2. Upload it with your videos
3. Enable "Voiceover Mode"
4. AI matches visuals to audio timing

## 🎨 Try the Extended Toolkit

Access advanced features at http://localhost:3002:

### Express Builder
Quick video from templates:
1. Choose a template
2. Customize text/colors
3. Export in seconds

### Clip Studio
Extract perfect moments:
1. Upload long video
2. AI finds best clips
3. Download individually

### GIF Studio
Create viral GIFs:
1. Paste your script
2. AI identifies GIF moments
3. Export as GIF/MP4

## 🔧 Configuration Tips

### For Best Results

**Optimal Settings** (`backend/.env`):
```env
# Faster processing (lower quality)
COMPRESSION_TARGET_MB=50
DEFAULT_TARGET_DURATION=30

# Better quality (slower)
COMPRESSION_TARGET_MB=150
DEFAULT_TARGET_DURATION=35
```

### Debug Mode

Having issues? Enable debug mode:

```env
DEBUG_MODE=true
```

This creates detailed logs in `output/debug_*.json`

## 🚢 Deploy to Production

### Quick Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy Flask backend
cd backend
railway login
railway init
railway up

# Note the URL, update frontend .env
```

### Setup RunPod (5 minutes)

1. **Create RunPod Account**: [runpod.io](https://runpod.io)

2. **Deploy Worker**:
   ```bash
   cd backend
   ./deploy-runpod.sh
   ```

3. **Create Endpoint**:
   - Go to RunPod dashboard
   - New serverless endpoint
   - Use your Docker image
   - Copy endpoint ID

4. **Update Config**:
   ```env
   RUNPOD_API_KEY=your-key
   RUNPOD_ENDPOINT_ID=your-endpoint
   ```

## 📝 Sample Projects

### TikTok Product Ad (30s)

**Script:**
```
🎯 Problem: Messy cables everywhere?
✨ Solution: CableWizard organizer!
🎬 Watch: Installation in 30 seconds
💪 Result: Clean, organized workspace
🛒 Action: Get 40% off today only!
```

**Videos Needed:**
- Messy desk footage (before)
- Product close-ups
- Installation process
- Clean desk (after)
- Call-to-action graphics

### Instagram Reel (15s)

**Script:**
```
POV: You discovered this app
It does your homework
Your grades improve
Mom is impressed
Download now!
```

**Videos Needed:**
- Phone screen recording
- Student studying
- Grade report
- Parent reaction
- App store screen

## 🆘 Quick Troubleshooting

### "Gemini API Error"
```bash
# Check your API key
echo $GEMINI_API_KEY

# Test Gemini connection
curl -H "x-goog-api-key: YOUR_KEY" \
  "https://generativelanguage.googleapis.com/v1/models"
```

### "Video Processing Failed"
```bash
# Check FFmpeg
ffmpeg -version

# Check logs
tail -f backend/logs/main.log
```

### "RunPod Not Responding"
```bash
# Check RunPod health
curl http://localhost:5000/api/runpod/health

# Verify credentials
grep RUNPOD backend/.env
```

## 📚 Next Steps

### Learn More
- [Full Documentation](../README.md)
- [API Reference](API_DOCUMENTATION.md)
- [Architecture Guide](ARCHITECTURE.md)

### Advanced Features
- Batch processing multiple ads
- Custom style templates
- Webhook integrations
- CI/CD pipelines

### Get Help
- GitHub Issues: Report bugs
- Discord: Join community
- Email: support@example.com

## 🎉 You're Ready!

You now have everything needed to create professional TikTok videos with AI. Start with simple projects and explore advanced features as you grow comfortable.

**Pro Tips:**
- Keep scripts concise and punchy
- Use diverse video footage
- Test different durations
- Enable debug mode when learning
- Join our Discord for tips!

---

Happy creating! 🚀