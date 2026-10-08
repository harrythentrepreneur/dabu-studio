# Deployment Guide

## Overview

Dabu is now split into two repositories:
- **Frontend**: This repository (Next.js application)
- **Backend**: ./backend (RunPod serverless)

## Frontend Deployment

### Prerequisites
- Node.js 18+ and pnpm
- Vercel, Netlify, or any Next.js hosting platform
- Environment variables configured

### Environment Setup

1. Copy `.env.example` to `.env`:
```bash
cp frontend/.env.example frontend/.env
```

2. Configure all required variables:
- Digital Ocean Spaces credentials
- RunPod API key and endpoint ID
- Gemini API key
- Clerk authentication keys
- Stripe payment keys

### Deployment Steps

#### Option 1: Vercel (Recommended)

1. Connect GitHub repository to Vercel
2. Set root directory to `frontend`
3. Configure environment variables in Vercel dashboard
4. Deploy

#### Option 2: Manual Deployment

```bash
cd frontend
pnpm install
pnpm build
pnpm start
```

### Important URLs
- Production: Configure in `NEXT_PUBLIC_APP_URL`
- API endpoints will use RunPod serverless

## Backend Deployment

### Prerequisites
- RunPod account with credits
- Docker installed locally (for building)
- Backend repository cloned

### RunPod Setup

1. Create a new serverless endpoint in RunPod
2. Note the endpoint ID
3. Configure environment variables in RunPod dashboard

### Deployment Steps

1. Clone backend repository:
```bash
git clone https://github.com/harrythentrepreneur/dabu-studio.git && cd dabu-studio/backend
```

2. Build and push Docker image:
```bash
docker build -t your-registry/dabu-backend .
docker push your-registry/dabu-backend
```

3. Deploy to RunPod:
- Use the Docker image URL in RunPod
- Configure environment variables
- Set appropriate GPU/CPU resources

### Environment Variables

Copy `.env.example` to `.env` and configure:
- Gemini API key
- OpenAI API key (for Whisper)
- Digital Ocean Spaces credentials
- CapCut credentials (for Quick Create)

## Testing

### Frontend Testing
```bash
cd frontend
pnpm test
pnpm lint
pnpm typecheck
```

### End-to-End Testing
1. Ensure backend is deployed and running
2. Update frontend with RunPod endpoint
3. Test video processing flow

## Monitoring

- Frontend: Use Vercel Analytics or your platform's monitoring
- Backend: Monitor through RunPod dashboard
- Logs: Check RunPod logs for processing issues

## Troubleshooting

### Common Issues

1. **TypeScript errors**: Run `pnpm typecheck` to verify
2. **API connection issues**: Check RunPod endpoint configuration
3. **Storage issues**: Verify Digital Ocean Spaces credentials
4. **Processing failures**: Check RunPod logs and Gemini API limits

### Support

For issues, create a GitHub issue in the appropriate repository:
- Frontend issues: This repository
- Backend/processing issues: ./backend
