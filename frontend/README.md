# Frontend - TikTok Video Ad Automation

Next.js web interface for the TikTok video ad automation tool.

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library
- **React Hook Form** - Form handling

## Setup

1. **Install Dependencies**

```bash
npm install
```

2. **Run Development Server**

```bash
npm run dev
```

3. **Build for Production**

```bash
npm run build
npm run start
```

## Features

- **Script Input**: Text area for TikTok ad scripts
- **Video Upload**: Multi-file video upload with validation
- **Voiceover Upload**: Optional ElevenLabs voiceover support
- **Real-time Progress**: Live processing status updates
- **Results Display**: Download generated videos and timestamps

## Components

### Main Components

- `script-input-section.tsx` - Script input and validation
- `video-upload-section.tsx` - Video file management
- `voiceover-upload-section.tsx` - Optional voiceover upload
- `processing-status.tsx` - Real-time progress tracking
- `results-display.tsx` - Output display and downloads

### UI Components (shadcn)

- Button, Card, Form, Input, Progress, Toast, etc.

## API Integration

Connects to backend API using environment variable `NEXT_PUBLIC_API_URL`:

- Upload videos and script
- Monitor processing status
- Download results

## Environment Variables

Create `.env.local`:

```env
# For development: http://localhost:5001
# For production: https://api.dabu.ai (or your production URL)
NEXT_PUBLIC_API_URL=http://localhost:5001
```

## Development

```bash
# Development with hot reload
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint

# Format code
npm run format
```
