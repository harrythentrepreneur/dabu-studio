<div align="center">

# Dabu

### Script + raw footage in. A cut TikTok ad out.

Give Dabu your ad script and a pile of clips. Gemini watches every clip, picks the best moment for each line, and a GPU worker cuts it into a vertical ad timed to your voiceover.

![Next.js](https://img.shields.io/badge/frontend-Next.js-black) ![Python](https://img.shields.io/badge/backend-Python-3776ab) ![Gemini](https://img.shields.io/badge/AI-Gemini%20vision-4285f4) ![RunPod](https://img.shields.io/badge/GPU-RunPod%20serverless-673ab7) ![License AGPL-3.0](https://img.shields.io/badge/license-AGPL--3.0-black)

</div>

---

## Why

Editing a short-form ad is mostly searching. You scrub through twenty minutes of footage to find the two seconds that match "and it actually works." Dabu hands that search to a vision model and keeps the creative call with you.

## The toolkit

| Studio | What it does |
| --- | --- |
| **Express Builder** | Script + videos → a finished ad with hard cuts, matched line by line |
| **Quick Create** | Express Builder plus automatic captions |
| **Clip Studio** | Search stock moments and reaction clips to drop into your edit |
| **GIF Studio** | Find and place GIF overlays by mood |
| **Trending Audio** | Browse music previews to pick a track |
| **Voiceover mode** | Upload a recorded VO; Whisper times every cut to your words |

## How it works

```
Next.js app ──upload──▶ S3-compatible storage (DigitalOcean Spaces)
     │
     └──job──▶ RunPod serverless worker (backend/)
                  1. compress clips for analysis
                  2. Gemini vision: score each moment against each script line
                  3. Whisper (optional): align cuts to the voiceover
                  4. FFmpeg: extract, merge, export 9:16
                  └──▶ finished video back to storage ──▶ results page
```

Workers scale to zero, so you only pay for the GPU seconds a job uses.

## Quick start

```bash
git clone https://github.com/harrythentrepreneur/dabu-studio.git
cd dabu-studio

# frontend
cd frontend
cp .env.example .env.local      # Clerk, Spaces, RunPod, Gemini keys
npm install --legacy-peer-deps
npm run dev                     # http://localhost:3000

# backend worker (local test server)
cd ../backend
cp .env.example .env
pip install -r requirements.txt
python test_server.py
```

To deploy the worker, see [`docs/deployment/RUNPOD_DEPLOYMENT.md`](docs/deployment/RUNPOD_DEPLOYMENT.md). The frontend runs anywhere Next.js runs.

## Configuration

| Variable | Used for |
| --- | --- |
| `GEMINI_API_KEY` | Clip analysis and script matching |
| `OPENAI_API_KEY` | Whisper voiceover alignment (optional) |
| `DO_SPACES_KEY`, `DO_SPACES_SECRET`, `DO_SPACES_BUCKET`, `DO_SPACES_REGION` | Video storage (any S3-compatible bucket) |
| `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT_ID` | Serverless GPU worker |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY` | Sign-in (required to build the frontend) |
| `NEXT_PUBLIC_KLIPY_API_KEY` | Clip and GIF search |
| `STRIPE_*`, `RESEND_*` | Optional billing and magic-link email |

## Repository

```
frontend/      Next.js app (studios, upload, results, auth, billing)
backend/       Python worker: Gemini analysis, Whisper, FFmpeg pipeline, RunPod handlers
docs/          overview, architecture, API, quick start, deployment guides
scripts/       deploy and validation helpers
```

## Status

Dabu was built as a product and is now shared as-is. The pipeline works end to end, but expect rough edges and docs written along the way.

## Credits

Built by [Harry Edwards](https://github.com/harrythentrepreneur) and [Kaviru Hapuarachchi](https://github.com/Kavirubc). Parts of the frontend shell are adapted from [Rybbit](https://github.com/rybbit-io/rybbit) (AGPL-3.0); see [NOTICE](NOTICE).

## License

[AGPL-3.0](LICENSE). Dabu includes AGPL-licensed code, so the whole project is AGPL.
