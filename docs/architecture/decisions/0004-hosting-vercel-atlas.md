# 0004. Hosting: Vercel (frontend + backend) and MongoDB Atlas

- **Status:** Accepted
- **Date:** 2026-11-19

## Context
The app ran only on my Mac: Next.js dev server, FastAPI under uvicorn, MongoDB in Docker. I want to use it
from my phone anywhere, deployed to Vercel from the GitHub repo `oksigma/life-tracker`.
Vercel runs Next.js natively and Python (FastAPI) as serverless functions, but has no database.

## Decision
- **Two Vercel projects from the same repo:**
  - `life-tracker` — Root Directory `life-tracker-app/frontend` (Next.js).
  - `life-tracker-api` — Root Directory `life-tracker-app/backend` (FastAPI as a Python function; entrypoint `index.py`).
- **The frontend proxies `/api/*` to the backend** with a Next.js rewrite (`BACKEND_URL`). The browser only ever
  talks to the frontend's domain, so the login cookie is first-party and no CORS is needed in production.
- **Database: MongoDB Atlas**, free M0 cluster. Same driver and code; only `MONGODB_URL` changes. Photos stay in GridFS.
- **Locally nothing changes:** uvicorn + Docker MongoDB. The frontend uses the same `/api` rewrite, pointing at
  `http://localhost:8000` by default.
- **A single-user app password** is required before the app goes on a public URL (spec 0006).

## Consequences
- Easier: one `git push` deploys both; free tiers cover a single user.
- **Upload limit:** Vercel functions accept request bodies up to 4.5 MB, so the browser shrinks larger photos
  (to ≤ 2000 px JPEG) before uploading. HEIC photos over 4 MB can't be shrunk in browsers that can't decode HEIC.
- **Storage limit:** Atlas M0 has 512 MB, roughly 1,000 photos. Upgrade or move photos to object storage later.
- Cold starts: the first request after idle takes a second or two (connect to Atlas, ensure indexes).
- Atlas must allow connections from anywhere (`0.0.0.0/0`), since Vercel has no fixed IPs; the database user's
  password protects it. Put Vercel's function region and the Atlas cluster in the same region.
- The in-memory Open Food Facts rate limiter and login-attempt limiter are per function instance (good enough for one user).
